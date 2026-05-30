import uuid
from typing import Any

from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    source_type: str | None = None
    category: str | None = None


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)
    filters: SearchFilters | None = None


class SearchResult(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    source: str
    chunk_text: str
    section_title: str | None
    similarity_score: float
    rank: int
    metadata: dict[str, Any]


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
