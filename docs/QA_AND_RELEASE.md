# QA and Release Checklist

Repeatable checks and release steps for the MVP workflow. Use this before demos, pilot
releases, and production deployments. (Merged from the former `QA_PLAN.md` and
`RELEASE_CHECKLIST.md`, which overlapped heavily.)

## Automated Checks

Run from the repository root:

```bash
python3 -m compileall backend/app backend/alembic scripts
npm run backend:test
npm run lint
npm run build
npm run qa:perf
```

What these cover:

- Backend syntax and import safety.
- Parser, graph, ECO, document, intelligence, security, job, export, and collaboration unit
  tests.
- A service-level full workflow test covering BOM import, BOM diff, ECO approval, impact
  report generation, comments, sign-off, and exports.
- Frontend lint and production build.
- A local performance smoke test, including a lattice-shaped BOM that exercises dependency
  path bounding (see `docs/FIX_PLAN.md` Phase 23).

For production Compose validation:

```bash
POSTGRES_PASSWORD=dummy JWT_SECRET_KEY=dummy-secret docker compose -f docker-compose.prod.yml config
```

## Live API Smoke Test

Exercises the running backend over HTTP with real cookies and CSRF headers.

Start the backend and database first:

```bash
npm run db:up
npm run db:migrate
npm run backend:dev
```

Then run:

```bash
npm run qa:e2e
```

The script creates a temporary test user, uploads the demo BOM files, imports both BOMs,
builds the graph, compares BOM versions, parses and approves an ECO, generates a report,
comments on it, signs it off, and downloads CSV/PDF exports.

## Manual Workflow Checklist

1. Register a fresh user.
2. Upload `demo-files/demo-bom.csv` as a BOM.
3. Confirm the BOM import job completes and parsed rows are visible.
4. Upload or use `demo-files/demo-bom-v2.csv` as a second BOM version.
5. Open BOM Compare and confirm `PN-1212` to `PN-2212` appears as a likely replacement.
6. Open Dependency Graph and confirm parents for `PN-1212` include the cooling manifold
   assembly path, and that the graph shows one root and no cycles.
7. Upload or paste the ECO text from `demo-files/demo-eco.txt` (or the computer-themed set
   in `demo-files/computer-*` for an easier-to-follow example).
8. Review the parsed ECO fields, correct them if needed, and approve the ECO.
9. Generate an impact report from the approved ECO and imported BOM.
10. Open the report detail page, add a comment, sign it off, and download CSV/PDF exports.

## Accessibility Checklist

- Every page is keyboard reachable without losing focus.
- Buttons and icon-only controls have accessible labels or titles.
- Form errors are visible near the field or action that caused them.
- Upload dropzones also support regular file picker interaction.
- Loading states do not trap focus.
- Color is not the only indicator for risk, status, success, or failure.
- Text remains readable in light and dark modes.
- Responsive layouts do not overlap at mobile widths.

## Security Review Checklist

- `JWT_SECRET_KEY` is strong and not the default value.
- `.env`, `.env.production`, uploads, database files, and generated artifacts are ignored
  by git.
- Auth cookies are HttpOnly.
- Production cookies use `Secure`.
- Mutation requests require the CSRF cookie/header pair.
- Upload validation rejects unsupported extensions, empty files, and oversized files.
- Protected records are always scoped to the current user.
- Rate limits are enabled for login/register and authenticated mutation requests, and are
  keyed per-user for authenticated requests (not just per-IP - see `docs/FIX_PLAN.md`
  Phase 25).
- Production CORS origins are explicit and do not use wildcards with credentials.
- Backups are encrypted or stored in a controlled location.

## Pre-Release

- Confirm `docs/PROJECT_CONTEXT.md` reflects the latest completed phase.
- Confirm `docs/USER_GUIDE.md` describes all user-facing workflows.
- Confirm `.env.production` is created from `.env.production.example`.
- Set strong values for `POSTGRES_PASSWORD` and `JWT_SECRET_KEY`.
- Set explicit `BACKEND_CORS_ORIGINS`.
- Decide whether ECO parsing uses `LLM_PROVIDER=rule_based` or `LLM_PROVIDER=openai`.
- If OpenAI is enabled, set `OPENAI_API_KEY` and keep fallback enabled for demos unless
  strict failure is preferred.

## Deployment

1. Back up the current database.
2. Pull the intended git revision.
3. Build containers with `npm run prod:build`.
4. Start services with `npm run prod:up`.
5. Confirm migrations completed successfully.
6. Confirm `/api/v1/health` returns `ok`.
7. Confirm `/api/v1/ready` returns `ready` (this endpoint is public and reflects real
   database connectivity - see `docs/FIX_PLAN.md` Phase 24).
8. Run the live API smoke test against the deployment if safe to create test data.

## Rollback

1. Stop production services with `npm run prod:down`.
2. Restore the previous application revision.
3. Restore the latest compatible database backup if migrations are not backward
   compatible.
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

## Known QA Limits

- The live smoke script does not validate frontend rendering.
- The PDF export is intentionally simple and dependency-free, and truncates past 48 lines
  with an explicit notice rather than paginating (see `docs/FIX_PLAN.md` Phase 28).
- Background jobs use FastAPI `BackgroundTasks`, not a durable external queue.
- Document intelligence is deterministic text matching, not semantic review.
