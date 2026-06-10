from fastapi import APIRouter, Depends, HTTPException, Response

from app.schemas.latex import LatexPdfRequest
from app.services.latex_service import LatexExportError, LatexService


router = APIRouter(prefix="/latex", tags=["latex"])


def get_latex_service() -> LatexService:
    # Per-request factory injected via FastAPI Depends.
    # LatexService is stateless after construction (all compilation state lives
    # inside compile_pdf's tempfile.TemporaryDirectory), so instantiating once
    # per request is safe and avoids any risk of shared mutable state across
    # concurrent compilations.
    return LatexService()


@router.post("/pdf")
def export_latex_pdf(
    request: LatexPdfRequest,
    service: LatexService = Depends(get_latex_service),
) -> Response:
    try:
        pdf_bytes = service.compile_pdf(request.latex)
    except LatexExportError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    filename = LatexService.safe_pdf_filename(request.filename)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
