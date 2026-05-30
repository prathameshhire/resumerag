import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.document import DocumentListItem, DocumentUploadResponse
from app.services.ingestion_service import IngestionError, IngestionService


router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    source_type: str | None = Form(default=None),
    category: str | None = Form(default=None),
    title: str | None = Form(default=None),
    description: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> DocumentUploadResponse:
    service = IngestionService(db)

    try:
        return await service.index_upload(
            upload=file,
            source_type=source_type,
            category=category,
            title=title,
            description=description,
        )
    except IngestionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("", response_model=list[DocumentListItem])
def list_documents(db: Session = Depends(get_db)) -> list[DocumentListItem]:
    service = IngestionService(db)
    return service.list_documents()


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    service = IngestionService(db)

    try:
        service.delete_document(document_id)
    except IngestionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
