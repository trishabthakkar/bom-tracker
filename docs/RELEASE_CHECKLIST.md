# Release Checklist

Use this checklist when preparing a tagged build, demo environment, or pilot deployment.

## Pre-Release

- Confirm `docs/PROJECT_CONTEXT.md` reflects the latest completed phase.
- Confirm `docs/USER_GUIDE.md` describes all user-facing workflows.
- Confirm `.env.production` is created from `.env.production.example`.
- Set strong values for `POSTGRES_PASSWORD` and `JWT_SECRET_KEY`.
- Set explicit `BACKEND_CORS_ORIGINS`.
- Decide whether ECO parsing uses `LLM_PROVIDER=rule_based` or `LLM_PROVIDER=openai`.
- If OpenAI is enabled, set `OPENAI_API_KEY` and keep fallback enabled for demos unless strict failure is preferred.

## Validation

Run:

```bash
python3 -m compileall backend/app backend/alembic scripts
npm run backend:test
npm run lint
npm run build
npm run qa:perf
```

When a backend is running, also run:

```bash
npm run qa:e2e
```

For production Compose validation:

```bash
POSTGRES_PASSWORD=dummy JWT_SECRET_KEY=dummy-secret docker compose -f docker-compose.prod.yml config
```

## Deployment

1. Back up the current database.
2. Pull the intended git revision.
3. Build containers with `npm run prod:build`.
4. Start services with `npm run prod:up`.
5. Confirm migrations completed successfully.
6. Confirm `/api/v1/health` returns `ok`.
7. Confirm `/api/v1/ready` returns `ready`.
8. Run the live API smoke test against the deployment if safe to create test data.

## Rollback

1. Stop production services with `npm run prod:down`.
2. Restore the previous application revision.
3. Restore the latest compatible database backup if migrations are not backward compatible.
4. Start services again.
5. Recheck `/api/v1/ready`.

## Pilot Acceptance

- A pilot user can create an account.
- The user can upload and import a BOM.
- The user can parse, review, and approve an ECO.
- The user can generate an impact report from an approved ECO.
- The user can see affected assemblies, downstream records, risk, and suggested updates.
- The user can comment on, sign off, and export a report.
- Known limitations are documented before the pilot starts.
