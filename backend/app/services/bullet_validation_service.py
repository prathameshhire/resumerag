import re
import uuid
from dataclasses import dataclass
from typing import Any

from app.schemas.search import SearchResult
from app.schemas.tailor import RejectedBullet, TailoredBullet


RISKY_TERMS = {
    "aws",
    "brute-force",
    "cloud-native",
    "cross-disciplinary",
    "distributed systems",
    "fault tolerant",
    "fault-tolerant",
    "helmet",
    "high availability",
    "kubernetes",
    "large distributed",
    "microservices",
    "on-call",
    "orchestration",
    "production issues",
    "rate limiting",
}

ROLE_CRITICAL_REQUIREMENT_GROUPS = {
    "C++": ("c++", "cpp"),
    "data storage systems": ("data storage", "storage system", "storage systems", "data management"),
    "data efficiency": ("deduplication", "dedupe", "reclamation", "replication", "wide-area"),
    "low-level systems": ("low-level", "hardware"),
    "concurrency and algorithms": ("concurrency", "algorithm", "algorithms", "data structure", "data structures"),
}

JOB_DESCRIPTION_STARTS = (
    "build and maintain",
    "built and maintained",
    "collaborate",
    "design and develop",
    "designed and developed",
    "participate in",
    "participated in",
    "use genai",
    "work in an agile",
    "write clean",
)

PLACEHOLDER_QUOTE_MARKERS = (
    "exact substring",
    "copied from source",
    "source quote",
)

STOPWORDS = {
    "about",
    "across",
    "added",
    "built",
    "clean",
    "code",
    "configured",
    "created",
    "designed",
    "developed",
    "engineering",
    "experience",
    "implemented",
    "improved",
    "local",
    "maintainable",
    "project",
    "source",
    "through",
    "using",
    "with",
}


@dataclass(frozen=True)
class RawBulletValidation:
    bullet: TailoredBullet | None
    rejected_bullet: RejectedBullet | None
    reasons: list[str]


class BulletValidationService:
    def validate(
        self,
        *,
        raw_bullet: dict[str, Any],
        bullet: TailoredBullet,
        retrieved_context: list[SearchResult],
        strict_mode: bool,
        job_description: str = "",
    ) -> RawBulletValidation:
        source_lookup = {result.chunk_id: result for result in retrieved_context}
        cited_sources = [source_lookup[chunk_id] for chunk_id in bullet.source_chunk_ids if chunk_id in source_lookup]
        cited_text = self._normalize(" ".join(source.chunk_text for source in cited_sources))
        bullet_text = self._normalize(bullet.bullet)

        reasons: list[str] = []
        if not cited_sources:
            reasons.append("No valid source chunks were cited.")

        if strict_mode and bullet.evidence_strength == "low":
            reasons.append("Strict mode rejected a low-evidence bullet.")

        for term in sorted(RISKY_TERMS):
            if term in bullet_text and term not in cited_text:
                reasons.append(f"Unsupported risky term: {term}.")

        if bullet_text.startswith(JOB_DESCRIPTION_STARTS):
            reasons.append("Bullet appears to restate the job description instead of user evidence.")

        overlap_reason = self._source_overlap_reason(bullet_text, cited_text)
        if overlap_reason:
            reasons.append(overlap_reason)

        quote_reason = self._evidence_quote_reason(raw_bullet, cited_text)
        if quote_reason:
            reasons.append(quote_reason)

        duplicate_reason = self._existing_resume_bullet_reason(bullet.bullet, cited_sources)
        if duplicate_reason:
            reasons.append(duplicate_reason)

        role_fit_reason = self._role_fit_reason(job_description, bullet_text, cited_text)
        if role_fit_reason:
            reasons.append(role_fit_reason)

        if reasons:
            return RawBulletValidation(
                bullet=None,
                rejected_bullet=RejectedBullet(
                    bullet=bullet.bullet,
                    matched_requirement=bullet.matched_requirement,
                    source_chunk_ids=bullet.source_chunk_ids,
                    reasons=reasons,
                ),
                reasons=reasons,
            )

        return RawBulletValidation(bullet=bullet, rejected_bullet=None, reasons=[])

    def _source_overlap_reason(self, bullet_text: str, cited_text: str) -> str | None:
        tokens = self._content_tokens(bullet_text)
        if len(tokens) < 4 or not cited_text:
            return None

        overlap = sum(1 for token in tokens if token in cited_text)
        if overlap / len(tokens) < 0.35:
            return f"Low source overlap: {overlap}/{len(tokens)} key terms found in cited chunks."

        return None

    def _role_fit_reason(
        self,
        job_description: str,
        bullet_text: str,
        cited_text: str,
    ) -> str | None:
        jd_text = self._normalize(job_description)
        if not jd_text:
            return None

        required_groups = self._matched_requirement_groups(jd_text)
        if len(required_groups) < 3:
            return None

        bullet_groups = self._matched_requirement_groups(bullet_text)
        cited_groups = self._matched_requirement_groups(cited_text)
        supported_groups = bullet_groups & cited_groups
        if supported_groups:
            return None

        return (
            "No evidence for role-critical systems/storage/C++ requirements; "
            "bullet appears transferable but not meaningfully tailored to this JD."
        )

    def _existing_resume_bullet_reason(self, bullet_text: str, cited_sources: list[SearchResult]) -> str | None:
        bullet_normalized = self._normalize(bullet_text)
        bullet_tokens = set(self._content_tokens(bullet_normalized))
        if len(bullet_tokens) < 5:
            return None

        for source in cited_sources:
            if (source.source_type or "").lower() != "resume":
                continue

            for candidate in self._resume_bullet_candidates(source.chunk_text):
                candidate_normalized = self._normalize(candidate)
                if len(candidate_normalized) < 40:
                    continue
                if bullet_normalized == candidate_normalized or bullet_normalized in candidate_normalized:
                    return "Bullet is already present in the uploaded resume; reject verbatim resume regurgitation."

                candidate_tokens = set(self._content_tokens(candidate_normalized))
                if len(candidate_tokens) < 5:
                    continue
                bullet_coverage = len(bullet_tokens & candidate_tokens) / len(bullet_tokens)
                candidate_coverage = len(bullet_tokens & candidate_tokens) / len(candidate_tokens)
                if bullet_coverage >= 0.9 and candidate_coverage >= 0.75:
                    return "Bullet is too close to an existing resume bullet; needs a meaningful rewrite."

        return None

    def _resume_bullet_candidates(self, text: str) -> list[str]:
        normalized = text.replace("\r", "\n")
        bullet_parts = re.split(r"(?:^|\n)\s*(?:[•*-]\s+)", normalized)
        candidates = [part.strip() for part in bullet_parts if part.strip()]
        if len(candidates) > 1:
            return candidates
        return [part.strip() for part in re.split(r"\n\s*\n|(?<=[.!?])\s+", normalized) if part.strip()]

    def _matched_requirement_groups(self, text: str) -> set[str]:
        return {
            group_name
            for group_name, markers in ROLE_CRITICAL_REQUIREMENT_GROUPS.items()
            if any(marker in text for marker in markers)
        }

    def _evidence_quote_reason(self, raw_bullet: dict[str, Any], cited_text: str) -> str | None:
        raw_quotes = raw_bullet.get("evidence_quotes") or raw_bullet.get("quotes")
        if raw_quotes is None and isinstance(raw_bullet.get("evidence_quote"), str):
            raw_quotes = [raw_bullet["evidence_quote"]]

        if raw_quotes is None:
            return None
        if not isinstance(raw_quotes, list):
            return "Evidence quote field was not a list."

        normalized_quotes = [self._normalize(quote) for quote in raw_quotes if isinstance(quote, str) and quote.strip()]
        if not normalized_quotes:
            return "Evidence quote field did not contain a usable quote."

        invalid_quotes: list[str] = []
        for quote in normalized_quotes:
            if any(marker in quote for marker in PLACEHOLDER_QUOTE_MARKERS):
                invalid_quotes.append("placeholder")
                continue
            if "..." in quote or len(quote) < 18:
                continue
            if quote not in cited_text:
                invalid_quotes.append("not found in cited chunks")

        if invalid_quotes and len(invalid_quotes) == len(normalized_quotes):
            return f"Evidence quote could not be verified ({invalid_quotes[0]})."

        return None

    def _content_tokens(self, text: str) -> list[str]:
        tokens = {
            token
            for token in re.split(r"[^a-z0-9+#.-]+", text)
            if len(token) >= 5 and token not in STOPWORDS
        }
        return sorted(tokens)

    def _normalize(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.lower()).strip()


def chunk_ids_from_source_numbers(source_numbers: Any, retrieved_context: list[SearchResult]) -> list[uuid.UUID]:
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
