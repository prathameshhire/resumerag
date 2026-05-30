from app.services.embedding_service import EmbeddingError, EmbeddingService


class FakeModel:
    def __init__(self, vector: list[float]) -> None:
        self.vector = vector

    def encode(self, texts: list[str], **_: object) -> list[list[float]]:
        return [self.vector for _ in texts]


def test_embedding_service_returns_expected_dimension() -> None:
    service = EmbeddingService(model_name="fake", embedding_dim=3, model=FakeModel([0.1, 0.2, 0.3]))

    assert service.embed_text("FastAPI PostgreSQL") == [0.1, 0.2, 0.3]


def test_embedding_service_rejects_dimension_mismatch() -> None:
    service = EmbeddingService(model_name="fake", embedding_dim=3, model=FakeModel([0.1, 0.2]))

    try:
        service.embed_text("FastAPI PostgreSQL")
    except EmbeddingError as exc:
        assert "dimension mismatch" in str(exc)
    else:
        raise AssertionError("Expected EmbeddingError")
