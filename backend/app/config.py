from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    frontend_port: int = 3000
    backend_port: int = 8000

    database_url: str = "postgresql+psycopg://resumerag:resumerag@db:5432/resumerag"

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
