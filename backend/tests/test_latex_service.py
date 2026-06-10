import shutil

from fastapi.testclient import TestClient

from app.api.latex import get_latex_service
from app.main import app
from app.services.latex_service import LatexExportError, LatexService


client = TestClient(app)


def test_safe_pdf_filename_normalizes_tex_name() -> None:
    assert LatexService.safe_pdf_filename("Prathamesh Resume.tex") == "Prathamesh-Resume.pdf"


def test_safe_pdf_filename_uses_pdf_extension() -> None:
    assert LatexService.safe_pdf_filename("../resume final") == "resume-final.pdf"


def test_compile_pdf_reports_missing_compiler(monkeypatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda _: None)
    service = LatexService()

    try:
        service.compile_pdf(r"\documentclass{article}\begin{document}Hello\end{document}")
    except LatexExportError as exc:
        assert exc.status_code == 503
        assert "pdflatex" in exc.message
    else:
        raise AssertionError("Expected LatexExportError")


def test_export_pdf_endpoint_returns_pdf(monkeypatch) -> None:
    # Patch the Depends factory so every request in this test gets a mock service.
    # Patching at the factory level (rather than on a module-level singleton) is
    # the correct pattern after the thread-safety refactor in api/latex.py.
    mock_service = LatexService.__new__(LatexService)
    mock_service.compile_pdf = lambda latex: b"%PDF-1.5"  # type: ignore[method-assign]

    app.dependency_overrides[get_latex_service] = lambda: mock_service
    try:
        response = client.post(
            "/latex/pdf",
            json={"latex": "resume source", "filename": "Prathamesh Resume.tex"},
        )
    finally:
        app.dependency_overrides.pop(get_latex_service, None)

    assert response.status_code == 200
    assert response.content == b"%PDF-1.5"
    assert response.headers["content-type"] == "application/pdf"
    assert 'filename="Prathamesh-Resume.pdf"' in response.headers["content-disposition"]
