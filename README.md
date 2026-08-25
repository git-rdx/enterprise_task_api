# Enterprise Task & Workflow Management API

A production-oriented backend application built with FastAPI for managing
projects, tasks, users, permissions, authentication, background jobs,
file uploads and workflow operations.

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- Celery
- JWT Authentication
- Google OAuth2 / OpenID Connect
- Docker & Docker Compose
- pytest
- GitHub Actions
- AWS ECR
- HTML, CSS and JavaScript frontend

## Architecture

The backend follows a layered architecture:

Router → Service → Repository → Database

This separates API handling, business logic and database access.

## Main Features

- User registration and login
- Email verification
- Password reset
- JWT access tokens
- Refresh-token rotation and reuse detection
- Google OAuth2 / OIDC login
- Role-Based Access Control
- Resource-level authorization
- Project management
- Project membership
- Task assignment and management
- Pagination, filtering and sorting
- Redis caching
- API rate limiting
- Celery background jobs
- File upload/download/delete
- Global exception handling
- Request logging
- Dockerized development environment
- Automated tests with pytest
- CI using GitHub Actions

## Roles

### Admin
Full administrative access.

### Manager
Can manage projects and tasks according to project-level permissions.

### Employee
Can work with assigned tasks according to authorization rules.

## Authentication

The application supports:

- Email/password authentication
- JWT access tokens
- Refresh-token rotation
- Refresh-token reuse detection
- Google OAuth2 / OpenID Connect
- OAuth state validation
- OIDC nonce validation
- PKCE

## Testing

Tests include:

- Authentication
- Database connectivity
- Project authorization
- Task authorization
- Refresh-token rotation
- Refresh-token reuse detection


## Run the application locally:
docker compose up --build

### Services include:
FastAPI
PostgreSQL
Redis
Celery


## Run tests:
```bash
python -m pytest -v