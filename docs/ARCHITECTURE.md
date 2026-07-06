# BOM Tracker Architecture

This document explains the current structure of the AI-Assisted BOM Change Intelligence Layer and where future phases should extend it.

## System Overview

```text
Frontend React app
  -> FastAPI REST API
    -> API routes
      -> business services
        -> SQLAlchemy models / file storage / parser utilities
```

The application is intentionally modular. API routes validate ownership and request boundaries, while business logic lives in service modules.

## Frontend Architecture

Frontend root:

```text
frontend/src/
  auth/              authentication state, protected/public route guards
  components/
    dashboard/       dashboard cards and sections
    layout/          sidebar, navbar, footer, layout shell
    ui/              reusable shadcn-style primitives
    upload/          reusable upload components
  data/              placeholder dashboard data
  lib/               API clients and shared utilities
  pages/             route-level page components
```

Key frontend decisions:

- React Router owns page routing.
- `AuthProvider` recovers session state from `/me`.
- JWTs are not stored in JavaScript; auth relies on the backend HttpOnly cookie.
- Uploads use `XMLHttpRequest` because browser `fetch` does not expose upload progress events.
- Domain-specific API clients live in `lib/` until the API surface grows enough to justify a larger client structure.

## Backend Architecture

Backend root:

```text
backend/app/
  api/               route handlers and dependencies
  core/              settings, security, logging, shared errors
  db/                SQLAlchemy engine/session/base
  middleware/        auth and request logging middleware
  models/            SQLAlchemy database models
  schemas/           Pydantic request/response schemas
  services/          business logic and integrations
  tests/             backend unit tests
```

Key backend decisions:

- FastAPI routes stay thin.
- Business logic lives in `services/`.
- Pydantic schemas define API contracts.
- SQLAlchemy models define persistence.
- Alembic owns schema migrations.
- Upload storage is local for MVP development and ignored by git.

## Auth Flow

1. User registers or logs in.
2. Backend hashes passwords with bcrypt.
3. Backend sets a JWT in an HttpOnly cookie named `access_token`.
4. Frontend calls `/me` on load to recover session state.
5. Protected routes redirect unauthenticated users to `/login`.
6. Backend middleware rejects protected API calls without a valid token.

## Upload Flow

1. Frontend validates extension and size before upload.
2. Backend validates extension, MIME type, size, and empty-file cases.
3. Backend generates a UUID-based stored filename.
4. Backend stores the file under `backend/uploads` by default.
5. Backend stores upload metadata in `uploaded_files`.
6. Future parsing modules consume stored upload records by id.

## BOM Parsing Flow

1. User uploads CSV/XLSX as a BOM.
2. API verifies upload ownership.
3. `services/bom_parser.py` parses the stored file.
4. Parser normalizes known column aliases into:
   - part number
   - description
   - parent assembly
   - child assembly
   - revision
5. Parsed rows are returned as structured JSON.

## Dependency Graph Flow

1. API loads an uploaded BOM.
2. BOM parser returns structured rows.
3. `services/dependency_graph.py` builds a NetworkX directed graph.
4. Direction is:
   - parent assembly to child assembly
   - child assembly to part number
   - fallback parent assembly to part number
5. API returns graph nodes, edges, parents, children, paths, or statistics.

## ECO Parsing Flow

1. Plain text is parsed directly, or uploaded PDF text is extracted first.
2. `EngineeringChangeParser` calls a provider implementing `BaseLLMProvider`.
3. The current provider is local and rule-based.
4. Future provider-backed LLM implementations should implement the same interface.

## Intelligence Flow

1. API verifies uploaded BOM ownership.
2. BOM parser returns structured rows.
3. Dependency graph service builds a directed graph.
4. ECO parser returns structured change data.
5. `services/intelligence_layer.py` combines the inputs.
6. API returns a structured impact report with:
   - affected assemblies
   - downstream record impacts
   - suggested updates
   - risk assessment

## Logging and Errors

- `core/logging.py` configures process logging.
- `middleware/request_logging.py` logs method, path, status, and duration.
- `core/errors.py` defines a stable application error contract for future service-level exceptions.
- Existing route-specific `HTTPException` usage remains valid where it is clearer.

## Extension Guidelines

- Put new API routes under `backend/app/api/v1`.
- Put new business logic under `backend/app/services`.
- Put request and response contracts under `backend/app/schemas`.
- Add unit tests beside existing backend tests.
- Update `docs/PROJECT_CONTEXT.md` whenever a phase changes system behavior.
- Keep frontend route pages in `pages/` and reusable UI in `components/`.
