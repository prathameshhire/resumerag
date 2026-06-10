from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    frontend_port: int = 3000
    backend_port: int = 8000

    # Required — no default so a missing DATABASE_URL raises ValidationError at
    # startup instead of silently connecting to a stale hardcoded host.
    # Must use the psycopg3 driver scheme: postgresql+psycopg://...
    database_url: str

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384
    chunk_size_chars: int = 2200
    chunk_overlap_chars: int = 300
    retrieval_top_k: int = 8
    max_prompt_context_chars: int = 12000

    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "llama3.2"
    ollama_timeout_seconds: int = 120

    max_upload_mb: int = 20
    upload_dir: str = Field(default="/app/uploads")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("database_url")
    @classmethod
    def require_psycopg3_scheme(cls, v: str) -> str:
        # Reject the bare postgresql:// scheme so driver-mismatch errors surface
        # immediately at startup rather than as cryptic connection failures later.
        if v.startswith("postgresql://") and not v.startswith("postgresql+"):
            raise ValueError(
                "DATABASE_URL must use the psycopg3 driver scheme: "
                "postgresql+psycopg://user:pass@host/db  "
                "(not the bare postgresql:// scheme)"
            )
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
