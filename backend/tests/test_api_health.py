"""API tests for /health and /health/full."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.database import get_db
from app.main import app


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

def test_health_returns_ok(plain_client: TestClient) -> None:
    """Basic liveness probe — no database access required."""
    response = plain_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["backend"] is True


# ---------------------------------------------------------------------------
# GET /health/full  — database reachable, pgvector present, Ollama up
# ---------------------------------------------------------------------------

def test_full_health_all_ok(client: TestClient) -> None:
    """All components healthy — database, pgvector, embedding model, Ollama."""
    with (
        patch("app.api.health._check_database") as mock_db_check,
        patch("app.api.health._check_pgvector") as mock_pgv_check,
        patch("app.api.health._check_embedding_model") as mock_emb_check,
        patch("app.api.health.OllamaService") as mock_ollama_cls,
    ):
        from app.schemas.health import ComponentHealth, EmbeddingModelHealth, OllamaHealth

        mock_db_check.return_value = ComponentHealth(ok=True)
        mock_pgv_check.return_value = ComponentHealth(ok=True)
        mock_emb_check.return_value = EmbeddingModelHealth(
            ok=True, model="sentence-transformers/all-MiniLM-L6-v2", dimension=384
        )
        mock_ollama_cls.return_value.health.return_value = (True, True, None)

        response = client.get("/health/full")

    assert response.status_code == 200
    data = response.json()
    assert data["backend"]["ok"] is True
    assert data["database"]["ok"] is True
    assert data["pgvector"]["ok"] is True
    assert data["embedding_model"]["ok"] is True
    assert data["ollama"]["ok"] is True
    assert data["ollama"]["model_available"] is True


def test_full_health_returns_200_when_database_is_down(client: TestClient) -> None:
    """A DB failure should produce a degraded (ok=False) status, not an HTTP 5xx.

    The health endpoint is a diagnostic — it must remain reachable even when
    the database is unavailable, so the operator can see *what* is broken.
    """
    with (
        patch("app.api.health._check_database") as mock_db_check,
        patch("app.api.health._check_pgvector") as mock_pgv_check,
        patch("app.api.health._check_embedding_model") as mock_emb_check,
        patch("app.api.health.OllamaService") as mock_ollama_cls,
    ):
        from app.schemas.health import ComponentHealth, EmbeddingModelHealth, OllamaHealth

        mock_db_check.return_value = ComponentHealth(
            ok=False, message="connection refused"
        )
        mock_pgv_check.return_value = ComponentHealth(
            ok=False, message="pgvector check failed: connection refused"
        )
        mock_emb_check.return_value = EmbeddingModelHealth(
            ok=True, model="sentence-transformers/all-MiniLM-L6-v2", dimension=384
        )
        mock_ollama_cls.return_value.health.return_value = (True, True, None)

        response = client.get("/health/full")

    assert response.status_code == 200
    data = response.json()
    assert data["database"]["ok"] is False
    assert "connection refused" in data["database"]["message"]
    assert data["backend"]["ok"] is True  # backend itself is still up


def test_full_health_reports_ollama_unreachable(client: TestClient) -> None:
    """Ollama down should be surfaced as ok=False, model_available=False."""
    with (
        patch("app.api.health._check_database") as mock_db_check,
        patch("app.api.health._check_pgvector") as mock_pgv_check,
        patch("app.api.health._check_embedding_model") as mock_emb_check,
        patch("app.api.health.OllamaService") as mock_ollama_cls,
    ):
        from app.schemas.health import ComponentHealth, EmbeddingModelHealth

        mock_db_check.return_value = ComponentHealth(ok=True)
        mock_pgv_check.return_value = ComponentHealth(ok=True)
        mock_emb_check.return_value = EmbeddingModelHealth(
            ok=True, model="sentence-transformers/all-MiniLM-L6-v2", dimension=384
        )
        mock_ollama_cls.return_value.health.return_value = (
            False, False, "Ollama server is not reachable."
        )

        response = client.get("/health/full")

    assert response.status_code == 200
    data = response.json()
    assert data["ollama"]["ok"] is False
    assert data["ollama"]["model_available"] is False
    assert "not reachable" in data["ollama"]["message"]


def test_full_health_reports_model_missing(client: TestClient) -> None:
    """Ollama reachable but requested model not pulled → ok=False, specific message."""
    with (
        patch("app.api.health._check_database") as mock_db_check,
        patch("app.api.health._check_pgvector") as mock_pgv_check,
        patch("app.api.health._check_embedding_model") as mock_emb_check,
        patch("app.api.health.OllamaService") as mock_ollama_cls,
    ):
        from app.schemas.health import ComponentHealth, EmbeddingModelHealth

        mock_db_check.return_value = ComponentHealth(ok=True)
        mock_pgv_check.return_value = ComponentHealth(ok=True)
        mock_emb_check.return_value = EmbeddingModelHealth(
            ok=True, model="sentence-transformers/all-MiniLM-L6-v2", dimension=384
        )
        mock_ollama_cls.return_value.health.return_value = (
            False, False, "Ollama is reachable, but model 'llama3.2' was not found."
        )

        response = client.get("/health/full")

    assert response.status_code == 200
    data = response.json()
    assert data["ollama"]["ok"] is False
    assert "not found" in data["ollama"]["message"]
