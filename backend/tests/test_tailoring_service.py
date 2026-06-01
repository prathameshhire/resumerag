from app.schemas.search import SearchResult
from app.services.bullet_validation_service import BulletValidationService
from app.services.placement_service import PlacementService
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


def test_non_strict_mode_keeps_draft_bullets_that_strict_mode_would_reject() -> None:
    service = TailoringService.__new__(TailoringService)
    service.validation_service = BulletValidationService()
    service.placement_service = PlacementService()
    result = SearchResult(
        chunk_id="11111111-1111-1111-1111-111111111111",
        document_id="22222222-2222-2222-2222-222222222222",
        source="resume.md",
        source_type="resume",
        category="fullstack",
        chunk_text="Improved cross-platform data flow with React components and Redux state management.",
        section_title=None,
        similarity_score=0.9,
        rank=1,
        metadata={},
    )
    raw_bullets = [
        {
            "bullet": "Improved cross-platform data flow with React components and Redux state management.",
            "matched_requirement": "Improve deduplication, reclamation, replication, and data storage performance.",
            "evidence_strength": "high",
            "source_numbers": [1],
        }
    ]
    hard_systems_jd = (
        "Software Engineer role working on data storage and management, data deduplication, "
        "reclamation, replication, low-level hardware systems, concurrency, algorithms, and C++."
    )

    strict_bullets, strict_rejected = service._map_bullets(raw_bullets, [result], True, hard_systems_jd)
    draft_bullets, draft_rejected = service._map_bullets(raw_bullets, [result], False, hard_systems_jd)

    assert strict_bullets == []
    assert len(strict_rejected) == 1
    assert len(draft_bullets) == 1
    assert draft_rejected == []


def test_map_skill_suggestions_requires_only_jd_mention() -> None:
    service = TailoringService.__new__(TailoringService)
    result = SearchResult(
        chunk_id="11111111-1111-1111-1111-111111111111",
        document_id="22222222-2222-2222-2222-222222222222",
        source="project.md",
        chunk_text="Built the interface with React, TypeScript, FastAPI, PostgreSQL, and Docker.",
        section_title=None,
        similarity_score=0.9,
        rank=1,
        metadata={},
    )
    raw_skills = [
        {
            "skill": "React",
            "category": "Frameworks & Libraries",
            "matched_requirement": "Experience with React",
            "evidence_strength": "high",
            "source_numbers": [1],
        },
        {
            "skill": "AWS",
            "category": "Tools",
            "matched_requirement": "Cloud infrastructure",
            "evidence_strength": "high",
            "source_numbers": [1],
        },
        {
            "skill": "PostgreSQL",
            "category": "Databases",
            "matched_requirement": "Relational databases",
            "evidence_strength": "high",
            "source_numbers": [],
        },
        {
            "skill": "Kubernetes",
            "category": "Tools",
            "matched_requirement": "Container orchestration",
            "evidence_strength": "high",
            "source_numbers": [],
        },
    ]

    skills = service._map_skill_suggestions(raw_skills, [result], "We need React, AWS, and PostgreSQL experience.")

    assert [skill.skill for skill in skills] == ["React", "AWS", "PostgreSQL"]
    assert skills[0].category == "Frameworks & Libraries"
    assert all(skill.evidence_strength == "jd" for skill in skills)
    assert skills[2].source_chunk_ids == []


def test_extract_jd_skill_suggestions_is_deterministic_fallback() -> None:
    service = TailoringService.__new__(TailoringService)
    jd = (
        "Experience with Python/Golang/Java/C++, containers/Docker, cloud infrastructure like AWS/GCP/Azure, "
        "Kafka, Elasticsearch, OpenSearch, Istio, Vector DB, React, Next.js, Tailwind CSS, and PostgreSQL."
    )

    skills = service._extract_jd_skill_suggestions(jd)

    skill_names = [skill.skill for skill in skills]
    assert "Python" in skill_names
    assert "Go" in skill_names
    assert "C++" in skill_names
    assert "Docker" in skill_names
    assert "AWS" in skill_names
    assert "GCP" in skill_names
    assert "Kafka" in skill_names
    assert "Elasticsearch" in skill_names
    assert "Vector DB" in skill_names
    assert "React" in skill_names
    assert all(skill.source_chunk_ids == [] for skill in skills)
