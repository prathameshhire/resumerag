from pathlib import Path

from app.schemas.search import SearchResult
from app.schemas.tailor import ResumePlacement


PROJECT_NAME_OVERRIDES = {
    "fairshare": "FairShare",
    "resumerag": "ResumeRAG",
    "sentimentscope": "SentimentScope",
}

OLEI_SOURCE_MARKERS = (
    "appointment",
    "booking",
    "clinic",
    "hipaa",
    "jwt",
    "olei",
    "practitioner",
)

OLEI_RESUME_BULLET_MARKERS = OLEI_SOURCE_MARKERS + (
    "context api",
    "cross-platform data flow",
    "custom hooks",
    "memoization",
    "react hook form",
    "redundant api calls",
    "redux",
    "reusable react components",
    "ui responsiveness",
)

PROJECT_MARKERS = (
    ("SentimentScope", ("sentimentscope", "youtube", "sentiment", "roberta", "comment classification")),
    ("ResumeRAG", ("resumerag", "ollama", "pgvector", "markitdown", "vector search")),
    ("FairShare", ("fairshare", "expense", "settlement", "balance reconciliation", "split")),
)


class PlacementService:
    def place_bullet(self, cited_sources: list[SearchResult], bullet_text: str = "") -> ResumePlacement:
        if not cited_sources:
            return ResumePlacement(
                section="Review manually",
                entry="Unplaced bullet",
                rationale="No validated source chunk was cited for this bullet.",
            )

        primary = cited_sources[0]
        inferred_project = self._infer_known_entry(primary, bullet_text)
        section = self._section_for_source(primary, inferred_project)
        entry = inferred_project or self._entry_for_source(primary)
        rationale_parts = [f"Based on {primary.source}"]

        if primary.section_title:
            rationale_parts.append(f"section '{primary.section_title}'")
        if inferred_project:
            rationale_parts.append(f"matched to '{inferred_project}' from bullet-level evidence")
        if primary.source_type:
            rationale_parts.append(f"source type '{self._format_label(primary.source_type)}'")

        return ResumePlacement(
            section=section,
            entry=entry,
            rationale=", ".join(rationale_parts) + ".",
        )

    def _section_for_source(self, source: SearchResult, inferred_entry: str | None = None) -> str:
        source_type = (source.source_type or "").lower()
        category = (source.category or "").lower()
        filename = source.source.lower()
        text = f"{source.section_title or ''} {source.chunk_text}".lower()

        if source_type == "work_experience" or "internship" in filename:
            return "Experience"
        if inferred_entry in {"FairShare", "ResumeRAG", "SentimentScope"}:
            return "Projects"
        if inferred_entry in {"Olei HR / Olei Clinic", "Internship experience"}:
            return "Experience"

        if source_type in {"project_notes", "github_readme"}:
            return "Projects"
        if source_type == "resume":
            if inferred_entry == "Olei HR / Olei Clinic":
                return "Experience"
            if inferred_entry in {"SentimentScope", "ResumeRAG", "FairShare"}:
                return "Projects"
            if any(marker in text for marker in ("experience", "intern", "olei", "clinic", "hr")):
                return "Experience"
            return "Summary or Skills"
        if source_type == "achievement_bank":
            return "Selected Achievements"
        if category == "leadership":
            return "Leadership"
        if category in {"backend", "data", "ml_infra", "fullstack"}:
            return "Projects"

        return "Projects or Experience"

    def _infer_known_entry(self, source: SearchResult, bullet_text: str) -> str | None:
        source_type = (source.source_type or "").lower()
        source_name = source.source.lower()

        if source_type == "resume":
            return self._infer_from_resume_bullet(bullet_text)

        if source_type == "work_experience" or "internship" in source_name:
            return source.section_title or "Internship experience"

        bullet_match = self._infer_from_text(bullet_text)
        if bullet_match:
            return bullet_match

        return self._infer_from_text(f"{source.section_title or ''} {source.source} {source.chunk_text}")

    def _infer_from_resume_bullet(self, text: str) -> str | None:
        normalized = text.lower()
        if any(marker in normalized for marker in OLEI_RESUME_BULLET_MARKERS):
            return "Olei HR / Olei Clinic"

        for project_name, markers in PROJECT_MARKERS:
            if any(marker in normalized for marker in markers):
                return project_name

        return None

    def _infer_from_text(self, text: str) -> str | None:
        normalized = text.lower()
        if any(marker in normalized for marker in OLEI_SOURCE_MARKERS):
            return "Olei HR / Olei Clinic"

        for project_name, markers in PROJECT_MARKERS:
            if any(marker in normalized for marker in markers):
                return project_name

        return None

    def _entry_for_source(self, source: SearchResult) -> str:
        if source.document_title:
            return source.document_title

        filename = Path(source.source).stem
        normalized = filename.replace("-evidence-notes", "").replace("_", "-").lower()
        if normalized in PROJECT_NAME_OVERRIDES:
            return PROJECT_NAME_OVERRIDES[normalized]
        if "internship" in normalized:
            return source.section_title or "Internship experience"
        if "resume" in normalized:
            return source.section_title or "Existing resume entry"

        return " ".join(word.capitalize() for word in normalized.split("-") if word) or source.source

    def _format_label(self, value: str) -> str:
        return " ".join(word.capitalize() for word in value.split("_"))
