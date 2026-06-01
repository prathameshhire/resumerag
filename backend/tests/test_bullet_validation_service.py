from app.schemas.search import SearchResult
from app.schemas.tailor import ResumePlacement, TailoredBullet
from app.services.bullet_validation_service import BulletValidationService


def _placement() -> ResumePlacement:
    return ResumePlacement(section="Projects", entry="Project", rationale="Test placement.")


def _search_result(text: str) -> SearchResult:
    return SearchResult(
        chunk_id="11111111-1111-1111-1111-111111111111",
        document_id="22222222-2222-2222-2222-222222222222",
        source="project-notes.md",
        chunk_text=text,
        section_title="Project",
        similarity_score=0.8,
        rank=1,
        metadata={},
    )


def _resume_result(text: str) -> SearchResult:
    result = _search_result(text)
    result.source = "Hire_Prathamesh_Resume.pdf"
    result.source_type = "resume"
    return result


def test_validator_accepts_grounded_bullet() -> None:
    source = _search_result("Built FastAPI services with PostgreSQL, structured error handling, and Docker Compose support.")
    bullet = TailoredBullet(
        bullet="Built FastAPI services with PostgreSQL and structured error handling.",
        matched_requirement="Backend APIs and databases",
        evidence_strength="high",
        source_chunk_ids=[source.chunk_id],
        placement=_placement(),
        notes=None,
    )

    result = BulletValidationService().validate(
        raw_bullet={"bullet": bullet.bullet, "source_numbers": [1]},
        bullet=bullet,
        retrieved_context=[source],
        strict_mode=True,
    )

    assert result.bullet == bullet
    assert result.rejected_bullet is None


def test_validator_rejects_unsupported_risky_term() -> None:
    source = _search_result("Built FastAPI services with PostgreSQL and Docker Compose support.")
    bullet = TailoredBullet(
        bullet="Built cloud-native microservices with high availability.",
        matched_requirement="Distributed systems",
        evidence_strength="high",
        source_chunk_ids=[source.chunk_id],
        placement=_placement(),
        notes=None,
    )

    result = BulletValidationService().validate(
        raw_bullet={"bullet": bullet.bullet, "source_numbers": [1]},
        bullet=bullet,
        retrieved_context=[source],
        strict_mode=True,
    )

    assert result.bullet is None
    assert result.rejected_bullet is not None
    assert any("Unsupported risky term" in reason for reason in result.reasons)


def test_validator_rejects_placeholder_evidence_quote() -> None:
    source = _search_result("Configured Vercel deployment for the React/Vite frontend.")
    bullet = TailoredBullet(
        bullet="Configured Vercel deployment for the React/Vite frontend.",
        matched_requirement="Deployment",
        evidence_strength="medium",
        source_chunk_ids=[source.chunk_id],
        placement=_placement(),
        notes=None,
    )

    result = BulletValidationService().validate(
        raw_bullet={"bullet": bullet.bullet, "source_numbers": [1], "evidence_quotes": ["exact substring copied from source"]},
        bullet=bullet,
        retrieved_context=[source],
        strict_mode=True,
    )

    assert result.bullet is None
    assert result.rejected_bullet is not None
    assert any("Evidence quote could not be verified" in reason for reason in result.reasons)


def test_validator_rejects_transferable_bullet_for_hard_systems_role() -> None:
    job_description = (
        "Software Engineer role working on data storage and management, data deduplication, "
        "reclamation, replication, low-level hardware systems, concurrency, algorithms, and C++."
    )
    source = _search_result(
        "Improved cross-platform data flow by building reusable React components and managing shared state."
    )
    bullet = TailoredBullet(
        bullet="Improved cross-platform data flow by building reusable React components and managing shared state.",
        matched_requirement="Improve deduplication, reclamation, replication, and data storage performance.",
        evidence_strength="high",
        source_chunk_ids=[source.chunk_id],
        placement=_placement(),
        notes=None,
    )

    result = BulletValidationService().validate(
        raw_bullet={"bullet": bullet.bullet, "source_numbers": [1]},
        bullet=bullet,
        retrieved_context=[source],
        strict_mode=True,
        job_description=job_description,
    )

    assert result.bullet is None
    assert result.rejected_bullet is not None
    assert any("role-critical systems/storage/C++" in reason for reason in result.reasons)


def test_validator_rejects_verbatim_existing_resume_bullet() -> None:
    source = _resume_result(
        "Experience\n"
        "- Reduced redundant API calls by ~35% and improved UI responsiveness by implementing memoization, "
        "React Hook Form, and custom hooks across React/TypeScript components.\n"
        "- Improved cross-platform data flow by building reusable React components."
    )
    bullet = TailoredBullet(
        bullet=(
            "Reduced redundant API calls by ~35% and improved UI responsiveness by implementing memoization, "
            "React Hook Form, and custom hooks across React/TypeScript components."
        ),
        matched_requirement="Frontend performance",
        evidence_strength="high",
        source_chunk_ids=[source.chunk_id],
        placement=_placement(),
        notes=None,
    )

    result = BulletValidationService().validate(
        raw_bullet={"bullet": bullet.bullet, "source_numbers": [1]},
        bullet=bullet,
        retrieved_context=[source],
        strict_mode=True,
        job_description="Improve frontend performance and state management.",
    )

    assert result.bullet is None
    assert result.rejected_bullet is not None
    assert any("already present" in reason or "too close" in reason for reason in result.reasons)


def test_validator_accepts_same_bullet_for_matching_frontend_role() -> None:
    job_description = "Build responsive React interfaces with component architecture and state management."
    source = _search_result(
        "Improved cross-platform data flow by building reusable React components and managing shared state."
    )
    bullet = TailoredBullet(
        bullet="Improved cross-platform data flow by building reusable React components and managing shared state.",
        matched_requirement="React component architecture and state management",
        evidence_strength="high",
        source_chunk_ids=[source.chunk_id],
        placement=_placement(),
        notes=None,
    )

    result = BulletValidationService().validate(
        raw_bullet={"bullet": bullet.bullet, "source_numbers": [1]},
        bullet=bullet,
        retrieved_context=[source],
        strict_mode=True,
        job_description=job_description,
    )

    assert result.bullet == bullet
    assert result.rejected_bullet is None
