# ML Infrastructure Project

## Local RAG Prototype

Built a local retrieval-augmented generation prototype with document ingestion, Markdown chunking, sentence-transformer embeddings, vector search, and source-grounded generation. Designed prompts to avoid unsupported claims and return structured JSON with evidence references.

## Embedding Workflow

Implemented batch embedding for document chunks using `sentence-transformers/all-MiniLM-L6-v2`. Normalized vectors for cosine search and stored metadata alongside chunks so retrieved evidence could be traced back to source documents.

## Model Operations

Integrated a local Ollama model through a FastAPI service layer. Added timeout handling, model availability checks, and clear error messages for missing or unreachable local models.

