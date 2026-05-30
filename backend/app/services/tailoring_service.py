import json
import re
import uuid
from typing import Any

from fastapi import status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.query import TailoringQuery
from app.models.retrieval_result import RetrievalResult
from app.schemas.search import SearchFilters, SearchResult
from app.schemas.tailor import TailorBulletsRequest, TailorBulletsResponse, TailoredBullet
from app.services.ollama_service import OllamaError, OllamaService
from app.services.prompt_service import PromptService
from app.services.retrieval_service import RetrievalError, RetrievalService


class TailoringError(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class TailoringService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.retrieval_service = RetrievalService(db)
        self.ollama_service = OllamaService()
        self.prompt_service = PromptService()

    def generate_bullets(self, request: TailorBulletsRequest) -> TailorBulletsResponse:
        if not request.job_description.strip():
            raise TailoringError("Job description cannot be empty.")

        try:
            retrieved_context = self.retrieval_service.search(
                query=request.job_description,
                top_k=request.top_k,
                filters=SearchFilters(),
            )
        except RetrievalError as exc:
            raise TailoringError(exc.message, exc.status_code) from exc

        messages = self.prompt_service.build_messages(request, retrieved_context)

        try:
            raw_response = self.ollama_service.chat(messages)
        except OllamaError as exc:
            raise TailoringError(str(exc), status.HTTP_503_SERVICE_UNAVAILABLE) from exc

        parsed = self._parse_llm_json(raw_response)
        bullets = self._map_bullets(parsed.get("bullets", []), retrieved_context)
        warnings = self._normalize_warnings(parsed.get("warnings", []))

        if not bullets and not warnings:
            warnings = ["Not enough evidence."]

        query_row = TailoringQuery(
            job_description=request.job_description,
            target_role=self._clean_optional(request.target_role),
            company_name=self._clean_optional(request.company_name),
            generated_answer=raw_response,
            model_name=self.settings.ollama_model,
        )

        try:
            self.db.add(query_row)
            self.db.flush()
            for result in retrieved_context:
                self.db.add(
                    RetrievalResult(
                        query_id=query_row.id,
                        chunk_id=result.chunk_id,
                        rank=result.rank,
                        similarity_score=result.similarity_score,
                    )
                )
            self.db.commit()
            self.db.refresh(query_row)
        except Exception as exc:
            self.db.rollback()
            raise TailoringError("Could not save tailoring query.", status.HTTP_500_INTERNAL_SERVER_ERROR) from exc

        return TailorBulletsResponse(
            query_id=query_row.id,
            target_role=query_row.target_role,
            company_name=query_row.company_name,
            bullets=bullets,
            retrieved_context=retrieved_context,
            warnings=warnings,
        )

    def _parse_llm_json(self, raw_response: str) -> dict[str, Any]:
        text = raw_response.strip()
        candidates = [text]

        fenced_match = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
        if fenced_match:
            candidates.append(fenced_match.group(1).strip())

        object_match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if object_match:
            candidates.append(object_match.group(0))

        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed

        raise TailoringError("Ollama returned JSON that could not be parsed.", status.HTTP_502_BAD_GATEWAY)

    def _map_bullets(self, raw_bullets: Any, retrieved_context: list[SearchResult]) -> list[TailoredBullet]:
        if not isinstance(raw_bullets, list):
            raise TailoringError("Ollama response was missing a valid bullets list.", status.HTTP_502_BAD_GATEWAY)

        mapped: list[TailoredBullet] = []
        for raw_bullet in raw_bullets:
            if not isinstance(raw_bullet, dict):
                continue

            bullet_text = self._string_value(raw_bullet.get("bullet"))
            if not bullet_text or bullet_text.lower() == "not enough evidence":
                continue

            source_chunk_ids = self._source_numbers_to_chunk_ids(raw_bullet.get("source_numbers"), retrieved_context)
            mapped.append(
                TailoredBullet(
                    bullet=bullet_text,
                    matched_requirement=self._string_value(raw_bullet.get("matched_requirement")) or "Not specified",
                    evidence_strength=self._normalize_evidence_strength(raw_bullet.get("evidence_strength")),
                    source_chunk_ids=source_chunk_ids,
                    notes=self._string_value(raw_bullet.get("notes")),
                )
            )

        return mapped

    def _source_numbers_to_chunk_ids(self, source_numbers: Any, retrieved_context: list[SearchResult]) -> list[uuid.UUID]:
        if not isinstance(source_numbers, list):
            return []

        chunk_ids: list[uuid.UUID] = []
        for source_number in source_numbers:
            try:
                index = int(source_number) - 1
            except (TypeError, ValueError):
                continue
            if 0 <= index < len(retrieved_context):
                chunk_ids.append(retrieved_context[index].chunk_id)

        return chunk_ids

    def _normalize_warnings(self, warnings: Any) -> list[str]:
        if not isinstance(warnings, list):
            return []
        return [warning.strip() for warning in warnings if isinstance(warning, str) and warning.strip()]

    def _normalize_evidence_strength(self, value: Any) -> str:
        normalized = self._string_value(value).lower()
        if normalized in {"high", "medium", "low"}:
            return normalized
        return "low"

    def _string_value(self, value: Any) -> str:
        return value.strip() if isinstance(value, str) else ""

    def _clean_optional(self, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None
