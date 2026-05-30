from app.schemas.search import SearchResult
from app.services.tailoring_service import TailoringService


def test_parse_llm_json_from_fenced_block() -> None:
    service = TailoringService.__new__(TailoringService)

    parsed = service._parse_llm_json('```json\n{"bullets": [], "warnings": ["Not enough evidence."]}\n```')

    assert parsed["warnings"] == ["Not enough evidence."]


def test_source_numbers_map_to_chunk_ids() -> None:
    service = TailoringService.__new__(TailoringService)
    result = SearchResult(
        chunk_id="11111111-1111-1111-1111-111111111111",
        document_id="22222222-2222-2222-2222-222222222222",
        source="resume.md",
        chunk_text="Built APIs.",
        section_title=None,
        similarity_score=0.9,
        rank=1,
        metadata={},
    )

    chunk_ids = service._source_numbers_to_chunk_ids([1, 3, "bad"], [result])

    assert [str(chunk_id) for chunk_id in chunk_ids] == ["11111111-1111-1111-1111-111111111111"]
