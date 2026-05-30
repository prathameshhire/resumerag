from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.search import SearchRequest, SearchResponse
from app.services.retrieval_service import RetrievalError, RetrievalService


router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search_documents(request: SearchRequest, db: Session = Depends(get_db)) -> SearchResponse:
    service = RetrievalService(db)

    try:
        results = service.search(request.query, request.top_k, request.filters)
    except RetrievalError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return SearchResponse(query=request.query, results=results)
