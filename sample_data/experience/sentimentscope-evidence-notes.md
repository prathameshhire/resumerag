# SentimentScope - Project Evidence Notes

## Overview

SentimentScope is a full-stack YouTube comment sentiment analysis application built as a solo full-stack and ML-integration project.

The app lets a user paste a public YouTube video URL or video ID, fetches video metadata and comments through the YouTube Data API, runs transformer-based sentiment analysis on the comments, extracts keywords, caches completed analyses, and displays results in an interactive React dashboard.

## Project Status

- Source code hosted on GitHub: https://github.com/prathameshhire/sentimentscope
- Dockerized local application with separate frontend and backend containers
- Backend API docs available through FastAPI
- Not publicly deployed

## Tech Stack

### Frontend

- React 18
- TypeScript
- Vite
- Tailwind CSS
- React Router
- TanStack React Query for API/server state
- Recharts for visualizations
- lucide-react for icons
- Vitest and Testing Library for frontend tests

### Backend

- Python 3.11
- FastAPI
- Pydantic v2
- pydantic-settings for environment-based configuration
- google-api-python-client for YouTube Data API v3
- Hugging Face Transformers
- PyTorch CPU inference
- scikit-learn for TF-IDF keyword extraction
- diskcache for local analysis caching
- pytest, ruff, and mypy for backend quality checks

### Data and Infrastructure

- Docker Compose for local development
- Local disk cache for completed analysis results
- Local Hugging Face model cache to avoid repeated model downloads
- Environment-based configuration through `.env` files
- YouTube API key stored server-side only

## Architecture

SentimentScope uses a split frontend/backend architecture:

- React/Vite frontend renders the analyzer form and results dashboard.
- FastAPI backend exposes REST endpoints under `/api/v1`.
- Frontend sends analysis requests to `POST /api/v1/analyze`.
- Backend communicates with YouTube Data API v3.
- Backend runs transformer inference using a Hugging Face RoBERTa sentiment model.
- Backend returns structured JSON analysis responses.
- Frontend visualizes analysis results using cards, charts, tabs, and representative comments.

## Main Backend Flow

The main analysis endpoint follows this pipeline:

1. Accept a YouTube URL or bare 11-character video ID.
2. Extract and validate the video ID.
3. Check diskcache for an existing analysis result.
4. Fetch video metadata from the YouTube Data API.
5. Fetch top-level YouTube comments.
6. Clean and normalize comment text.
7. Run batched sentiment classification with a transformer model.
8. Extract keywords using TF-IDF.
9. Aggregate sentiment distribution, percentages, time series, and sample comments.
10. Cache the completed analysis response.
11. Return structured results to the frontend.

## Sentiment Analysis

- Uses `cardiffnlp/twitter-roberta-base-sentiment-latest`.
- Classifies comments as positive, neutral, or negative.
- Returns confidence scores for classified comments.
- Runs inference in batches instead of processing comments one by one.
- Loads the model once during backend startup.

## YouTube API Integration

- Uses YouTube Data API v3.
- Fetches video metadata including title, channel, thumbnail, view count, comment count, and publish date.
- Fetches top-level comments through the YouTube comment threads API.
- Supports full YouTube URLs, shortened URLs, Shorts URLs, and bare video IDs.
- Handles YouTube-specific failure states including missing videos, disabled comments, quota issues, and API failures.

## Caching

SentimentScope uses two local caches:

- `data/huggingface`: stores downloaded Hugging Face model files.
- `data/cache`: stores completed analysis results using diskcache.

The Hugging Face cache prevents repeated model downloads. The analysis cache stores completed video analyses for 24 hours, reducing repeated YouTube API usage and improving repeat request speed.

## Frontend Features

- Analyzer form is the first screen.
- User can paste a YouTube URL or video ID.
- User can choose comment count, defaulting to 50.
- Results page displays video metadata, thumbnail, analyzed comment count, cached status, sentiment summary, positive/neutral/negative percentages, sentiment distribution chart, sentiment-over-time chart, keyword tabs, and representative sample comments.
- Results routes are reloadable using `/results/:videoId`.

## Error Handling

The backend returns stable API error codes:

- `invalid_url`
- `video_not_found`
- `comments_disabled`
- `quota_exceeded`
- `youtube_api_error`
- `internal_error`

The frontend maps these backend error codes to user-facing error states. This keeps failures predictable and avoids exposing raw technical errors to users.

## Security

- YouTube API key is stored only in backend environment variables.
- `.env` files are ignored by Git.
- Frontend never receives the YouTube API key.
- Frontend only stores `VITE_API_BASE_URL`, which is not secret.

## Comment Limits

- Frontend default comment count: 50
- Frontend cap: 500 comments
- Backend default cap: 500 comments

These limits help control latency and YouTube API usage.

## Testing and Quality

Backend testing covers URL parsing, keyword extraction, aggregation logic, cache behavior, YouTube service normalization, error mapping, and analyze endpoint behavior with mocked services.

Frontend testing covers form validation, API error parsing, timeout handling, formatting helpers, and result rendering behavior.

Quality tools used:

- Backend: `pytest`, `ruff`, `mypy`
- Frontend: `Vitest`, `ESLint`, TypeScript type checking

## Engineering Challenges Solved

- Solved Python version mismatch by using Docker with Python 3.11.
- Reduced backend image weight by using CPU-only PyTorch.
- Added persistent Hugging Face cache so the transformer model does not redownload every run.
- Fixed tokenizer length issues by enforcing a safe maximum input length.
- Fixed missing YouTube timestamp crashes by safely handling missing or invalid dates.
- Added request timeout handling so the UI does not spin indefinitely.
- Added stable API error codes and matching frontend error states.
- Protected the YouTube API key by keeping it backend-only and ignored by Git.

## Resume-Relevant Summary

SentimentScope demonstrates full-stack ML application development, external API integration, backend data processing, transformer inference, caching, structured error handling, and frontend data visualization.

The strongest engineering evidence from this project is:

- Built a FastAPI backend that fetches YouTube metadata and comments through the YouTube Data API.
- Integrated a Hugging Face RoBERTa sentiment model for batched comment classification.
- Added disk-backed caching for completed analyses to reduce repeated API usage.
- Built a React/TypeScript dashboard with charts, sentiment summaries, keyword tabs, and sample comments.
- Added stable backend error codes and frontend error states for predictable failure handling.
- Dockerized the app to provide a stable Python 3.11 ML runtime.

