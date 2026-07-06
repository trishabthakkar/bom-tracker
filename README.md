# AI-Assisted BOM Change Intelligence Layer

Phase 1 bootstrap for a modern full-stack MVP that will later analyze engineering changes and downstream BOM impact.

This phase only scaffolds the project. It does not implement BOM ingestion, ECO parsing, dependency analysis, AI workflows, or impact reports.

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
- SQLite by default for local development
- PostgreSQL-ready via `DATABASE_URL`

Run independently:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Useful commands:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

Default URLs:

- Frontend: `http://localhost:5173`
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
cd backend
source .venv/bin/activate
alembic upgrade head
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

## Root Scripts

From the repository root:

```bash
npm run dev
npm run build
npm run lint
npm run backend:dev
```
