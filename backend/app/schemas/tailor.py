import uuid

from pydantic import BaseModel, Field

from app.schemas.search import SearchResult


class OllamaTestRequest(BaseModel):
    message: str = "Reply with: ResumeRAG Ollama test ok."


class OllamaTestResponse(BaseModel):
    model: str
    response: str


class TailorBulletsRequest(BaseModel):
    job_description: str = Field(min_length=1)
    target_role: str | None = None
    company_name: str | None = None
    bullet_count: int = Field(default=6, ge=1, le=8)
    tone: str = "technical"
    strict_mode: bool = True
    top_k: int | None = Field(default=None, ge=1, le=12)


class ResumePlacement(BaseModel):
    section: str
    entry: str
    rationale: str


class TailoredBullet(BaseModel):
    bullet: str
    matched_requirement: str
    evidence_strength: str
    source_chunk_ids: list[uuid.UUID]
    placement: ResumePlacement
    notes: str | None = None


class TailoredSkill(BaseModel):
    skill: str
    category: str
    matched_requirement: str
    evidence_strength: str
    source_chunk_ids: list[uuid.UUID]
    notes: str | None = None


class RejectedBullet(BaseModel):
    bullet: str
    matched_requirement: str
    source_chunk_ids: list[uuid.UUID]
    reasons: list[str]


class TailorBulletsResponse(BaseModel):
    query_id: uuid.UUID
    target_role: str | None
    company_name: str | None
    bullets: list[TailoredBullet]
    skill_suggestions: list[TailoredSkill] = []
    rejected_bullets: list[RejectedBullet] = []
    retrieved_context: list[SearchResult]
    warnings: list[str]
