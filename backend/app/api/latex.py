from fastapi import APIRouter, HTTPException, Response

from app.schemas.latex import LatexPdfRequest
from app.services.latex_service import LatexExportError, LatexService


router = APIRouter(prefix="/latex", tags=["latex"])
latex_service = LatexService()


@router.post("/pdf")
def export_latex_pdf(request: LatexPdfRequest) -> Response:
    try:
        pdf_bytes = latex_service.compile_pdf(request.latex)
    except LatexExportError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    filename = LatexService.safe_pdf_filename(request.filename)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
