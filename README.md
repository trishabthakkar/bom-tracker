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

## Root Scripts

From the repository root:

```bash
npm run dev
npm run build
npm run lint
npm run backend:dev
```
