from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    backend: bool


class ComponentHealth(BaseModel):
    ok: bool
    message: str | None = None


class EmbeddingModelHealth(ComponentHealth):
    model: str
    dimension: int


class OllamaHealth(ComponentHealth):
    base_url: str
    model: str
    model_available: bool


class FullHealthResponse(BaseModel):
    backend: ComponentHealth
    database: ComponentHealth
    pgvector: ComponentHealth
    embedding_model: EmbeddingModelHealth
    ollama: OllamaHealth
