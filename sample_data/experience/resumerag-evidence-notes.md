# ResumeRAG - Project Evidence Notes

## Overview

ResumeRAG is a local-first resume tailoring RAG application that generates tailored resume bullets from uploaded work-experience context and a pasted job description.

The app is designed to keep private resume documents, project notes, embeddings, job descriptions, and LLM calls local. It does not use paid external AI APIs.

## Tech Stack

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- lucide-react icons
- Fetch-based API client

### Backend

- Python 3.11
- FastAPI
- Uvicorn
- SQLAlchemy 2.x
- Alembic
- Pydantic and pydantic-settings
- psycopg
- python-multipart for file uploads
- httpx for Ollama calls

### RAG and AI

- Microsoft MarkItDown for document conversion
- `sentence-transformers/all-MiniLM-L6-v2` for local embeddings
- 384-dimensional embeddings
- PostgreSQL with pgvector for chunk storage and vector search
- Ollama for local LLM generation
- Default Ollama model: `llama3.2`

### Infrastructure

- Docker Compose for frontend, backend, and PostgreSQL/pgvector
- Ollama runs on the host machine
- Linux Docker support through `host.docker.internal:host-gateway`

## Architecture

ResumeRAG uses a full-stack local RAG architecture:

- React frontend provides upload, document list, semantic search, health, and tailored-bullet panels.
- FastAPI backend handles health checks, document ingestion, search, and tailoring endpoints.
- PostgreSQL with pgvector stores uploaded document metadata, chunks, embeddings, tailoring queries, and retrieval results.
- Ollama is called locally from the backend for non-streaming chat generation.

## Document Ingestion Flow

The document upload endpoint follows this pipeline:

1. Accept PDF, DOCX, Markdown, or TXT uploads.
2. Validate filename, extension, and upload size.
3. Save the uploaded file to the backend upload directory.
4. Convert the uploaded document to Markdown with MarkItDown.
5. Reject empty conversions.
6. Split Markdown into heading-aware chunks.
7. Generate local embeddings for each chunk with sentence-transformers.
8. Store the document, Markdown text, chunks, metadata, and vector embeddings in PostgreSQL/pgvector.

## Chunking and Embeddings

- Markdown is chunked with heading awareness.
- Chunk metadata preserves section titles.
- Chunk size and overlap are configurable through environment variables.
- Embeddings are generated locally.
- Embeddings are normalized for cosine search.
- Chunk embeddings are stored in a `vector(384)` column.

## Semantic Search

ResumeRAG exposes a `/search` endpoint:

- Embeds the search query locally.
- Runs pgvector cosine similarity search over stored experience chunks.
- Supports top-k retrieval.
- Supports optional source type and category filters.
- Returns chunk text, document source, section title, similarity score, rank, and metadata.

## Ollama Integration

ResumeRAG integrates with local Ollama through the backend:

- Calls Ollama `/api/chat`.
- Uses non-streaming generation for the MVP.
- Supports model configuration through environment variables.
- Exposes health checks for Ollama availability and selected model availability.
- Returns clear errors when Ollama is unavailable, the model is missing, or generation times out.

## Tailored Bullet Generation

The tailoring endpoint follows this pipeline:

1. Accept a pasted job description and tailoring options.
2. Retrieve relevant uploaded experience chunks using vector search.
3. Build a grounded prompt with numbered source chunks.
4. Ask Ollama to generate JSON resume bullets.
5. Parse the model response.
6. Map model-cited source numbers back to chunk IDs.
7. Store the tailoring query and retrieval results.
8. Return generated bullets, matched requirements, evidence strength, retrieved context, source document names, and similarity scores.

## Anti-Fabrication Behavior

The prompt instructs the model to:

- Use only uploaded user experience context.
- Avoid inventing tools, companies, employers, dates, metrics, degrees, titles, or outcomes.
- Mark weak evidence as low.
- Say not enough evidence when context is insufficient.
- Include job-description keywords only when supported by uploaded evidence.
- Return structured JSON.

The current MVP uses prompt-level anti-fabrication behavior. A future backend validator can further reject bullets with unsupported claims.

## Health and Diagnostics

ResumeRAG includes:

- Basic backend health endpoint.
- Full health endpoint for backend, database, pgvector, embedding model, Ollama connectivity, and Ollama model availability.
- Frontend health checklist showing local service status.

## Frontend Features

- Dashboard with local-first status and health checklist.
- Upload panel for PDF, DOCX, Markdown, and TXT documents.
- Document list with chunk counts and delete action.
- Semantic search panel with filters and similarity scores.
- Tailored bullet panel with target role, company, job description, bullet count, tone, strict mode, and top-k settings.
- Result cards showing generated bullets, matched requirements, evidence strength, source references, warnings, and retrieved evidence chunks.
- Copy buttons for individual bullets and all bullets.

## Testing and Quality

Backend tests cover:

- Health endpoint behavior
- Chunking service behavior
- Embedding service behavior
- Ollama service error handling
- Prompt formatting
- Retrieval service behavior
- Tailoring service JSON parsing and source mapping

Frontend TypeScript checking is run through the Vite/TypeScript build pipeline.

## Engineering Challenges Solved

- Built a local-first RAG stack without paid AI APIs.
- Connected a Dockerized backend to host-machine Ollama.
- Added PDF and DOCX conversion support through MarkItDown extras.
- Switched PyTorch to CPU-only wheels to reduce unnecessary GPU/CUDA package weight.
- Added persistent Hugging Face model cache through a Docker volume.
- Added sample data for testing without private resume content.
- Added clear setup, troubleshooting, and Docker/Ollama guidance in the README.

