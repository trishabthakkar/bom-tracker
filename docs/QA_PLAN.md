# QA Plan

This document captures the repeatable checks for the MVP workflow. Use it before demos, pilot releases, and production deployments.

## Automated Checks

Run from the repository root:

```bash
python3 -m compileall backend/app backend/alembic scripts
npm run backend:test
npm run lint
npm run build
PYTHONPATH=backend PERF_BOM_ROWS=1000 backend/.venv/bin/python scripts/performance_smoke.py
```

What these checks cover:

- Backend syntax and import safety.
- Parser, graph, ECO, document, intelligence, security, job, export, and collaboration unit tests.
- A service-level full workflow test for BOM import, BOM diff, ECO approval, impact report generation, comments, sign-off, and exports.
- Frontend lint and production build.
- A local performance smoke test for larger generated BOMs.

## Live API Smoke Test

The live smoke test exercises the running backend over HTTP with real cookies and CSRF headers.

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

The script creates a temporary test user, uploads the demo BOM files, imports both BOMs, builds the graph, compares BOM versions, parses and approves an ECO, generates a report, comments on it, signs it off, and downloads CSV/PDF exports.

## Manual Workflow Checklist

1. Register a fresh user.
2. Upload `demo-files/demo-bom.csv` as a BOM.
3. Confirm the BOM import job completes and parsed rows are visible.
4. Upload or use `demo-files/demo-bom-v2.csv` as a second BOM version.
5. Open BOM Compare and confirm `PN-1212` to `PN-2212` appears as a likely replacement.
6. Open Dependency Graph and confirm parents for `PN-1212` include the cooling manifold assembly path.
7. Upload or paste the ECO text from `demo-files/demo-eco.txt`.
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
- `.env`, `.env.production`, uploads, database files, and generated artifacts are ignored by git.
- Auth cookies are HttpOnly.
- Production cookies use `Secure`.
- Mutation requests require the CSRF cookie/header pair.
- Upload validation rejects unsupported extensions, empty files, and oversized files.
- Protected records are always scoped to the current user.
- Rate limits are enabled for login/register and authenticated mutation requests.
- Production CORS origins are explicit and do not use wildcards with credentials.
- Backups are encrypted or stored in a controlled location.

## Known QA Limits

- The live smoke script does not validate frontend rendering.
- The PDF export is intentionally simple and dependency-free.
- Background jobs use FastAPI `BackgroundTasks`, not a durable external queue.
- Document intelligence is deterministic text matching, not semantic review.
