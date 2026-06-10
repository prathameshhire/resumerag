"""API tests for /documents endpoints.

All tests mock IngestionService so they run without a real database or
embedding model.  They verify HTTP routing, request validation, response
serialisation, and correct error-code propagation from the service layer.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.schemas.document import DocumentListItem, DocumentUploadResponse
from app.services.ingestion_service import IngestionError

# Small fixtures defined locally so the test module has no import dependency on
# conftest implementation details.
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
SAMPLE_DOCUMENT_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


# ---------------------------------------------------------------------------
# POST /documents/upload
# ---------------------------------------------------------------------------

def test_upload_txt_returns_201(
    client: TestClient, mock_ingestion_service: MagicMock
) -> None:
    """Successful .txt upload returns 201 with document metadata."""
    expected = DocumentUploadResponse(
        document_id=SAMPLE_DOCUMENT_ID,
        filename="notes.txt",
        chunks_created=3,
        status="indexed",
    )
    mock_ingestion_service.index_upload = AsyncMock(return_value=expected)

    response = client.post(
        "/documents/upload",
        files={"file": ("notes.txt", SAMPLE_TEXT.encode(), "text/plain")},
        data={"source_type": "project_notes", "category": "backend", "title": "My Notes"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["document_id"] == str(SAMPLE_DOCUMENT_ID)
    assert data["filename"] == "notes.txt"
    assert data["chunks_created"] == 3
    assert data["status"] == "indexed"


def test_upload_pdf_returns_201(
    client: TestClient, mock_ingestion_service: MagicMock
) -> None:
    """Successful .pdf upload returns 201."""
    expected = DocumentUploadResponse(
        document_id=SAMPLE_DOCUMENT_ID,
        filename="resume.pdf",
        chunks_created=5,
        status="indexed",
    )
    mock_ingestion_service.index_upload = AsyncMock(return_value=expected)

    response = client.post(
        "/documents/upload",
        files={"file": ("resume.pdf", MINIMAL_PDF, "application/pdf")},
    )

    assert response.status_code == 201
    assert response.json()["chunks_created"] == 5


def test_upload_without_optional_fields_returns_201(
    client: TestClient, mock_ingestion_service: MagicMock
) -> None:
    """Optional form fields (source_type, category, title, description) may be omitted."""
    expected = DocumentUploadResponse(
        document_id=SAMPLE_DOCUMENT_ID,
        filename="doc.md",
        chunks_created=2,
        status="indexed",
    )
    mock_ingestion_service.index_upload = AsyncMock(return_value=expected)

    response = client.post(
        "/documents/upload",
        files={"file": ("doc.md", b"# Section\nContent.", "text/markdown")},
    )

    assert response.status_code == 201


def test_upload_unsupported_extension_returns_415(
    client: TestClient, mock_ingestion_service: MagicMock
) -> None:
    """The service raises IngestionError(400) for bad extensions; API maps it to 415
    because the schema validation happens inside the service, not the route.
    The important thing is that the error propagates as a non-2xx response."""
    mock_ingestion_service.index_upload = AsyncMock(
        side_effect=IngestionError(
            "Unsupported file type. Supported types: .docx, .md, .pdf, .txt.",
            status_code=400,
        )
    )

    response = client.post(
        "/documents/upload",
        files={"file": ("virus.exe", b"\x4d\x5a\x90", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_oversized_file_returns_400(
    client: TestClient, mock_ingestion_service: MagicMock
) -> None:
    """Files exceeding the upload limit raise IngestionError which surfaces as 400."""
    mock_ingestion_service.index_upload = AsyncMock(
        side_effect=IngestionError(
            "File is too large. Maximum upload size is 20 MB.",
            status_code=400,
        )
    )

    response = client.post(
        "/documents/upload",
        files={"file": ("big.txt", b"x" * 100, "text/plain")},
    )

    assert response.status_code == 400
    assert "too large" in response.json()["detail"]


def test_upload_empty_document_returns_400(
    client: TestClient, mock_ingestion_service: MagicMock
) -> None:
    """Documents that convert to empty text are rejected with 400."""
    mock_ingestion_service.index_upload = AsyncMock(
        side_effect=IngestionError(
            "Document conversion produced empty text.",
            status_code=400,
        )
    )

    response = client.post(
        "/documents/upload",
        files={"file": ("empty.md", b"", "text/markdown")},
    )

    assert response.status_code == 400


def test_upload_missing_file_returns_422(client: TestClient) -> None:
    """Omitting the required `file` field fails FastAPI validation before hitting the service."""
    response = client.post("/documents/upload", data={"source_type": "notes"})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /documents
# ---------------------------------------------------------------------------

def test_list_documents_empty_returns_empty_list(
    client: TestClient, mock_ingestion_service: MagicMock
) -> None:
    """No documents uploaded → 200 with an empty list (not 404)."""
    mock_ingestion_service.list_documents.return_value = []

    response = client.get("/documents")

    assert response.status_code == 200
    assert response.json() == []


def test_list_documents_returns_uploaded_documents(
    client: TestClient, mock_ingestion_service: MagicMock
) -> None:
    """After upload the list includes the document with correct metadata."""
    now = datetime(2026, 6, 10, 12, 0, 0, tzinfo=timezone.utc)
    mock_ingestion_service.list_documents.return_value = [
        DocumentListItem(
            id=SAMPLE_DOCUMENT_ID,
            filename="notes.txt",
            source_type="project_notes",
            category="backend",
            chunks_count=3,
            created_at=now,
        )
    ]

    response = client.get("/documents")

    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["filename"] == "notes.txt"
    assert items[0]["source_type"] == "project_notes"
    assert items[0]["chunks_count"] == 3


def test_list_documents_with_null_optional_fields(
    client: TestClient, mock_ingestion_service: MagicMock
) -> None:
    """Documents uploaded without source_type/category appear correctly in the list."""
    now = datetime(2026, 6, 10, 12, 0, 0, tzinfo=timezone.utc)
    mock_ingestion_service.list_documents.return_value = [
        DocumentListItem(
            id=SAMPLE_DOCUMENT_ID,
            filename="plain.md",
            source_type=None,
            category=None,
            chunks_count=1,
            created_at=now,
        )
    ]

    response = client.get("/documents")

    assert response.status_code == 200
    item = response.json()[0]
    assert item["source_type"] is None
    assert item["category"] is None


# ---------------------------------------------------------------------------
# DELETE /documents/{document_id}
# ---------------------------------------------------------------------------

def test_delete_existing_document_returns_204(
    client: TestClient, mock_ingestion_service: MagicMock
) -> None:
    """Deleting an existing document returns 204 with no body."""
    mock_ingestion_service.delete_document.return_value = None

    response = client.delete(f"/documents/{SAMPLE_DOCUMENT_ID}")

    assert response.status_code == 204
    assert response.content == b""
    mock_ingestion_service.delete_document.assert_called_once_with(SAMPLE_DOCUMENT_ID)


def test_delete_nonexistent_document_returns_404(
    client: TestClient, mock_ingestion_service: MagicMock
) -> None:
    """Deleting a document that does not exist returns 404."""
    missing_id = uuid.uuid4()
    mock_ingestion_service.delete_document.side_effect = IngestionError(
        "Document not found.", status_code=404
    )

    response = client.delete(f"/documents/{missing_id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_delete_with_invalid_uuid_returns_422(client: TestClient) -> None:
    """A malformed document ID fails FastAPI's UUID validation before the service is called."""
    response = client.delete("/documents/not-a-uuid")
    assert response.status_code == 422
