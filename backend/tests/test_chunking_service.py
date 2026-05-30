from app.services.chunking_service import ChunkingService


def test_chunking_preserves_section_titles() -> None:
    service = ChunkingService(chunk_size_chars=120, chunk_overlap_chars=20)

    chunks = service.chunk_markdown(
        "# Backend Projects\n\n"
        "Built FastAPI services with PostgreSQL.\n\n"
        "## Authentication Refactor\n\n"
        "Replaced login flow with a custom endpoint and JWT storage."
    )

    assert [chunk.section_title for chunk in chunks] == ["Backend Projects", "Authentication Refactor"]
    assert chunks[0].chunk_text.startswith("# Backend Projects")


def test_chunking_splits_long_sections_with_overlap() -> None:
    service = ChunkingService(chunk_size_chars=50, chunk_overlap_chars=10)
    text = "# Data Project\n\n" + "A" * 90

    chunks = service.chunk_markdown(text)

    assert len(chunks) >= 2
    assert chunks[0].section_title == "Data Project"
    assert chunks[0].chunk_text.startswith("# Data Project")
    assert not any(chunk.chunk_text == "# Data Project" for chunk in chunks)
