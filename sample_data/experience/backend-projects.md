# Backend Projects

## Appointment Booking API

Built a FastAPI backend for appointment booking with PostgreSQL, role-based access patterns, practitioner availability, patient selection, and service/location filtering. Designed REST endpoints for booking workflows and used transaction-safe updates to avoid double booking.

## Authentication Refactor

Refactored frontend authentication flow to replace Supabase login logic with a custom FastAPI `/auth/login` endpoint. Updated Redux auth state, JWT storage, error handling, and maintained existing UI behavior.

## Local Development Stack

Containerized a full-stack development environment with Docker Compose, including a FastAPI backend, React frontend, and PostgreSQL database. Added health checks, environment variable configuration, and repeatable startup commands for local contributors.

