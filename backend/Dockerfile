# ── Stage 1: dependency installer ────────────────────────────────────────────
# Isolates pip install from the runtime image so build-time artifacts (pip
# cache, wheel unpacking) never end up in the final layer.
FROM python:3.11-slim AS builder

WORKDIR /build

RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage 2: runtime ──────────────────────────────────────────────────────────
# LaTeX packages are installed here (not in builder) because pdflatex is
# invoked at request time, not at install time.
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        lmodern \
        texlive-fonts-recommended \
        texlive-latex-base \
        texlive-latex-extra \
        texlive-latex-recommended \
        texlive-plain-generic \
    && rm -rf /var/lib/apt/lists/*

# Copy the pre-built virtualenv from the builder stage
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

COPY pytest.ini .
COPY alembic.ini .
COPY migrations ./migrations
COPY app ./app
# tests/ is intentionally excluded; in development the docker-compose volume
# mount (./backend/tests:/app/tests) makes them available inside the container.

RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
