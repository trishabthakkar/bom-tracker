# AI-Assisted BOM Change Intelligence Layer

A full-stack app for analyzing engineering changes (ECOs) and their downstream impact
across BOMs, assemblies, procurement, and documentation. Upload a bill of materials and an
engineering change, and it generates a risk-scored impact report showing affected
assemblies, downstream records, and suggested follow-up actions.

## Quick start

```bash
npm run setup       # backend venv + deps, frontend deps, .env files - safe to re-run
npm run db:up        # start PostgreSQL
npm run db:migrate   # apply migrations
npm run dev:all       # start backend + frontend together
```

Then open:

- Frontend: <http://localhost:5173>
- Backend API docs: <http://localhost:8000/docs>
- Backend health: <http://localhost:8000/api/v1/health>

If Docker reports a permission error on `db:up`, either run Docker from a terminal with
Docker access, or run `sudo docker compose up -d postgres`.

If port 5432 is already in use by another Postgres install on your machine, copy
`.env.example` to `.env` at the repo root and set `POSTGRES_PORT` to something free (e.g.
`55432`) - then update the port in `DATABASE_URL` inside `backend/.env` to match.

To try the app with sample data, see `demo-files/` - `computer-bom.csv`,
`computer-eco.pdf`, and two indexed documents make up a small, easy-to-follow example
(a desktop PC BOM with a CPU replacement ECO). The original `demo-bom.csv` /
`demo-bom-v2.csv` set is a cooling-skid BOM used by the automated QA scripts.

## What it does

- Authentication with JWT cookies, CSRF protection, and rate limiting.
- Secure CSV/XLSX/PDF uploads with per-category validation.
- Deterministic BOM parsing and NetworkX-based dependency graph analysis.
- BOM-to-BOM diffing (added/removed/revised parts, replacement candidates).
- Engineering change (ECO) parsing from text or uploaded PDF, with a pluggable rule-based
  or OpenAI-backed parser.
- ECO review workflow: correct, review, approve, or reject parsed changes.
- Deterministic impact report generation: affected assemblies, downstream record impact,
  risk scoring, and suggested updates.
- Downstream engineering document indexing (installation guides, service manuals, etc.),
  cross-referenced against affected parts in generated reports.
- Persisted reports with comments, sign-off workflow, and CSV/PDF export.
- Background job processing for slower operations (BOM import, graph build, report
  generation).

See `docs/PROJECT_CONTEXT.md` for the full phase-by-phase history and technical detail
behind each of these.

## Project structure

```text
bom-tracker/
├── frontend/           React + TypeScript + Vite + Tailwind + React Router
│   └── src/{pages,components,lib,auth}/
├── backend/             FastAPI + SQLAlchemy + Alembic + PostgreSQL
│   ├── alembic/versions/
│   └── app/{api,core,db,models,schemas,services,tests}/
├── demo-files/          Sample BOMs, ECOs, and documents for trying the app
├── scripts/              e2e_api_workflow.py, performance_smoke.py, setup.sh
├── docs/                 See "Documentation" below
├── docker-compose.yml    Local PostgreSQL
├── docker-compose.prod.yml
└── package.json          Root scripts (see below)
```

## Running frontend/backend separately

Useful when you don't want `dev:all`, e.g. to see backend logs on their own.

**Frontend only:**

```bash
cd frontend
npm install
npm run dev
```

**Backend only:**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

## Testing and QA

```bash
npm run backend:test   # backend unit/integration tests (pytest)
npm run lint            # frontend lint
npm run build            # frontend production build
npm run qa:perf          # parser/graph/report performance smoke test
npm run qa:e2e            # live API smoke test - needs a running backend + database
```

See `docs/QA_AND_RELEASE.md` for the full manual QA checklist, accessibility/security
review checklists, and release/rollback steps.

## Production

```bash
cp .env.production.example .env.production   # then set real secrets
npm run prod:build
npm run prod:up
```

See `docs/PRODUCTION.md` for deployment, health checks, backups, restore steps, and
security notes.

## All root scripts

```bash
npm run setup           # one-time local environment setup
npm run dev              # frontend only
npm run dev:all           # postgres + backend + frontend together
npm run build             # frontend production build
npm run lint               # frontend lint
npm run backend:dev        # backend dev server
npm run backend:test        # backend test suite
npm run qa:e2e                # live API smoke test
npm run qa:perf                 # performance smoke test
npm run db:up                    # start PostgreSQL
npm run db:migrate                 # apply migrations
npm run db:reset-data                # clear app data + stored uploads (local dev only)
npm run db:down                        # stop PostgreSQL
npm run prod:build                      # build production images
npm run prod:up                          # start production stack
npm run prod:logs                         # tail production logs
npm run prod:down                          # stop production stack
```

## Documentation

- `docs/PROJECT_CONTEXT.md` - product context, full phase-by-phase history, feature
  detail, security decisions, and roadmap. The most complete reference in this repo.
- `docs/ARCHITECTURE.md` - system architecture and request flows.
- `docs/USER_GUIDE.md` - user-facing feature guide.
- `docs/PRODUCTION.md` - deployment operations.
- `docs/QA_AND_RELEASE.md` - QA checklists and release/rollback steps.
- `docs/FIX_PLAN.md` - record of the August 2026 whole-project review and the fix phases
  that followed it.
