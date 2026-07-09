# Production Operations

This guide describes how to build, deploy, monitor, and back up the BOM Change Intelligence Layer.

## Services

Production Compose runs:

- `postgres`: PostgreSQL database.
- `migrate`: one-shot Alembic migration runner.
- `backend`: FastAPI API.
- `frontend`: nginx serving the React build and proxying API/auth routes.

## Required Environment

Create a production env file from the template:

```bash
cp .env.production.example .env.production
```

Set strong values for:

- `POSTGRES_PASSWORD`
- `JWT_SECRET_KEY`
- `BACKEND_CORS_ORIGINS`

Use `LLM_PROVIDER=rule_based` unless OpenAI-backed ECO parsing is intentionally enabled.

## Build And Run

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml build
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
```

The `migrate` service runs `alembic upgrade head` before the backend starts.

## Health Checks

Basic liveness:

```text
GET /api/v1/health
```

Readiness with database check:

```text
GET /api/v1/ready
```

Use readiness for load balancers and container health checks.

## Logs

Application logs are written to stdout/stderr and should be collected by the container runtime or hosting platform.

Important log sources:

- request logs from `RequestLoggingMiddleware`
- auth/upload/job audit logs
- backend container logs
- PostgreSQL logs

## Backups

Back up both:

- PostgreSQL data
- uploaded files volume

Example PostgreSQL backup:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml exec postgres \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > bom_tracker_backup.sql
```

Example upload volume backup:

```bash
docker run --rm \
  -v bom-tracker_uploaded_files:/data:ro \
  -v "$PWD/backups:/backup" \
  alpine tar czf /backup/uploads.tar.gz -C /data .
```

Store backups outside the application host and test restores regularly.

## Restore Outline

1. Stop application services.
2. Restore PostgreSQL from a known-good dump.
3. Restore uploaded files into the upload volume.
4. Run migrations.
5. Start services.
6. Check `/api/v1/ready`.

## Security Checklist

- Change `JWT_SECRET_KEY`.
- Use HTTPS in front of the frontend service.
- Set `BACKEND_CORS_ORIGINS` to exact production origins.
- Keep `.env.production` out of git.
- Back up uploaded files and database together.
- Rotate OpenAI/API keys if enabled.
- Restrict direct database access.

## Current Production Limits

- Background work uses FastAPI in-process background tasks.
- Rate limiting is in-memory per backend process.
- Upload storage is a local Docker volume, not object storage.
- Team permissions and share links are not implemented yet.
