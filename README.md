# ResumeRAG

ResumeRAG is a privacy-first local RAG application that generates tailored resume bullet points from your own work experience context. It runs locally with React, FastAPI, PostgreSQL/pgvector, sentence-transformers, MarkItDown, and Ollama.

This repository is currently at Phase 1: the runnable local stack skeleton.

## Prerequisites

- Docker Desktop
- Git
- Ollama, for later phases

Recommended local model for later phases:

```bash
ollama pull llama3.2
```

## Setup

```bash
cp .env.example .env
docker compose up --build
```

## Open App

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Phase 1 Includes

- Docker Compose services for frontend, backend, and PostgreSQL/pgvector
- FastAPI app with `GET /health`
- React/Vite dashboard shell
- Alembic setup with initial pgvector schema migration
- Baseline tables for documents, chunks, tailoring queries, and retrieval results

## Troubleshooting

### Docker cannot reach Ollama later

On Mac and Windows, use:

```env
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

On Linux, this Compose file already includes:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

### Database errors

Reset local database data:

```bash
docker compose down -v
docker compose up --build
```

### Slow generation in later phases

- Use a smaller Ollama model.
- Reduce `RETRIEVAL_TOP_K`.
- Reduce `CHUNK_SIZE_CHARS`.
- Close other heavy apps.

## Privacy Note

ResumeRAG is intended as a local development app for personal career data. It is not hardened for public multi-user deployment.
