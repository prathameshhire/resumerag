from app.services.retrieval_service import RetrievalService


def test_vector_literal_uses_pgvector_format() -> None:
    service = RetrievalService.__new__(RetrievalService)

    assert service._vector_literal([0.1, -0.2, 0.0]) == "[0.1,-0.2,0.0]"
