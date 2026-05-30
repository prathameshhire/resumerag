import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: uuid.UUID
    filename: str
    chunks_created: int
    status: str


class DocumentListItem(BaseModel):
    id: uuid.UUID
    filename: str
    source_type: str | None
    category: str | None
    chunks_count: int
    created_at: datetime
