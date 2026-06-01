from app.schemas.search import SearchResult
from app.services.placement_service import PlacementService


def _result(
    *,
    source: str = "resumerag-evidence-notes.md",
    source_type: str | None = "project_notes",
    category: str | None = "ml_infra",
    section_title: str | None = "Semantic Search",
    title: str | None = None,
) -> SearchResult:
    return SearchResult(
        chunk_id="11111111-1111-1111-1111-111111111111",
        document_id="22222222-2222-2222-2222-222222222222",
        source=source,
        source_type=source_type,
        category=category,
        document_title=title,
        chunk_text="Built semantic search with PostgreSQL and pgvector.",
        section_title=section_title,
        similarity_score=0.84,
        rank=1,
        metadata={},
    )


def test_places_project_notes_in_projects_section() -> None:
    placement = PlacementService().place_bullet([_result()])

    assert placement.section == "Projects"
    assert placement.entry == "ResumeRAG"
    assert "Semantic Search" in placement.rationale


def test_places_work_experience_in_experience_section() -> None:
    placement = PlacementService().place_bullet(
        [
            _result(
                source="Internship Summary.pdf",
                source_type="work_experience",
                category="fullstack",
                section_title="Olei Clinic",
            )
        ]
    )

    assert placement.section == "Experience"
    assert placement.entry == "Olei Clinic"


def test_places_resume_chunk_by_bullet_content() -> None:
    placement = PlacementService().place_bullet(
        [
            _result(
                source="Hire_Prathamesh_Resume.pdf",
                source_type="resume",
                category="fullstack",
                section_title=None,
            )
        ],
        "Built a FastAPI backend that fetches YouTube comments and analyzes sentiment.",
    )

    assert placement.section == "Projects"
    assert placement.entry == "SentimentScope"


def test_resume_chunk_does_not_place_work_bullet_in_project_from_noisy_chunk() -> None:
    source = _result(
        source="Hire_Prathamesh_Resume.pdf",
        source_type="resume",
        category="fullstack",
        section_title=None,
    )
    source.chunk_text = (
        "Experience: improved cross-platform data flow with Redux and Context API. "
        "Projects: SentimentScope used YouTube comments and sentiment analysis."
    )

    placement = PlacementService().place_bullet(
        [source],
        "Reduced redundant API calls by ~35% and improved UI responsiveness with memoization and custom hooks.",
    )

    assert placement.section == "Experience"
    assert placement.entry == "Olei HR / Olei Clinic"


def test_unplaced_without_sources() -> None:
    placement = PlacementService().place_bullet([])

    assert placement.section == "Review manually"
