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
    jobs/            reusable job status/progress components
    layout/          sidebar, navbar, footer, layout shell
    reports/         persisted report cards and risk display helpers
    ui/              reusable shadcn-style primitives
    upload/          reusable upload components
  data/              shared dashboard labels and quick-action definitions
  lib/               API clients and shared utilities
  pages/             route-level page components
```

Key frontend decisions:

- React Router owns page routing.
- `AuthProvider` recovers session state from `/me`.
- JWTs are not stored in JavaScript; auth relies on the backend HttpOnly cookie.
- Uploads use `XMLHttpRequest` because browser `fetch` does not expose upload progress events.
- Domain-specific API clients live in `lib/` and cover auth, uploads, jobs, BOM imports, BOM diffs, ECO records, graph analysis, documents, and reports.
- Dashboard and workflow pages load authenticated backend data directly instead of relying on static placeholders.

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

## Background Job Flow

1. Frontend starts a job through `/api/v1/jobs/*`.
2. API validates authentication, upload ownership, and basic request shape.
3. API creates a `jobs` row with `queued` status and returns `202 Accepted`.
4. FastAPI `BackgroundTasks` runs the worker in-process for the MVP.
5. Worker opens its own database session and marks the job `processing`.
6. Worker calls the existing business service for BOM import, ECO PDF parsing, graph build, or report generation.
7. Worker stores result metadata or failure details and marks the job `completed` or `failed`.
8. Frontend polls `GET /api/v1/jobs/{job_id}` and displays progress/failure state.

This is intentionally compatible with the existing synchronous endpoints. A future production queue can replace the in-process worker while keeping the job API contract.

## Auth Flow

1. User registers or logs in.
2. Backend hashes passwords with bcrypt.
3. Backend sets a JWT in an HttpOnly cookie named `access_token`.
4. Backend sets a non-HttpOnly `csrf_token` cookie for same-site mutation protection.
5. Frontend calls `/me` on load to recover session state.
6. Protected routes redirect unauthenticated users to `/login`.
7. Backend middleware rejects protected API calls without a valid token.
8. Cookie-authenticated mutation requests require the `X-CSRF-Token` header to match the CSRF cookie.

## Security Middleware

- `JWTAuthenticationMiddleware` validates auth cookies or bearer tokens.
- `CSRFMiddleware` protects cookie-authenticated mutations.
- `InMemoryRateLimitMiddleware` rate limits login/register and authenticated mutations for MVP local deployments.
- `SecurityHeadersMiddleware` adds browser security headers.
- Audit logs record auth events, uploads, and background job creation.

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

## BOM Import Persistence Flow

1. User uploads a BOM.
2. Frontend calls `/api/v1/jobs/bom-imports/from-upload/{upload_id}`.
3. A background job calls `services/bom_importer.py`.
4. The service infers simple version metadata for active same-name imports.
5. The service parses the uploaded file and persists:
   - BOM import batch
   - normalized BOM part rows
   - assembly relationships
   - dependency graph snapshot
6. Frontend polls job status, then refreshes import status and parsed row preview.

## BOM Diff Flow

1. User opens the BOM Compare page.
2. Frontend loads active normalized BOM imports through `/api/v1/bom-imports`.
3. User selects a base import and target import.
4. Frontend calls `/api/v1/bom-imports/diff`.
5. `services/bom_diff.py` compares persisted `bom_parts` by part number.
6. The response identifies added parts, removed parts, revised parts, unchanged count, and possible replacement candidates.

Replacement candidates are deterministic hints based on assembly context and description overlap. They are not persisted as approved changes.

## Dependency Graph Flow

1. User selects a normalized BOM import on the Dependency Graph page.
2. Frontend can queue a graph build job through `/api/v1/jobs/graph/build/{upload_id}`.
3. API loads the uploaded BOM.
4. BOM parser returns structured rows.
5. `services/dependency_graph.py` builds a NetworkX directed graph.
6. Direction is:
   - parent assembly to child assembly
   - child assembly to part number
   - fallback parent assembly to part number
7. Job completion stores graph result metadata.
8. Frontend refreshes graph API endpoints for nodes, edges, parents, children, paths, or statistics.
9. Frontend renders graph statistics, part lookup results, and edge tables.

## ECO Parsing Flow

1. Plain text is parsed directly, or uploaded PDF text is extracted first.
2. `EngineeringChangeParser` calls a provider implementing `BaseLLMProvider`.
3. `LLM_PROVIDER=rule_based` uses local deterministic extraction.
4. `LLM_PROVIDER=openai` uses `OpenAILLMProvider` for structured ECO extraction.
5. If remote parsing fails and fallback is enabled, the parser falls back to the rule-based provider.
6. Future provider-backed LLM implementations should implement the same interface.

## ECO Record Persistence Flow

1. User enters ECO text or uploads an ECO PDF.
2. Plain text can be parsed synchronously; uploaded PDFs are queued through `/api/v1/jobs/eco-records/parse-upload/{upload_id}`.
3. Background worker extracts PDF text and parses the change using `EngineeringChangeParser`.
4. `/api/v1/eco-records/*` workflows persist parsed fields.
5. Frontend shows saved ECO records for later workflows.

## ECO Review Flow

1. User selects a saved ECO record from the Upload ECO page.
2. Frontend calls `/api/v1/eco-records/{record_id}` for detail.
3. User edits parser output fields when needed.
4. Frontend sends corrections through `PATCH /api/v1/eco-records/{record_id}`.
5. Backend stores corrected fields, correction notes, and marks the record `reviewed`.
6. User can call:
   - `/api/v1/eco-records/{record_id}/review`
   - `/api/v1/eco-records/{record_id}/approve`
   - `/api/v1/eco-records/{record_id}/reject`
7. Backend persists workflow status, notes, and timestamps.

This is a lightweight single-user review trail. Report generation can now use selected approved ECO records; a later phase can add assigned approvers and team permissions.

## Document Intelligence Flow

1. User uploads a PDF from the Documents page with `upload_category=document`.
2. Frontend calls `/api/v1/documents/from-upload/{upload_id}` after upload completes.
3. API validates upload ownership and document file type.
4. `services/pdf_text_extractor.py` extracts PDF text.
5. `services/document_parser.py` splits text into sections and detects part references.
6. `services/documents.py` infers document type and persists:
   - indexed document metadata in `engineering_documents`
   - section text and part references in `document_sections`
7. Frontend lists indexed documents through `/api/v1/documents`.
8. Frontend opens section previews through `/api/v1/documents/{document_id}`.
9. Affected-section lookup is available through `/api/v1/documents/affected/{part_number}`.

Current document intelligence is deterministic. It relies on extracted text and part-like identifiers, not semantic LLM matching.

## Intelligence Flow

1. API verifies uploaded BOM ownership.
2. BOM parser returns structured rows.
3. Dependency graph service builds a directed graph.
4. ECO parser returns structured change data.
5. `services/intelligence_layer.py` combines the inputs.
6. `services/report_persistence.py` checks indexed document sections for ECO old/new part references when generating saved reports.
7. API returns a structured impact report with:
   - affected assemblies
   - downstream record impacts
   - affected document sections
   - suggested updates
   - risk assessment

## Report Persistence Flow

1. Frontend calls `/api/v1/jobs/reports/impact-report`.
2. Background worker reuses or creates a normalized BOM import.
3. Worker either parses pasted ECO text or loads a selected approved ECO record.
4. Worker finds indexed document sections that reference ECO old/new parts.
5. `services/intelligence_layer.py` generates the structured report.
6. `services/report_persistence.py` stores report metadata and full structured JSON.
7. Job result metadata includes the saved report id.
8. Frontend refreshes saved reports and renders report detail pages.

## Report Collaboration and Export Flow

1. User opens a saved report detail page.
2. Frontend can download CSV or PDF through:
   - `/api/v1/reports/{report_id}/export.csv`
   - `/api/v1/reports/{report_id}/export.pdf`
3. `services/report_exports.py` renders exports from persisted structured report JSON.
4. User can update report review status through `/api/v1/reports/{report_id}/review`.
5. User can add comments through `/api/v1/reports/{report_id}/comments`.
6. Backend persists comments in `report_comments` and review metadata on `impact_reports`.

Current collaboration is scoped to the report owner. Team visibility and share links are future production features.

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
