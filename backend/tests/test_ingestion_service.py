"""Unit tests for IngestionService atomicity.

These tests verify that a failure anywhere between file-save and DB-commit
leaves the database clean (no orphan Document row) and the filesystem clean
(no orphan upload file).

They do NOT require a real database: they use a purpose-built FakeSession that
records which objects were added and whether commit/rollback was called.  The
embedding service and converter are monkeypatched to allow fine-grained failure
injection at specific points in the pipeline.

async def helpers are called via asyncio.run() so that pytest-asyncio is not
needed as an additional dependency.
"""

import asyncio
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.services.ingestion_service import IngestionError, IngestionService
from app.services.markitdown_service import ConversionError


# ---------------------------------------------------------------------------
# Fake collaborators
# ---------------------------------------------------------------------------

class _FakeSession:
    """Minimal SQLAlchemy Session stand-in that records what happened."""

    def __init__(self) -> None:
        self.added: list[Any] = []
        self.committed = False
        self.rolled_back = False

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    def flush(self) -> None:
        pass  # intentional no-op — confirms service no longer calls flush

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def refresh(self, obj: Any) -> None:
        # Simulate SQLAlchemy applying the column default (default=uuid.uuid4)
        # that a real session would have applied during flush/commit.
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()


class _FakeUpload:
    """Minimal UploadFile stand-in for testing."""

    def __init__(self, filename: str, content: bytes, content_type: str = "text/plain") -> None:
        self.filename = filename
        self.content_type = content_type
        self._content = content
        self._pos = 0

    async def read(self, size: int = -1) -> bytes:
        if size == -1:
            data = self._content[self._pos :]
            self._pos = len(self._content)
        else:
            data = self._content[self._pos : self._pos + size]
            self._pos += len(data)
        return data


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service(session: _FakeSession, tmp_path: Path) -> IngestionService:
    """Construct an IngestionService with a fake session and writable upload dir."""
    service = IngestionService.__new__(IngestionService)
    service.db = session
    service.settings = MagicMock()
    service.settings.upload_dir = str(tmp_path)
    service.settings.max_upload_mb = 20
    service.settings.chunk_size_chars = 800
    service.settings.chunk_overlap_chars = 100
    service.converter = MagicMock()
    service.chunker = MagicMock()
    service.embedding_service = MagicMock()
    return service


def _make_chunk_mock() -> MagicMock:
    chunk = MagicMock()
    chunk.chunk_text = "Built things."
    chunk.section_title = "Work"
    chunk.token_estimate = 4
    chunk.metadata = {}
    return chunk


# ---------------------------------------------------------------------------
# Tests: conversion failures
# ---------------------------------------------------------------------------

def test_conversion_failure_rolls_back_and_removes_file(tmp_path: Path) -> None:
    """If the converter raises ConversionError the DB is rolled back and the saved
    file is removed — no orphan file left on disk."""
    session = _FakeSession()
    service = _make_service(session, tmp_path)
    service.converter.convert_file_to_markdown.side_effect = ConversionError(
        "Document conversion failed."
    )

    with pytest.raises(IngestionError):
        asyncio.run(
            service.index_upload(_FakeUpload("doc.txt", b"content"), "notes", "be", "T", None)
        )

    assert session.rolled_back, "session.rollback() must be called on conversion failure"
    assert not session.committed, "session.commit() must NOT be called on failure"
    assert list(tmp_path.iterdir()) == [], "No upload file should remain on disk"


# ---------------------------------------------------------------------------
# Tests: embedding failures
# ---------------------------------------------------------------------------

def test_embedding_failure_rolls_back_and_removes_file(tmp_path: Path) -> None:
    """If the embedding service raises after chunking, the DB is rolled back and
    the saved file is removed."""
    from app.services.embedding_service import EmbeddingError

    session = _FakeSession()
    service = _make_service(session, tmp_path)
    service.converter.convert_file_to_markdown.return_value = "# Section\nContent."
    service.chunker.chunk_markdown.return_value = [_make_chunk_mock()]
    service.embedding_service.embed_texts.side_effect = EmbeddingError("Model failed.")

    with pytest.raises(IngestionError):
        asyncio.run(
            service.index_upload(_FakeUpload("notes.txt", b"# Section\nContent."), None, None, None, None)
        )

    assert session.rolled_back
    assert not session.committed
    assert list(tmp_path.iterdir()) == []


# ---------------------------------------------------------------------------
# Tests: happy path
# ---------------------------------------------------------------------------

def test_successful_ingestion_commits_once_without_rollback(tmp_path: Path) -> None:
    """On success exactly one commit is called and rollback is never called.

    This also confirms the Gap-2 fix: flush() was removed in favour of a
    single commit() at the end of the happy path.  _FakeSession.flush() is a
    no-op — the service is free to call it and nothing breaks — but the
    important invariant is commit() called once, rollback() never called.
    """
    session = _FakeSession()
    service = _make_service(session, tmp_path)
    service.converter.convert_file_to_markdown.return_value = "# Work\nBuilt things."
    service.chunker.chunk_markdown.return_value = [_make_chunk_mock()]
    service.embedding_service.embed_texts.return_value = [[0.1] * 384]

    result = asyncio.run(
        service.index_upload(
            _FakeUpload("work.md", b"# Work\nBuilt things.", "text/markdown"),
            "project_notes", None, "Work Log", None,
        )
    )

    assert session.committed, "session.commit() must be called on success"
    assert not session.rolled_back, "session.rollback() must NOT be called on success"
    # Document + at least one Chunk were added
    assert len(session.added) >= 2
    assert result.chunks_created == 1
    assert result.status == "indexed"


# ---------------------------------------------------------------------------
# Tests: empty / unchunkable content
# ---------------------------------------------------------------------------

def test_empty_conversion_result_raises_before_any_db_write(tmp_path: Path) -> None:
    """A document that converts to whitespace-only text is rejected before any DB write."""
    session = _FakeSession()
    service = _make_service(session, tmp_path)
    service.converter.convert_file_to_markdown.return_value = "   "

    with pytest.raises(IngestionError, match="empty text"):
        asyncio.run(
            service.index_upload(_FakeUpload("empty.txt", b"   "), None, None, None, None)
        )

    assert not session.committed
    assert list(tmp_path.iterdir()) == []


def test_no_chunks_produced_raises_before_any_db_write(tmp_path: Path) -> None:
    """A document that produces zero chunks is rejected before any DB write."""
    session = _FakeSession()
    service = _make_service(session, tmp_path)
    service.converter.convert_file_to_markdown.return_value = "Some content."
    service.chunker.chunk_markdown.return_value = []

    with pytest.raises(IngestionError, match="No indexable chunks"):
        asyncio.run(
            service.index_upload(_FakeUpload("sparse.md", b"Some content."), None, None, None, None)
        )

    assert not session.committed
    assert list(tmp_path.iterdir()) == []


# ---------------------------------------------------------------------------
# Tests: unsupported file type
# ---------------------------------------------------------------------------

def test_unsupported_extension_is_rejected_before_file_is_written(tmp_path: Path) -> None:
    """Extension validation fires before the file is written to disk, so the
    filesystem stays clean."""
    session = _FakeSession()
    service = _make_service(session, tmp_path)

    with pytest.raises(IngestionError, match="Unsupported file type"):
        asyncio.run(
            service.index_upload(_FakeUpload("malware.exe", b"\x4d\x5a\x90"), None, None, None, None)
        )

    assert list(tmp_path.iterdir()) == []
    assert not session.committed
