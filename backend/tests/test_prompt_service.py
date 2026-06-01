from app.schemas.search import SearchResult
from app.schemas.tailor import TailorBulletsRequest
from app.services.prompt_service import PromptService


def test_prompt_service_formats_source_numbers() -> None:
    service = PromptService()
    result = SearchResult(
        chunk_id="11111111-1111-1111-1111-111111111111",
        document_id="22222222-2222-2222-2222-222222222222",
        source="backend-projects.md",
        chunk_text="Built FastAPI services with PostgreSQL.",
        section_title="Appointment API",
        similarity_score=0.82,
        rank=1,
        metadata={},
    )

    messages = service.build_messages(
        TailorBulletsRequest(job_description="Backend role", target_role="Backend Engineer"),
        [result],
    )

    assert messages[0]["role"] == "system"
    assert "[Source 1]" in messages[1]["content"]
    assert "backend-projects.md" in messages[1]["content"]
    assert "skill_suggestions" in messages[1]["content"]
    assert "explicitly named in the job description" in messages[1]["content"]
    assert "does not need to appear in the retrieved user context" in messages[1]["content"]
