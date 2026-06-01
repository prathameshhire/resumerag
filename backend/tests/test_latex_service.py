import shutil

from fastapi.testclient import TestClient

from app.api import latex as latex_api
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
    monkeypatch.setattr(latex_api.latex_service, "compile_pdf", lambda _: b"%PDF-1.5")

    response = client.post("/latex/pdf", json={"latex": "resume source", "filename": "Prathamesh Resume.tex"})

    assert response.status_code == 200
    assert response.content == b"%PDF-1.5"
    assert response.headers["content-type"] == "application/pdf"
    assert 'filename="Prathamesh-Resume.pdf"' in response.headers["content-disposition"]
