from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.latex import router as latex_router
from app.api.search import router as search_router
from app.api.tailor import router as tailor_router
from app.config import get_settings


settings = get_settings()

app = FastAPI(
    title="ResumeRAG API",
    description="Local-first resume tailoring API.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Proxy entry-point (port 80 is the default, omitted in the Origin header)
        "http://localhost",
        "http://127.0.0.1",
        # Direct Vite dev-server access (local development outside Docker)
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        f"http://localhost:{settings.frontend_port}",
        f"http://127.0.0.1:{settings.frontend_port}",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(tailor_router)
app.include_router(latex_router)
