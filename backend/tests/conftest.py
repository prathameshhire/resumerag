"""Shared pytest fixtures for the ResumeRAG test suite.

DATABASE_URL must be set before any app module is imported because
app.database creates the SQLAlchemy engine at module scope.  We set it here
at module scope (not inside a fixture) so it is in place by the time pytest
begins collecting and importing test files.

If DATABASE_URL is already in the environment (e.g. inside the Docker backend
container) os.environ.setdefault leaves it untouched.  When running tests
locally outside Docker, the fallback points at the same default credentials
used by docker-compose so that `docker compose exec backend pytest` works
without any extra configuration.
"""

import os
import uuid
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

# ── must come before any `from app.*` import ─────────────────────────────────
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://resumerag:resumerag@localhost:5432/resumerag",
)
# ─────────────────────────────────────────────────────────────────────────────

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app


# ---------------------------------------------------------------------------
# Minimal fake database session
# ---------------------------------------------------------------------------

class _FakeDB:
    """A lightweight stand-in for a SQLAlchemy Session.

    Only the methods called by the service layer need to be present.
    Tests that need richer behaviour can replace individual attributes via
    monkeypatch or by subclassing.
    """

    def __init__(self) -> None:
        self._store: dict[Any, Any] = {}
        self.added: list[Any] = []
        self.committed = False
        self.rolled_back = False

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    def flush(self) -> None:
        pass

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        pass

    def refresh(self, obj: Any) -> None:
        pass

    def get(self, model: Any, pk: Any) -> Any:
        return self._store.get((model, pk))

    def delete(self, obj: Any) -> None:
        pass

    def execute(self, *args: Any, **kwargs: Any) -> MagicMock:
        return MagicMock()


# ---------------------------------------------------------------------------
# Core fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_db() -> _FakeDB:
    """A fresh _FakeDB instance per test."""
    return _FakeDB()


@pytest.fixture
def client(fake_db: _FakeDB) -> Generator[TestClient, None, None]:
    """TestClient with get_db overridden to return a fake session.

    Using app.dependency_overrides is the idiomatic FastAPI way to replace
    dependencies in tests without touching production code.
    """
    app.dependency_overrides[get_db] = lambda: fake_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def plain_client() -> TestClient:
    """TestClient with no dependency overrides — for routes that need no DB."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# Sample data helpers
# ---------------------------------------------------------------------------

MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 3 3]>>endobj\n"
    b"xref\n0 4\n0000000000 65535 f\n"
    b"0000000009 00000 n\n"
    b"0000000058 00000 n\n"
    b"0000000115 00000 n\n"
    b"trailer<</Size 4/Root 1 0 R>>\n"
    b"startxref\n190\n%%EOF"
)

SAMPLE_TEXT = "This is a test document about software engineering and Python development."

SAMPLE_JD = (
    "We are looking for a Software Engineer with experience in Python, FastAPI, "
    "PostgreSQL, and Docker.  You will build scalable backend services and "
    "collaborate with cross-functional teams."
)

SAMPLE_DOCUMENT_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
SAMPLE_CHUNK_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


# ---------------------------------------------------------------------------
# Service-level mock factories
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_ingestion_service() -> Generator[MagicMock, None, None]:
    """Patch IngestionService so route handlers receive a controllable mock.

    Yields the *instance* mock (the object returned by IngestionService(db)).
    Configure it per-test:  mock_ingestion_service.list_documents.return_value = [...]
    """
    with patch("app.api.documents.IngestionService") as mock_cls:
        instance = mock_cls.return_value
        yield instance


@pytest.fixture
def mock_retrieval_service() -> Generator[MagicMock, None, None]:
    """Patch RetrievalService so search routes receive a controllable mock."""
    with patch("app.api.search.RetrievalService") as mock_cls:
        instance = mock_cls.return_value
        yield instance


@pytest.fixture
def mock_tailoring_service() -> Generator[MagicMock, None, None]:
    """Patch TailoringService so tailor routes receive a controllable mock."""
    with patch("app.api.tailor.TailoringService") as mock_cls:
        instance = mock_cls.return_value
        yield instance


@pytest.fixture
def mock_ollama_service() -> Generator[MagicMock, None, None]:
    """Patch OllamaService used directly by the tailor/test-ollama route."""
    with patch("app.api.tailor.OllamaService") as mock_cls:
        instance = mock_cls.return_value
        yield instance
