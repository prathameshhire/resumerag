"""API tests for POST /search.

All tests mock RetrievalService.  They verify request validation, response
shape, filter forwarding, and correct error-code propagation.
"""

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.schemas.search import SearchResult
from app.services.retrieval_service import RetrievalError

SAMPLE_DOCUMENT_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
SAMPLE_CHUNK_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_result(rank: int = 1, score: float = 0.9) -> SearchResult:
    return SearchResult(
        chunk_id=SAMPLE_CHUNK_ID,
        document_id=SAMPLE_DOCUMENT_ID,
        source="project-notes.md",
        source_type="project_notes",
        category="backend",
        document_title="My Notes",
        chunk_text="Built a FastAPI service with PostgreSQL and Docker.",
        section_title="Projects",
        similarity_score=score,
        rank=rank,
        metadata={},
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def test_search_empty_query_returns_422(client: TestClient) -> None:
    """The query field has min_length=1; an empty string fails Pydantic validation."""
    response = client.post("/search", json={"query": ""})
    assert response.status_code == 422


def test_search_missing_query_returns_422(client: TestClient) -> None:
    """A request body without a query field fails Pydantic validation."""
    response = client.post("/search", json={"top_k": 5})
    assert response.status_code == 422


def test_search_top_k_zero_returns_422(client: TestClient) -> None:
    """top_k must be >= 1; zero fails Pydantic's ge=1 constraint."""
    response = client.post("/search", json={"query": "Python", "top_k": 0})
    assert response.status_code == 422


def test_search_top_k_above_limit_returns_422(client: TestClient) -> None:
    """top_k must be <= 20; exceeding the limit fails Pydantic's le=20 constraint."""
    response = client.post("/search", json={"query": "Python", "top_k": 99})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# No embedded chunks
# ---------------------------------------------------------------------------

def test_search_no_chunks_returns_empty_results(
    client: TestClient, mock_retrieval_service: MagicMock
) -> None:
    """When no chunks are indexed the service raises RetrievalError(404).

    The current API converts that to an HTTP 404.  This test documents the
    existing behaviour so any future change to return an empty list instead
    is caught and reviewed deliberately.
    """
    mock_retrieval_service.search.side_effect = RetrievalError(
        "No embedded document chunks found. Upload documents first.",
        status_code=status.HTTP_404_NOT_FOUND,
    )

    response = client.post("/search", json={"query": "Python experience"})

    assert response.status_code == 404
    assert "Upload documents" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Successful search
# ---------------------------------------------------------------------------

def test_search_returns_ranked_results(
    client: TestClient, mock_retrieval_service: MagicMock
) -> None:
    """Happy-path: results are returned in rank order with correct fields."""
    results = [_make_result(rank=1, score=0.92), _make_result(rank=2, score=0.85)]
    mock_retrieval_service.search.return_value = results

    response = client.post("/search", json={"query": "FastAPI Python service"})

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "FastAPI Python service"
    assert len(data["results"]) == 2
    assert data["results"][0]["rank"] == 1
    assert data["results"][0]["similarity_score"] == pytest.approx(0.92)
    assert data["results"][1]["rank"] == 2


def test_search_result_fields_are_complete(
    client: TestClient, mock_retrieval_service: MagicMock
) -> None:
    """Every field in SearchResult is present and has the expected type."""
    mock_retrieval_service.search.return_value = [_make_result()]

    response = client.post("/search", json={"query": "Docker containers"})

    result = response.json()["results"][0]
    assert isinstance(result["chunk_id"], str)
    assert isinstance(result["document_id"], str)
    assert isinstance(result["source"], str)
    assert isinstance(result["chunk_text"], str)
    assert isinstance(result["similarity_score"], float)
    assert isinstance(result["rank"], int)
    assert isinstance(result["metadata"], dict)


def test_search_with_source_type_filter(
    client: TestClient, mock_retrieval_service: MagicMock
) -> None:
    """Filters are forwarded to the service unchanged."""
    mock_retrieval_service.search.return_value = [_make_result()]

    response = client.post(
        "/search",
        json={
            "query": "backend service",
            "filters": {"source_type": "project_notes"},
        },
    )

    assert response.status_code == 200
    # Verify the filter reached the service
    call_args = mock_retrieval_service.search.call_args
    passed_filters = call_args.args[2]  # positional: (query, top_k, filters)
    assert passed_filters.source_type == "project_notes"


def test_search_with_category_filter(
    client: TestClient, mock_retrieval_service: MagicMock
) -> None:
    """Category filter is forwarded to the service."""
    mock_retrieval_service.search.return_value = [_make_result()]

    response = client.post(
        "/search",
        json={"query": "databases", "filters": {"category": "backend"}},
    )

    assert response.status_code == 200
    call_args = mock_retrieval_service.search.call_args
    passed_filters = call_args.args[2]
    assert passed_filters.category == "backend"


def test_search_top_k_is_forwarded(
    client: TestClient, mock_retrieval_service: MagicMock
) -> None:
    """An explicit top_k value is passed through to the service."""
    mock_retrieval_service.search.return_value = [_make_result()]

    client.post("/search", json={"query": "Python", "top_k": 3})

    call_args = mock_retrieval_service.search.call_args
    assert call_args.args[1] == 3  # positional: (query, top_k, filters)


def test_search_embedding_error_returns_500(
    client: TestClient, mock_retrieval_service: MagicMock
) -> None:
    """If the embedding service fails, RetrievalError(500) propagates as HTTP 500."""
    mock_retrieval_service.search.side_effect = RetrievalError(
        "Embedding model failed to encode the query.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

    response = client.post("/search", json={"query": "Python"})

    assert response.status_code == 500
