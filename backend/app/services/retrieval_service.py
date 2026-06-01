from typing import Any

from fastapi import status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.schemas.search import SearchFilters, SearchResult
from app.services.embedding_service import EmbeddingError, get_embedding_service


class RetrievalError(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class RetrievalService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.embedding_service = get_embedding_service()

    def search(self, query: str, top_k: int | None, filters: SearchFilters | None) -> list[SearchResult]:
        cleaned_query = query.strip()
        if not cleaned_query:
            raise RetrievalError("Search query cannot be empty.")

        limit = top_k or self.settings.retrieval_top_k
        active_filters = filters or SearchFilters()

        try:
            query_embedding = self.embedding_service.embed_text(cleaned_query)
        except EmbeddingError as exc:
            raise RetrievalError(str(exc), status.HTTP_500_INTERNAL_SERVER_ERROR) from exc

        params: dict[str, Any] = {
            "query_embedding": self._vector_literal(query_embedding),
            "top_k": limit,
        }
        where_clauses = ["chunks.embedding IS NOT NULL"]

        if active_filters.source_type:
            where_clauses.append("documents.source_type = :source_type")
            params["source_type"] = active_filters.source_type
        if active_filters.category:
            where_clauses.append("documents.category = :category")
            params["category"] = active_filters.category

        sql = text(
            f"""
            SELECT
                chunks.id AS chunk_id,
                chunks.document_id AS document_id,
                documents.original_filename AS source,
                documents.source_type AS source_type,
                documents.category AS category,
                documents.title AS document_title,
                chunks.chunk_text AS chunk_text,
                chunks.section_title AS section_title,
                chunks.metadata AS metadata,
                1 - (chunks.embedding <=> CAST(:query_embedding AS vector)) AS similarity_score
            FROM chunks
            JOIN documents ON documents.id = chunks.document_id
            WHERE {" AND ".join(where_clauses)}
            ORDER BY chunks.embedding <=> CAST(:query_embedding AS vector)
            LIMIT :top_k
            """
        )

        rows = self.db.execute(sql, params).mappings().all()
        if not rows:
            raise RetrievalError("No embedded document chunks found. Upload documents first.", status.HTTP_404_NOT_FOUND)

        return [
            SearchResult(
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                source=row["source"],
                source_type=row["source_type"],
                category=row["category"],
                document_title=row["document_title"],
                chunk_text=row["chunk_text"],
                section_title=row["section_title"],
                similarity_score=float(row["similarity_score"]),
                rank=index,
                metadata=row["metadata"] or {},
            )
            for index, row in enumerate(rows, start=1)
        ]

    def _vector_literal(self, vector: list[float]) -> str:
        return "[" + ",".join(str(value) for value in vector) + "]"
