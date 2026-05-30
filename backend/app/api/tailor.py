from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas.tailor import OllamaTestRequest, OllamaTestResponse, TailorBulletsRequest, TailorBulletsResponse
from app.services.ollama_service import OllamaError, OllamaService
from app.services.tailoring_service import TailoringError, TailoringService


router = APIRouter(prefix="/tailor", tags=["tailor"])


@router.post("/test-ollama", response_model=OllamaTestResponse)
def test_ollama(request: OllamaTestRequest) -> OllamaTestResponse:
    settings = get_settings()
    service = OllamaService()

    try:
        response = service.chat(
            [
                {"role": "system", "content": "You are a concise local connectivity test for ResumeRAG."},
                {"role": "user", "content": request.message},
            ]
        )
    except OllamaError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return OllamaTestResponse(model=settings.ollama_model, response=response)


@router.post("/bullets", response_model=TailorBulletsResponse)
def tailor_bullets(request: TailorBulletsRequest, db: Session = Depends(get_db)) -> TailorBulletsResponse:
    service = TailoringService(db)

    try:
        return service.generate_bullets(request)
    except TailoringError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
