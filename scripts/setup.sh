#!/usr/bin/env bash
# One-time local setup: backend venv + deps, frontend deps, and .env files.
# Safe to re-run - every step is skipped if already done.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "==> Backend: creating virtualenv (backend/.venv) if needed"
if [ ! -d backend/.venv ]; then
  python3 -m venv backend/.venv
fi

echo "==> Backend: installing dependencies (requirements-dev.txt)"
backend/.venv/bin/pip install --upgrade pip -q
backend/.venv/bin/pip install -q -r backend/requirements-dev.txt

echo "==> Backend: copying .env from .env.example if missing"
[ -f backend/.env ] || cp backend/.env.example backend/.env

echo "==> Frontend: copying .env from .env.example if missing"
[ -f frontend/.env ] || cp frontend/.env.example frontend/.env

echo "==> Root: copying .env from .env.example if missing (docker compose POSTGRES_PORT)"
[ -f .env ] || cp .env.example .env

echo "==> Frontend: installing npm dependencies"
npm --prefix frontend ci

cat <<'EOF'

Setup complete. Next steps:
  npm run db:up       # start PostgreSQL
  npm run db:migrate  # apply migrations
  npm run dev:all      # start backend + frontend together
EOF
