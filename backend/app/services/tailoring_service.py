import json
import re
from typing import Any

from fastapi import status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.query import TailoringQuery
from app.models.retrieval_result import RetrievalResult
from app.schemas.search import SearchFilters, SearchResult
from app.schemas.tailor import RejectedBullet, TailorBulletsRequest, TailorBulletsResponse, TailoredBullet, TailoredSkill
from app.services.bullet_validation_service import BulletValidationService, chunk_ids_from_source_numbers
from app.services.ollama_service import OllamaError, OllamaService
from app.services.placement_service import PlacementService
from app.services.prompt_service import PromptService
from app.services.retrieval_service import RetrievalError, RetrievalService


class TailoringError(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


SKILL_CATEGORIES = {
    "languages": "Languages",
    "frameworks libraries": "Frameworks & Libraries",
    "frameworks and libraries": "Frameworks & Libraries",
    "frameworks & libraries": "Frameworks & Libraries",
    "databases": "Databases",
    "ai ml": "AI/ML",
    "ai/ml": "AI/ML",
    "tools": "Tools",
}

JD_SKILL_CATALOG = (
    ("C++", "Languages", (r"(?i)(?<![a-z0-9])c\+\+(?![a-z0-9])",)),
    ("Java", "Languages", (r"(?i)(?<![a-z0-9])java(?![a-z0-9])",)),
    ("Python", "Languages", (r"(?i)(?<![a-z0-9])python(?![a-z0-9])",)),
    ("JavaScript", "Languages", (r"(?i)(?<![a-z0-9])javascript(?![a-z0-9])",)),
    ("TypeScript", "Languages", (r"(?i)(?<![a-z0-9])typescript(?![a-z0-9])",)),
    ("Go", "Languages", (r"(?<![A-Za-z0-9])Go(?![A-Za-z0-9])", r"(?i)(?<![a-z0-9])golang(?![a-z0-9])")),
    ("SQL", "Languages", (r"(?i)(?<![a-z0-9])sql(?![a-z0-9])",)),
    ("Bash", "Languages", (r"(?i)(?<![a-z0-9])bash(?![a-z0-9])",)),
    ("JSON", "Languages", (r"(?i)(?<![a-z0-9])json(?![a-z0-9])",)),
    ("XML", "Languages", (r"(?i)(?<![a-z0-9])xml(?![a-z0-9])",)),
    ("React", "Frameworks & Libraries", (r"(?i)(?<![a-z0-9])react(?:\.js|js)?(?![a-z0-9])",)),
    ("Next.js", "Frameworks & Libraries", (r"(?i)(?<![a-z0-9])next(?:\.js|js)?(?![a-z0-9])",)),
    ("Tailwind CSS", "Frameworks & Libraries", (r"(?i)(?<![a-z0-9])tailwind(?:\s+css)?(?![a-z0-9])",)),
    ("Node.js", "Frameworks & Libraries", (r"(?i)(?<![a-z0-9])node(?:\.js|js)?(?![a-z0-9])",)),
    ("FastAPI", "Frameworks & Libraries", (r"(?i)(?<![a-z0-9])fastapi(?![a-z0-9])",)),
    ("Spring Boot", "Frameworks & Libraries", (r"(?i)(?<![a-z0-9])spring\s+boot(?![a-z0-9])",)),
    ("Spring Framework", "Frameworks & Libraries", (r"(?i)(?<![a-z0-9])spring\s+framework(?![a-z0-9])",)),
    ("Hibernate/JPA", "Frameworks & Libraries", (r"(?i)(?<![a-z0-9])hibernate(?:/jpa)?(?![a-z0-9])", r"(?i)(?<![a-z0-9])jpa(?![a-z0-9])")),
    ("JUnit", "Frameworks & Libraries", (r"(?i)(?<![a-z0-9])junit(?![a-z0-9])",)),
    ("Mockito", "Frameworks & Libraries", (r"(?i)(?<![a-z0-9])mockito(?![a-z0-9])",)),
    ("pandas", "Frameworks & Libraries", (r"(?i)(?<![a-z0-9])pandas(?![a-z0-9])",)),
    ("NumPy", "Frameworks & Libraries", (r"(?i)(?<![a-z0-9])numpy(?![a-z0-9])",)),
    ("Ray", "Frameworks & Libraries", (r"(?i)(?<![a-z0-9])ray(?![a-z0-9])",)),
    ("PostgreSQL", "Databases", (r"(?i)(?<![a-z0-9])postgresql(?![a-z0-9])", r"(?i)(?<![a-z0-9])postgres(?![a-z0-9])")),
    ("MySQL", "Databases", (r"(?i)(?<![a-z0-9])mysql(?![a-z0-9])",)),
    ("MongoDB", "Databases", (r"(?i)(?<![a-z0-9])mongodb(?![a-z0-9])",)),
    ("Redis", "Databases", (r"(?i)(?<![a-z0-9])redis(?![a-z0-9])",)),
    ("Oracle", "Databases", (r"(?i)(?<![a-z0-9])oracle(?![a-z0-9])",)),
    ("Elasticsearch", "Databases", (r"(?i)(?<![a-z0-9])elasticsearch(?![a-z0-9])",)),
    ("OpenSearch", "Databases", (r"(?i)(?<![a-z0-9])opensearch(?![a-z0-9])",)),
    ("Vector DB", "Databases", (r"(?i)(?<![a-z0-9])vector\s+db(?![a-z0-9])", r"(?i)(?<![a-z0-9])vector\s+stores?(?![a-z0-9])")),
    ("NoSQL", "Databases", (r"(?i)(?<![a-z0-9])nosql(?![a-z0-9])", r"(?i)no\s*sql")),
    ("LangChain", "AI/ML", (r"(?i)(?<![a-z0-9])langchain(?![a-z0-9])",)),
    ("RAG", "AI/ML", (r"(?i)(?<![a-z0-9])rag(?![a-z0-9])",)),
    ("GenAI", "AI/ML", (r"(?i)(?<![a-z0-9])genai(?![a-z0-9])", r"(?i)generative\s+ai")),
    ("LLM", "AI/ML", (r"(?i)(?<![a-z0-9])llm(?:s)?(?![a-z0-9])",)),
    ("Embeddings", "AI/ML", (r"(?i)(?<![a-z0-9])embedding(?:s)?(?![a-z0-9])",)),
    ("Chunking", "AI/ML", (r"(?i)(?<![a-z0-9])chunking(?![a-z0-9])",)),
    ("Prompt Engineering", "AI/ML", (r"(?i)(?<![a-z0-9])prompt\s+engineering(?![a-z0-9])",)),
    ("Tool Calling", "AI/ML", (r"(?i)(?<![a-z0-9])tool\s+calling(?![a-z0-9])", r"(?i)(?<![a-z0-9])tool\s+use(?![a-z0-9])")),
    ("Docker", "Tools", (r"(?i)(?<![a-z0-9])docker(?![a-z0-9])",)),
    ("Terraform", "Tools", (r"(?i)(?<![a-z0-9])terraform(?![a-z0-9])",)),
    ("Git/GitHub", "Tools", (r"(?i)(?<![a-z0-9])github(?![a-z0-9])", r"(?i)(?<![a-z0-9])git(?![a-z0-9])")),
    ("CI/CD", "Tools", (r"(?i)(?<![a-z0-9])ci/cd(?![a-z0-9])", r"(?i)continuous\s+integration")),
    ("AWS", "Tools", (r"(?i)(?<![a-z0-9])aws(?![a-z0-9])",)),
    ("AWS CloudFormation", "Tools", (r"(?i)(?<![a-z0-9])cloudformation(?![a-z0-9])",)),
    ("Azure", "Tools", (r"(?i)(?<![a-z0-9])azure(?![a-z0-9])",)),
    ("GCP", "Tools", (r"(?i)(?<![a-z0-9])gcp(?![a-z0-9])", r"(?i)google\s+cloud")),
    ("Kubernetes", "Tools", (r"(?i)(?<![a-z0-9])kubernetes(?![a-z0-9])",)),
    ("Kafka", "Tools", (r"(?i)(?<![a-z0-9])kafka(?![a-z0-9])",)),
    ("Istio", "Tools", (r"(?i)(?<![a-z0-9])istio(?![a-z0-9])",)),
    ("Linux", "Tools", (r"(?i)(?<![a-z0-9])linux(?![a-z0-9])",)),
    ("Datadog", "Tools", (r"(?i)(?<![a-z0-9])datadog(?![a-z0-9])",)),
    ("AWS CloudWatch", "Tools", (r"(?i)(?<![a-z0-9])cloudwatch(?![a-z0-9])",)),
    ("Databricks", "Tools", (r"(?i)(?<![a-z0-9])databricks(?![a-z0-9])",)),
    ("AWS Lambda", "Tools", (r"(?i)(?<![a-z0-9])lambda(?![a-z0-9])",)),
    ("AWS Glue", "Tools", (r"(?i)(?<![a-z0-9])glue(?![a-z0-9])",)),
    ("AWS Athena", "Tools", (r"(?i)(?<![a-z0-9])athena(?![a-z0-9])",)),
    ("AWS Batch", "Tools", (r"(?i)(?<![a-z0-9])batch(?![a-z0-9])",)),
    ("AWS EventBridge", "Tools", (r"(?i)(?<![a-z0-9])eventbridge(?![a-z0-9])",)),
    ("ECS Fargate", "Tools", (r"(?i)(?<![a-z0-9])ecs\s+fargate(?![a-z0-9])", r"(?i)(?<![a-z0-9])fargate(?![a-z0-9])")),
    ("Postman", "Tools", (r"(?i)(?<![a-z0-9])postman(?![a-z0-9])",)),
    ("Jira", "Tools", (r"(?i)(?<![a-z0-9])jira(?![a-z0-9])",)),
    ("SCIM", "Tools", (r"(?i)(?<![a-z0-9])scim(?![a-z0-9])",)),
    ("LDAP", "Tools", (r"(?i)(?<![a-z0-9])ldap(?![a-z0-9])",)),
    ("Active Directory", "Tools", (r"(?i)(?<![a-z0-9])active\s+directory(?![a-z0-9])",)),
    ("SAML", "Tools", (r"(?i)(?<![a-z0-9])saml(?![a-z0-9])",)),
    ("SSO", "Tools", (r"(?i)(?<![a-z0-9])sso(?![a-z0-9])",)),
    ("OAuth2", "Tools", (r"(?i)(?<![a-z0-9])oauth2(?![a-z0-9])", r"(?i)(?<![a-z0-9])oauth\s*2(?![a-z0-9])")),
    ("OpenID Connect", "Tools", (r"(?i)(?<![a-z0-9])openid\s+connect(?![a-z0-9])",)),
    ("SOAP", "Tools", (r"(?i)(?<![a-z0-9])soap(?![a-z0-9])",)),
    ("REST", "Tools", (r"(?i)(?<![a-z0-9])rest(?:\s+apis?)?(?![a-z0-9])",)),
    ("RBAC", "Tools", (r"(?i)(?<![a-z0-9])rbac(?![a-z0-9])",)),
    ("ABAC", "Tools", (r"(?i)(?<![a-z0-9])abac(?![a-z0-9])",)),
    ("ReBAC", "Tools", (r"(?i)(?<![a-z0-9])rebac(?![a-z0-9])",)),
)


class TailoringService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.retrieval_service = RetrievalService(db)
        self.ollama_service = OllamaService()
        self.prompt_service = PromptService()
        self.validation_service = BulletValidationService()
        self.placement_service = PlacementService()

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
            raw_response = self.ollama_service.chat(messages, json_format=True, options={"temperature": 0.1})
        except OllamaError as exc:
            raise TailoringError(str(exc), status.HTTP_503_SERVICE_UNAVAILABLE) from exc

        parsed = self._parse_llm_json(raw_response)
        bullets, rejected_bullets = self._map_bullets(
            parsed.get("bullets", []),
            retrieved_context,
            request.strict_mode,
            request.job_description,
        )
        llm_skill_suggestions = self._map_skill_suggestions(
            parsed.get("skill_suggestions", parsed.get("skills", [])),
            retrieved_context,
            request.job_description,
        )
        skill_suggestions = self._merge_skill_suggestions(
            self._extract_jd_skill_suggestions(request.job_description),
            llm_skill_suggestions,
        )
        warnings = self._normalize_warnings(parsed.get("warnings", []))
        warnings.extend(self._validation_warnings(rejected_bullets))

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
            skill_suggestions=skill_suggestions,
            rejected_bullets=rejected_bullets,
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

    def _map_bullets(
        self,
        raw_bullets: Any,
        retrieved_context: list[SearchResult],
        strict_mode: bool = True,
        job_description: str = "",
    ) -> tuple[list[TailoredBullet], list[RejectedBullet]]:
        if not isinstance(raw_bullets, list):
            raise TailoringError("Ollama response was missing a valid bullets list.", status.HTTP_502_BAD_GATEWAY)

        mapped: list[TailoredBullet] = []
        rejected: list[RejectedBullet] = []
        for raw_bullet in raw_bullets:
            if not isinstance(raw_bullet, dict):
                continue

            bullet_text = self._string_value(raw_bullet.get("bullet"))
            if not bullet_text or bullet_text.lower() == "not enough evidence":
                continue

            source_chunk_ids = self._source_numbers_to_chunk_ids(raw_bullet.get("source_numbers"), retrieved_context)
            cited_sources = self._sources_for_chunk_ids(source_chunk_ids, retrieved_context)
            bullet = TailoredBullet(
                bullet=bullet_text,
                matched_requirement=self._string_value(raw_bullet.get("matched_requirement")) or "Not specified",
                evidence_strength=self._normalize_evidence_strength(raw_bullet.get("evidence_strength")),
                source_chunk_ids=source_chunk_ids,
                placement=self.placement_service.place_bullet(cited_sources, bullet_text),
                notes=self._string_value(raw_bullet.get("notes")),
            )

            if not strict_mode:
                mapped.append(bullet)
                continue

            validation = self.validation_service.validate(
                raw_bullet=raw_bullet,
                bullet=bullet,
                retrieved_context=retrieved_context,
                strict_mode=strict_mode,
                job_description=job_description,
            )
            if validation.bullet:
                mapped.append(validation.bullet)
            elif validation.rejected_bullet:
                rejected.append(validation.rejected_bullet)

        return mapped, rejected

    def _map_skill_suggestions(
        self,
        raw_skills: Any,
        retrieved_context: list[SearchResult],
        job_description: str,
    ) -> list[TailoredSkill]:
        if not isinstance(raw_skills, list):
            return []

        mapped: list[TailoredSkill] = []
        seen: set[tuple[str, str]] = set()
        for raw_skill in raw_skills:
            if not isinstance(raw_skill, dict):
                continue

            skill = self._string_value(raw_skill.get("skill"))
            category = self._normalize_skill_category(raw_skill.get("category"))
            if not skill or not category:
                continue
            if not self._skill_is_mentioned(skill, job_description):
                continue

            source_chunk_ids = self._source_numbers_to_chunk_ids(raw_skill.get("source_numbers"), retrieved_context)

            key = (skill.lower(), category)
            if key in seen:
                continue
            seen.add(key)

            mapped.append(
                TailoredSkill(
                    skill=skill,
                    category=category,
                    matched_requirement=self._string_value(raw_skill.get("matched_requirement")) or f"{skill} mentioned in job description",
                    evidence_strength="jd",
                    source_chunk_ids=source_chunk_ids,
                    notes=self._string_value(raw_skill.get("notes")) or "Explicitly mentioned in the job description; review before adding.",
                )
            )

        return mapped

    def _extract_jd_skill_suggestions(self, job_description: str) -> list[TailoredSkill]:
        suggestions: list[TailoredSkill] = []
        for skill, category, patterns in JD_SKILL_CATALOG:
            if not any(re.search(pattern, job_description) for pattern in patterns):
                continue
            suggestions.append(
                TailoredSkill(
                    skill=skill,
                    category=category,
                    matched_requirement=f"{skill} explicitly mentioned in the job description",
                    evidence_strength="jd",
                    source_chunk_ids=[],
                    notes="Explicitly mentioned in the job description; review before adding.",
                )
            )

        return suggestions

    def _merge_skill_suggestions(self, *skill_groups: list[TailoredSkill]) -> list[TailoredSkill]:
        merged: list[TailoredSkill] = []
        seen: set[tuple[str, str]] = set()
        for skill_group in skill_groups:
            for skill in skill_group:
                key = (skill.skill.lower(), skill.category)
                if key in seen:
                    continue
                seen.add(key)
                merged.append(skill)
        return merged

    def _source_numbers_to_chunk_ids(self, source_numbers: Any, retrieved_context: list[SearchResult]):
        return chunk_ids_from_source_numbers(source_numbers, retrieved_context)

    def _sources_for_chunk_ids(self, chunk_ids: list, retrieved_context: list[SearchResult]) -> list[SearchResult]:
        source_lookup = {result.chunk_id: result for result in retrieved_context}
        return [source_lookup[chunk_id] for chunk_id in chunk_ids if chunk_id in source_lookup]

    def _normalize_warnings(self, warnings: Any) -> list[str]:
        if not isinstance(warnings, list):
            return []
        return [warning.strip() for warning in warnings if isinstance(warning, str) and warning.strip()]

    def _normalize_evidence_strength(self, value: Any) -> str:
        normalized = self._string_value(value).lower()
        if normalized in {"high", "medium", "low"}:
            return normalized
        return "low"

    def _normalize_skill_category(self, value: Any) -> str:
        raw = self._string_value(value).lower().replace("&", " and ")
        normalized = re.sub(r"[^a-z0-9/]+", " ", raw).strip()
        return SKILL_CATEGORIES.get(normalized, SKILL_CATEGORIES.get(raw.strip(), ""))

    def _skill_is_mentioned(self, skill: str, text: str) -> bool:
        skill_text = skill.strip().lower()
        haystack = text.lower()
        if not skill_text or not haystack:
            return False

        if re.search(rf"(?<![a-z0-9+#]){re.escape(skill_text)}(?![a-z0-9+#])", haystack):
            return True

        aliases = {
            "postgresql": ("postgres", "postgresql"),
            "node.js": ("node", "node.js", "nodejs"),
            "next.js": ("next", "next.js", "nextjs"),
            "javascript": ("javascript", "js"),
            "typescript": ("typescript", "ts"),
            "ci/cd": ("ci/cd", "ci cd", "continuous integration"),
            "go": ("go", "golang"),
        }
        return any(
            re.search(rf"(?<![a-z0-9+#]){re.escape(alias)}(?![a-z0-9+#])", haystack)
            for alias in aliases.get(skill_text, ())
        )

    def _validation_warnings(self, rejected_bullets: list[RejectedBullet]) -> list[str]:
        warnings: list[str] = []
        for rejected in rejected_bullets:
            reason_text = "; ".join(rejected.reasons)
            warnings.append(f"Rejected unsupported bullet: {rejected.bullet} Reason: {reason_text}")
        return warnings

    def _string_value(self, value: Any) -> str:
        return value.strip() if isinstance(value, str) else ""

    def _clean_optional(self, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None
