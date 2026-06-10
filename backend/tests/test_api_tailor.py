"""API tests for /tailor/test-ollama and /tailor/bullets.

Tests mock OllamaService and TailoringService so they run without a live
Ollama instance or a real database.
"""

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.schemas.search import SearchResult
from app.schemas.tailor import (
    ResumePlacement,
    TailoredBullet,
    TailorBulletsResponse,
)
from app.services.ollama_service import OllamaError
from app.services.tailoring_service import TailoringError

SAMPLE_DOCUMENT_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
SAMPLE_CHUNK_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_QUERY_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")

def _make_search_result() -> SearchResult:
    return SearchResult(
        chunk_id=SAMPLE_CHUNK_ID,
        document_id=SAMPLE_DOCUMENT_ID,
        source="backend-projects.md",
        source_type="project_notes",
        category="backend",
        document_title=None,
        chunk_text="Reduced API latency by 40% by introducing async batch processing.",
        section_title="Projects",
        similarity_score=0.91,
        rank=1,
        metadata={},
    )


def _make_bullet() -> TailoredBullet:
    return TailoredBullet(
        bullet="Reduced API latency by 40% through async batch processing.",
        matched_requirement="Experience optimising backend service performance.",
        evidence_strength="high",
        source_chunk_ids=[SAMPLE_CHUNK_ID],
        placement=ResumePlacement(
            section="Projects",
            entry="ResumeRAG",
            rationale="Directly evidenced by latency reduction work.",
        ),
        notes=None,
    )


def _make_bullets_response(warnings: list[str] | None = None) -> TailorBulletsResponse:
    return TailorBulletsResponse(
        query_id=_QUERY_ID,
        target_role="Backend Engineer",
        company_name="Acme Corp",
        bullets=[_make_bullet()],
        skill_suggestions=[],
        rejected_bullets=[],
        retrieved_context=[_make_search_result()],
        warnings=warnings or [],
    )


# ---------------------------------------------------------------------------
# POST /tailor/test-ollama
# ---------------------------------------------------------------------------

def test_test_ollama_connected(
    client: TestClient, mock_ollama_service: MagicMock
) -> None:
    """Ollama reachable and responding → 200 with model name and response text."""
    mock_ollama_service.chat.return_value = "ResumeRAG Ollama test ok."

    response = client.post(
        "/tailor/test-ollama",
        json={"message": "Reply with: ResumeRAG Ollama test ok."},
    )

    assert response.status_code == 200
    data = response.json()
    assert "model" in data
    assert data["response"] == "ResumeRAG Ollama test ok."


def test_test_ollama_not_reachable_returns_503(
    client: TestClient, mock_ollama_service: MagicMock
) -> None:
    """Ollama not reachable → 503 with an informative error."""
    mock_ollama_service.chat.side_effect = OllamaError("Ollama server is not reachable.")

    response = client.post(
        "/tailor/test-ollama",
        json={"message": "ping"},
    )

    assert response.status_code == 503
    assert "not reachable" in response.json()["detail"]


def test_test_ollama_default_message(
    client: TestClient, mock_ollama_service: MagicMock
) -> None:
    """The message field has a default; an empty body should still succeed."""
    mock_ollama_service.chat.return_value = "ok"

    response = client.post("/tailor/test-ollama", json={})

    assert response.status_code == 200


# ---------------------------------------------------------------------------
# POST /tailor/bullets — request validation
# ---------------------------------------------------------------------------

def test_bullets_empty_job_description_returns_422(client: TestClient) -> None:
    """job_description has min_length=1; empty string fails Pydantic validation."""
    response = client.post(
        "/tailor/bullets",
        json={"job_description": ""},
    )
    assert response.status_code == 422


def test_bullets_missing_job_description_returns_422(client: TestClient) -> None:
    """job_description is required; omitting it fails Pydantic validation."""
    response = client.post("/tailor/bullets", json={"bullet_count": 3})
    assert response.status_code == 422


def test_bullets_bullet_count_above_max_returns_422(client: TestClient) -> None:
    """bullet_count has le=8; values above that fail Pydantic validation."""
    response = client.post(
        "/tailor/bullets",
        json={"job_description": "We need a Python developer.", "bullet_count": 99},
    )
    assert response.status_code == 422


def test_bullets_bullet_count_zero_returns_422(client: TestClient) -> None:
    """bullet_count has ge=1; zero fails Pydantic validation."""
    response = client.post(
        "/tailor/bullets",
        json={"job_description": "Python developer needed.", "bullet_count": 0},
    )
    assert response.status_code == 422


def test_bullets_top_k_above_max_returns_422(client: TestClient) -> None:
    """top_k has le=12; values above that fail Pydantic validation."""
    response = client.post(
        "/tailor/bullets",
        json={"job_description": "Python developer.", "top_k": 50},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /tailor/bullets — service integration
# ---------------------------------------------------------------------------

def test_bullets_happy_path(
    client: TestClient, mock_tailoring_service: MagicMock
) -> None:
    """Happy-path: service returns bullets and the response is serialised correctly."""
    mock_tailoring_service.generate_bullets.return_value = _make_bullets_response()

    response = client.post(
        "/tailor/bullets",
        json={"job_description": "Backend Engineer with Python and FastAPI experience."},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["query_id"] == str(_QUERY_ID)
    assert len(data["bullets"]) == 1

    bullet = data["bullets"][0]
    assert "bullet" in bullet
    assert "matched_requirement" in bullet
    assert "evidence_strength" in bullet
    assert "source_chunk_ids" in bullet
    assert "placement" in bullet


def test_bullets_response_includes_retrieved_context(
    client: TestClient, mock_tailoring_service: MagicMock
) -> None:
    """retrieved_context in the response allows the UI to show source evidence."""
    mock_tailoring_service.generate_bullets.return_value = _make_bullets_response()

    response = client.post(
        "/tailor/bullets",
        json={"job_description": "FastAPI and PostgreSQL experience required."},
    )

    data = response.json()
    assert len(data["retrieved_context"]) == 1
    ctx = data["retrieved_context"][0]
    assert "chunk_text" in ctx
    assert "similarity_score" in ctx


def test_bullets_with_warnings_when_no_context(
    client: TestClient, mock_tailoring_service: MagicMock
) -> None:
    """When no relevant context is found the service adds a warning; the API
    still returns 200 — warnings are surfaced in the response body, not as errors."""
    mock_tailoring_service.generate_bullets.return_value = _make_bullets_response(
        warnings=["No relevant document chunks found for this job description."]
    )

    response = client.post(
        "/tailor/bullets",
        json={"job_description": "Quantum computing experience required."},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["warnings"]) == 1
    assert "No relevant" in data["warnings"][0]


def test_bullets_no_documents_indexed_returns_error(
    client: TestClient, mock_tailoring_service: MagicMock
) -> None:
    """TailoringError propagates as the appropriate HTTP status code."""
    mock_tailoring_service.generate_bullets.side_effect = TailoringError(
        "No embedded document chunks found. Upload documents first.",
        status_code=404,
    )

    response = client.post(
        "/tailor/bullets",
        json={"job_description": "Python engineer needed."},
    )

    assert response.status_code == 404
    assert "Upload documents" in response.json()["detail"]


def test_bullets_ollama_failure_returns_503(
    client: TestClient, mock_tailoring_service: MagicMock
) -> None:
    """If Ollama is down during generation the service raises TailoringError(503)."""
    mock_tailoring_service.generate_bullets.side_effect = TailoringError(
        "Ollama server is not reachable.",
        status_code=503,
    )

    response = client.post(
        "/tailor/bullets",
        json={"job_description": "We need a Python developer."},
    )

    assert response.status_code == 503


def test_bullets_optional_fields_forwarded(
    client: TestClient, mock_tailoring_service: MagicMock
) -> None:
    """target_role and company_name are optional but forwarded when provided."""
    mock_tailoring_service.generate_bullets.return_value = _make_bullets_response()

    client.post(
        "/tailor/bullets",
        json={
            "job_description": "Backend Engineer.",
            "target_role": "Senior Backend Engineer",
            "company_name": "Acme Corp",
            "bullet_count": 4,
            "strict_mode": False,
        },
    )

    call_args = mock_tailoring_service.generate_bullets.call_args
    request_obj = call_args.args[0]
    assert request_obj.target_role == "Senior Backend Engineer"
    assert request_obj.company_name == "Acme Corp"
    assert request_obj.bullet_count == 4
    assert request_obj.strict_mode is False
