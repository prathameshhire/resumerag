import importlib.util

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas.health import ComponentHealth, EmbeddingModelHealth, FullHealthResponse, HealthResponse, OllamaHealth
from app.services.ollama_service import OllamaService


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", backend=True)


@router.get("/health/full", response_model=FullHealthResponse)
def full_health(db: Session = Depends(get_db)) -> FullHealthResponse:
    settings = get_settings()

    database_health = _check_database(db)
    pgvector_health = _check_pgvector(db)
    embedding_health = _check_embedding_model(settings.embedding_model, settings.embedding_dim)

    ollama_service = OllamaService(
        base_url=settings.ollama_base_url,
        model_name=settings.ollama_model,
        timeout_seconds=settings.ollama_timeout_seconds,
    )
    ollama_ok, model_available, ollama_message = ollama_service.health()

    return FullHealthResponse(
        backend=ComponentHealth(ok=True),
        database=database_health,
        pgvector=pgvector_health,
        embedding_model=embedding_health,
        ollama=OllamaHealth(
            ok=ollama_ok,
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            model_available=model_available,
            message=ollama_message,
        ),
    )


def _check_database(db: Session) -> ComponentHealth:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        return ComponentHealth(ok=False, message=f"Database check failed: {exc}")

    return ComponentHealth(ok=True)


def _check_pgvector(db: Session) -> ComponentHealth:
    try:
        result = db.execute(text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')"))
        has_vector = bool(result.scalar())
    except Exception as exc:
        return ComponentHealth(ok=False, message=f"pgvector check failed: {exc}")

    if not has_vector:
        return ComponentHealth(ok=False, message="pgvector extension is not installed.")

    return ComponentHealth(ok=True)


def _check_embedding_model(model_name: str, dimension: int) -> EmbeddingModelHealth:
    has_package = importlib.util.find_spec("sentence_transformers") is not None
    if not has_package:
        return EmbeddingModelHealth(
            ok=False,
            model=model_name,
            dimension=dimension,
            message="sentence-transformers is not installed.",
        )

    return EmbeddingModelHealth(ok=True, model=model_name, dimension=dimension)
