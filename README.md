# AI-Assisted BOM Change Intelligence Layer

A modern full-stack MVP for analyzing engineering changes and downstream BOM impact.

The application currently supports authentication, secure uploads, BOM parsing, persisted BOM imports, dependency graph analysis, persisted ECO records, and saved deterministic impact reports. AI provider integration is intentionally deferred to later phases.

## Repository Structure

```text
bom-tracker/
├── frontend/
│   ├── src/
│   │   ├── components/ui/
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── pages/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── router.tsx
│   │   └── styles.css
│   ├── components.json
│   ├── package.json
│   ├── tailwind.config.ts
│   └── vite.config.ts
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── app/
│   │   ├── api/v1/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── tests/
│   │   └── main.py
│   ├── alembic.ini
│   ├── requirements.txt
│   └── .env.example
├── docs/
│   ├── ARCHITECTURE.md
│   └── PROJECT_CONTEXT.md
├── .gitignore
├── package.json
└── README.md
```

## Frontend

Stack:

- React
- TypeScript
- Vite
- Tailwind CSS
- React Router
- shadcn/ui-ready structure via `components.json`, `src/components/ui`, and `src/lib/utils.ts`

Run independently:

```bash
cd frontend
npm install
npm run dev
```

Useful commands:

```bash
npm run build
npm run lint
npm run preview
```

Environment:

```bash
cp .env.example .env
```

## Backend

Stack:

- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL by default for local development
- SQLite-compatible via `DATABASE_URL` if needed for quick experiments

Start PostgreSQL:

```bash
npm run db:up
```

If Docker reports a permission error, start it from a terminal with Docker access or run:

```bash
sudo docker compose up -d postgres
```

Run independently:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Useful commands:

```bash
npm run db:up
npm run db:migrate
npm run db:down
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

Default URLs:

- Frontend: `http://localhost:5173` or `http://localhost:5174`
- Backend API: `http://localhost:8000`
- Backend docs: `http://localhost:8000/docs`
- Backend health: `http://localhost:8000/api/v1/health`

## Authentication

Phase 3 adds JWT-backed authentication endpoints:

```text
POST /register
POST /login
POST /logout
GET  /me
```

Run migrations before using authentication:

```bash
npm run db:migrate
```

Security defaults:

- Passwords are hashed with bcrypt.
- JWTs are stored in an HttpOnly cookie named `access_token`.
- Cookies use `SameSite=Lax`; `Secure` is enabled automatically outside local development.
- JavaScript does not read or store JWTs.
- `JWT_SECRET_KEY` must be changed for production.
- `/me` is protected by JWT middleware plus a current-user dependency.

## Secure Uploads

Phase 5 adds authenticated file uploads for future parsing modules.

Supported file types:

- `.csv`
- `.xlsx`
- `.pdf`

Default upload limit:

- `25 MB`

Backend endpoints:

```text
POST /api/v1/uploads
GET  /api/v1/uploads
```

Run migrations before using uploads:

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

Upload files are stored locally under `backend/uploads` by default. The directory is ignored by git.

Project context is tracked in:

```text
docs/PROJECT_CONTEXT.md
```

Architecture documentation is tracked in:

```text
docs/ARCHITECTURE.md
```

User-facing feature documentation is tracked in:

```text
docs/USER_GUIDE.md
```

## BOM Parser

Phase 6 adds deterministic BOM parsing for uploaded CSV/XLSX files.

Endpoint:

```text
POST /api/v1/bom/parse/{upload_id}
```

The parser extracts:

- part number
- description
- parent assembly
- child assembly
- revision

Run parser tests:

```bash
cd backend
source .venv/bin/activate
pytest app/tests
```

## Dependency Graph

Phase 7 adds NetworkX-based dependency graph analysis for parsed BOM files.

Endpoints:

```text
POST /api/v1/graph/build/{upload_id}
GET  /api/v1/graph/{upload_id}/parents/{part_number}
GET  /api/v1/graph/{upload_id}/children/{part_number}
GET  /api/v1/graph/{upload_id}/paths?source={source}&target={target}
GET  /api/v1/graph/{upload_id}/stats
```

The graph is directed from parent assembly to child assembly, then from child assembly to part number when both values exist. If no child assembly is provided, it falls back to parent assembly to part number.

## Engineering Change Parser

Phase 8 adds structured ECO parsing for plain text and uploaded PDFs.

Endpoints:

```text
POST /api/v1/eco/parse-text
POST /api/v1/eco/parse-upload/{upload_id}
```

Extracted fields:

- change type
- old part
- new part
- reason
- effective date

The parser uses an LLM abstraction layer with a local rule-based provider. External provider integration is intentionally deferred.

## Intelligence Layer

Phase 9 adds deterministic impact report generation. Phase 11 adds persisted impact reports.

Endpoint:

```text
POST /api/v1/intelligence/impact-report
POST /api/v1/reports/impact-report
GET  /api/v1/reports
GET  /api/v1/reports/{report_id}
```

Request body:

```json
{
  "bom_upload_id": 1,
  "eco_text": "Replace old part PN-100 with new part PN-200. Reason: supplier obsolescence. Effective date: 2026-08-15."
}
```

The response includes affected assemblies, downstream record impacts, suggested updates, and risk assessment. Use `/api/v1/reports/impact-report` when the report should be saved and visible in the Reports page.

## Persisted Engineering Data

Phase 11 persists normalized engineering records.

Endpoints:

```text
POST /api/v1/bom-imports/from-upload/{upload_id}
GET  /api/v1/bom-imports
GET  /api/v1/bom-imports/{import_id}
POST /api/v1/eco-records/parse-text
GET  /api/v1/eco-records
POST /api/v1/reports/impact-report
GET  /api/v1/reports
GET  /api/v1/reports/{report_id}
```

The frontend now shows normalized BOM import status, saved ECO records, saved report history, and report detail pages.

## Root Scripts

From the repository root:

```bash
npm run dev
npm run build
npm run lint
npm run backend:dev
npm run backend:test
npm run db:up
npm run db:migrate
npm run db:down
```
