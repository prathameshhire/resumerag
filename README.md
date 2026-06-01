# ResumeRAG

ResumeRAG is a privacy-first local RAG application that generates tailored resume bullet points from your own work experience context. It runs locally with React, FastAPI, PostgreSQL/pgvector, sentence-transformers, MarkItDown, and Ollama.

The app is currently at Phase 6 polish: document upload, Markdown conversion, chunking, local embeddings, pgvector search, Ollama generation, evidence-backed bullets, sample data, and clearer demo instructions.

## Prerequisites

- Docker Desktop
- Git
- Ollama
- 16 GB RAM recommended for the full local stack

Recommended model:

```bash
ollama pull llama3.2
```

The default `.env.example` value is:

```env
OLLAMA_MODEL=llama3.2
```

Specific Ollama tags such as `llama3.2:3b` can be used by changing `OLLAMA_MODEL`.

## Setup

```bash
cp .env.example .env
docker compose up --build
```

Open:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health/full

## Quick Demo

1. Start Ollama and Docker Compose.
2. Open http://localhost:3000.
3. Upload one or more synthetic files from `sample_data/experience`.
4. Paste a job description from `sample_data/jobs`.
5. Generate tailored bullets.
6. Review each bullet with its matched requirement and retrieved source evidence.
7. Paste your resume `.tex` file into the LaTeX workspace, apply or reject suggested bullet patches, then export either `.tex` or a compiled PDF.

Suggested first demo:

- Upload `sample_data/experience/backend-projects.md`
- Upload `sample_data/experience/ml-infra-project.md`
- Paste `sample_data/jobs/backend-engineer-jd.txt`

You can also upload sample data from PowerShell:

```powershell
curl.exe -X POST http://localhost:8000/documents/upload `
  -F "file=@sample_data/experience/backend-projects.md;type=text/markdown" `
  -F "source_type=project_notes" `
  -F "category=backend" `
  -F "title=Backend sample"
```

## Current Features

- Docker Compose services for frontend, backend, and PostgreSQL/pgvector
- FastAPI health checks
- React/Vite dashboard with upload, tailoring, and search panels
- Alembic setup with pgvector schema migration
- Document upload for `.pdf`, `.docx`, `.md`, and `.txt`
- MarkItDown conversion to Markdown
- Heading-aware Markdown chunking
- Local embeddings with `sentence-transformers/all-MiniLM-L6-v2`
- Chunk and vector persistence in PostgreSQL/pgvector
- Semantic chunk search
- Ollama model availability checks
- Tailored bullet generation with retrieved source evidence
- LaTeX resume workspace with patch review and PDF export through `pdflatex`
- Synthetic sample experience and job descriptions

## API Endpoints

Documents:

- `POST /documents/upload`
- `GET /documents`
- `DELETE /documents/{document_id}`

Search:

- `POST /search`

Tailoring:

- `POST /tailor/test-ollama`
- `POST /tailor/bullets`

LaTeX:

- `POST /latex/pdf`

Health:

- `GET /health`
- `GET /health/full`

## Screenshots

Screenshot placeholders for the README:

- Dashboard and health checklist
- Upload and indexed documents
- Tailored bullets with evidence
- Semantic search results

## Development

```bash
docker compose up --build
docker compose exec backend pytest
docker compose exec frontend npm run test
```

Stop the stack while preserving local database data:

```bash
docker compose down
```

Reset local database and uploaded files:

```bash
docker compose down -v
docker compose up --build
```

## Troubleshooting

### Ollama not connected

Make sure Ollama is running, then check installed models:

```bash
ollama list
```

Pull the default model if needed:

```bash
ollama pull llama3.2
```

### Docker cannot reach Ollama

On Mac and Windows, use:

```env
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

On Linux, this Compose file already includes:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

### Slow generation

- Use a small model such as `llama3.2`.
- Reduce `RETRIEVAL_TOP_K`.
- Reduce `CHUNK_SIZE_CHARS`.
- Close other heavy apps.
- Expect the first embedding request to take longer while the model loads.

### PDF export fails

PDF export uses `pdflatex` inside the backend container. If the UI says `pdflatex` is missing, rebuild the backend image:

```bash
docker compose up -d --build backend
```

### Docker memory looks high on Windows

Docker Desktop runs Linux containers through WSL. Task Manager often shows that memory under `Vmmem`. Memory can drop after containers settle, and `docker compose down` stops this app while preserving the named database volume.

### Database errors

Reset local data:

```bash
docker compose down -v
docker compose up --build
```

## Privacy Note

ResumeRAG is intended as a local development app for personal career data. It is not hardened for public multi-user deployment. Documents, job descriptions, embeddings, and Ollama calls stay local for the MVP.
