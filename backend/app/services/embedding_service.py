from functools import lru_cache
from typing import Any

from app.config import get_settings


class EmbeddingError(Exception):
    pass


class EmbeddingService:
    def __init__(self, model_name: str | None = None, embedding_dim: int | None = None, model: Any | None = None) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self.embedding_dim = embedding_dim or settings.embedding_dim
        self._model = model

    def embed_text(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        cleaned_texts = [text.strip() for text in texts]
        if any(not text for text in cleaned_texts):
            raise EmbeddingError("Cannot embed empty text.")

        try:
            embeddings = self.model.encode(
                cleaned_texts,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
        except Exception as exc:
            raise EmbeddingError("Embedding model failed to encode text.") from exc

        vectors = embeddings.tolist() if hasattr(embeddings, "tolist") else embeddings
        normalized_vectors = [[float(value) for value in vector] for vector in vectors]

        for vector in normalized_vectors:
            if len(vector) != self.embedding_dim:
                raise EmbeddingError(
                    f"Embedding dimension mismatch: expected {self.embedding_dim}, got {len(vector)}."
                )

        return normalized_vectors

    @property
    def model(self) -> Any:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise EmbeddingError("sentence-transformers is not installed in the backend environment.") from exc

            try:
                self._model = SentenceTransformer(self.model_name)
            except Exception as exc:
                raise EmbeddingError(f"Could not load embedding model: {self.model_name}.") from exc

        return self._model


@lru_cache
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
