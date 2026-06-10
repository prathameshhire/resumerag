import re
import uuid
from pathlib import Path

from fastapi import UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.chunk import Chunk
from app.models.document import Document
from app.schemas.document import DocumentListItem, DocumentUploadResponse
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingError, get_embedding_service
from app.services.markitdown_service import ALLOWED_EXTENSIONS, ConversionError, MarkItDownService


class IngestionError(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class IngestionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.converter = MarkItDownService()
        self.embedding_service = get_embedding_service()
        self.chunker = ChunkingService(
            chunk_size_chars=self.settings.chunk_size_chars,
            chunk_overlap_chars=self.settings.chunk_overlap_chars,
        )

    async def index_upload(
        self,
        upload: UploadFile,
        source_type: str | None,
        category: str | None,
        title: str | None,
        description: str | None,
    ) -> DocumentUploadResponse:
        original_filename = upload.filename or ""
        extension = Path(original_filename).suffix.lower()

        if not original_filename:
            raise IngestionError("Uploaded file must include a filename.")
        if extension not in ALLOWED_EXTENSIONS:
            allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise IngestionError(f"Unsupported file type. Supported types: {allowed}.")

        upload_dir = Path(self.settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        stored_filename = f"{uuid.uuid4()}_{self._safe_filename(original_filename)}"
        file_path = upload_dir / stored_filename

        try:
            file_size = await self._save_upload(upload, file_path)
            markdown_text = self.converter.convert_file_to_markdown(file_path).strip()

            if not markdown_text:
                raise IngestionError("Document conversion produced empty text.")

            chunks = self.chunker.chunk_markdown(markdown_text)
            if not chunks:
                raise IngestionError("No indexable chunks were created from the document.")
            embeddings = self.embedding_service.embed_texts([chunk.chunk_text for chunk in chunks])

            document = Document(
                filename=stored_filename,
                original_filename=original_filename,
                content_type=upload.content_type,
                source_type=self._clean_optional(source_type),
                category=self._clean_optional(category),
                title=self._clean_optional(title),
                description=self._clean_optional(description),
                file_size_bytes=file_size,
                markdown_text=markdown_text,
            )
            self.db.add(document)
            # No explicit flush needed: Document.id uses default=uuid.uuid4 so the
            # UUID is available in Python immediately, without a round-trip to the DB.
            # SQLAlchemy's commit() flushes parent rows before child rows automatically,
            # respecting the FK constraint.  A single commit() at the end keeps the
            # document row and all its chunks in the same transaction — either both
            # land or neither does.

            for index, chunk in enumerate(chunks):
                self.db.add(
                    Chunk(
                        document_id=document.id,
                        chunk_index=index,
                        chunk_text=chunk.chunk_text,
                        section_title=chunk.section_title,
                        token_estimate=chunk.token_estimate,
                        metadata_=chunk.metadata,
                        embedding=embeddings[index],
                    )
                )

            self.db.commit()
            self.db.refresh(document)
        except IngestionError:
            self.db.rollback()
            file_path.unlink(missing_ok=True)
            raise
        except ConversionError as exc:
            self.db.rollback()
            file_path.unlink(missing_ok=True)
            raise IngestionError(str(exc)) from exc
        except EmbeddingError as exc:
            self.db.rollback()
            file_path.unlink(missing_ok=True)
            raise IngestionError(str(exc), status.HTTP_500_INTERNAL_SERVER_ERROR) from exc
        except Exception as exc:
            self.db.rollback()
            file_path.unlink(missing_ok=True)
            raise IngestionError("Document indexing failed.", status.HTTP_500_INTERNAL_SERVER_ERROR) from exc

        return DocumentUploadResponse(
            document_id=document.id,
            filename=document.original_filename,
            chunks_created=len(chunks),
            status="indexed",
        )

    def list_documents(self) -> list[DocumentListItem]:
        stmt = (
            select(Document, func.count(Chunk.id).label("chunks_count"))
            .outerjoin(Chunk, Chunk.document_id == Document.id)
            .group_by(Document.id)
            .order_by(Document.created_at.desc())
        )

        rows = self.db.execute(stmt).all()
        return [
            DocumentListItem(
                id=document.id,
                filename=document.original_filename,
                source_type=document.source_type,
                category=document.category,
                chunks_count=chunks_count,
                created_at=document.created_at,
            )
            for document, chunks_count in rows
        ]

    def delete_document(self, document_id: uuid.UUID) -> None:
        document = self.db.get(Document, document_id)
        if document is None:
            raise IngestionError("Document not found.", status.HTTP_404_NOT_FOUND)

        file_path = Path(self.settings.upload_dir) / document.filename
        self.db.delete(document)
        self.db.commit()
        file_path.unlink(missing_ok=True)

    async def _save_upload(self, upload: UploadFile, file_path: Path) -> int:
        max_bytes = self.settings.max_upload_mb * 1024 * 1024
        total = 0

        with file_path.open("wb") as target:
            while chunk := await upload.read(1024 * 1024):
                total += len(chunk)
                if total > max_bytes:
                    raise IngestionError(f"File is too large. Maximum upload size is {self.settings.max_upload_mb} MB.")
                target.write(chunk)

        return total

    def _safe_filename(self, filename: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(filename).name).strip(".-")
        return safe or "upload"

    def _clean_optional(self, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None
