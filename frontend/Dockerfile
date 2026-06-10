# ── Stage 1: build ───────────────────────────────────────────────────────────
# Runs `tsc -b && vite build` and produces the static bundle in /app/dist.
# VITE_* env vars are baked into the bundle at build time by Vite; they are
# not available at nginx runtime.
FROM node:20-alpine AS builder

WORKDIR /app

ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ── Stage 2: serve ────────────────────────────────────────────────────────────
# Minimal nginx image (~25 MB). Serves the pre-built /dist as a React SPA
# with proper cache headers and client-side routing fallback.
FROM nginx:alpine AS runner

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# nginx starts automatically; no CMD override needed.
