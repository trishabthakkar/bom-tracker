# AI-Assisted BOM Change Intelligence Layer - Project Context

This document is the living product and technical context file for the project. Update it whenever a phase adds features, endpoints, architecture, security decisions, or important constraints.

## Product Purpose

The application analyzes engineering changes and determines downstream impact across BOMs, assemblies, procurement records, installation guides, commissioning procedures, and service manuals.

The long-term goal is to ingest engineering data, build a dependency graph, interpret changes with AI-assisted services, and produce human-readable impact reports with risk levels and suggested downstream updates.

## Current Architecture

```text
frontend/
  React + TypeScript + Vite + Tailwind CSS + React Router

backend/
  FastAPI + SQLAlchemy + Alembic + PostgreSQL for local MVP development
```

The frontend and backend run independently. The frontend calls protected backend APIs with cookie-based authentication.

Local PostgreSQL runs through `docker-compose.yml`. The default development database URL is:

```text
postgresql+psycopg://bom_tracker:bom_tracker_password@localhost:5432/bom_tracker
```

Development CORS allows both `localhost` and `127.0.0.1` on Vite ports `5173` and `5174`.

## Implemented Phases

### Phase 1 - Project Bootstrap

- Created `frontend/` and `backend/` structure.
- Added React, TypeScript, Vite, Tailwind CSS, React Router, and shadcn/ui-ready conventions.
- Added FastAPI, SQLAlchemy, Alembic, environment config, and setup documentation.

### Phase 2 - Application Shell

- Added responsive dashboard layout.
- Added collapsible sidebar, top navigation, footer, and dark mode.
- Added placeholder routes for Dashboard, Upload BOM, Upload ECO, Reports, Dependency Graph, History, and Settings.

### Phase 3 - Authentication

- Added `User` model and users migration.
- Added JWT-backed authentication endpoints:
  - `POST /register`
  - `POST /login`
  - `POST /logout`
  - `GET /me`
- Added frontend login/register pages, auth provider, protected routes, and persisted auth recovery through `/me`.

### Phase 4 - Dashboard

- Replaced dashboard placeholder with realistic placeholder cards.
- Added recent uploads, recent reports, quick actions, recent activity, metrics, badges, and loading skeletons.
- Kept shared dashboard labels and quick actions in `frontend/src/data/dashboardData.ts`; Phase 12 later connected the dashboard records to backend data.

### Phase 5 - Secure File Uploads

- Added secure upload API for CSV, XLSX, and PDF.
- Added upload metadata persistence in `uploaded_files`.
- Added server-side file size validation.
- Added extension and MIME validation.
- Added server-generated stored filenames.
- Added local file storage in `backend/uploads`.
- Added upload history endpoint.
- Added frontend drag-and-drop upload pages with validation, progress bar, and upload history.

### Phase 6 - BOM Parser

- Added deterministic CSV/XLSX BOM parser.
- Extracts:
  - part number
  - description
  - parent assembly
  - child assembly
  - revision
- Added structured Python parser objects and API response schemas.
- Added protected parse endpoint for already-uploaded BOM files.
- Added parser unit tests for CSV, XLSX, aliases, missing required columns, and unsupported extensions.

### Phase 7 - Dependency Graph

- Added NetworkX dependency graph service.
- Converts parsed BOM rows into a directed graph.
- Keeps graph construction separate from parsing.
- Adds directed edges from parent assembly to child assembly, or from parent assembly to part number when no child assembly is present.
- Added protected graph endpoints for graph build, affected parents, affected children, dependency paths, and graph statistics.
- Added graph unit tests for construction, traversal, paths, and statistics.

### Phase 8 - Engineering Change Parsing

- Added Engineering Change parsing for plain text.
- Added PDF text extraction for uploaded ECO PDFs.
- Extracts:
  - change type
  - old part
  - new part
  - reason
  - effective date
- Added provider-neutral LLM abstraction layer.
- Added local rule-based provider so the system runs without external API keys.
- Added protected ECO parsing endpoints.
- Added unit tests for text parsing and provider abstraction.

### Phase 9 - Intelligence Layer

- Added deterministic intelligence service that combines:
  - parsed BOM data
  - dependency graph
  - parsed ECO data
- Generates structured impact reports.
- Determines affected assemblies, downstream record categories, risk level, risk reasons, and suggested updates.
- Keeps business logic in `services/intelligence_layer.py`.
- Added protected impact report endpoint.
- Added unit tests for replacement, revision, no-match, risk, and downstream record selection.

### Phase 10 - Refactor, Polish, and Architecture Documentation

- Added backend logging configuration.
- Added request logging middleware.
- Added shared API error primitives for future centralized error handling.
- Improved frontend accessibility for navigation, upload dropzone, and loading states.
- Reused existing UI button primitive in upload flows.
- Added architecture documentation in `docs/ARCHITECTURE.md`.
- Added focused unit coverage for shared error primitives.

### PostgreSQL Local Development Switch

- Switched default backend configuration from SQLite to PostgreSQL.
- Added `docker-compose.yml` for local PostgreSQL.
- Added root scripts for starting PostgreSQL and running migrations.
- Expanded development CORS origins to support both `localhost` and `127.0.0.1` on Vite ports `5173` and `5174`.

### User Guide Documentation

- Added `docs/USER_GUIDE.md`.
- Documents current UI features, backend/API-only features, setup steps, database behavior, and troubleshooting.
- Should be updated whenever new user-facing features or workflows are added.

### Phase 11 - Persistence for Normalized BOMs, Graphs, ECOs, and Reports

- Added persistent normalized BOM import batches.
- Added persistent BOM part rows and assembly relationships.
- Added persistent parsed ECO records.
- Added persistent dependency graph snapshots.
- Added persistent generated impact reports with full structured report JSON.
- Added Alembic migration `20260706_0003_persist_engineering_data.py`.
- Added protected APIs for BOM imports, ECO records, and saved reports.
- Added report history and report detail views in the frontend.
- Added Upload BOM import status and parsed row preview after upload.
- Added Upload ECO text parsing and saved ECO record visibility.
- Added focused unit coverage for BOM import and report persistence services.

### Phase 12 - Frontend Data Integration

- Connected Dashboard metrics, recent uploads, reports, and activity to real backend APIs.
- Replaced manual report BOM upload id entry with a normalized BOM import selector.
- Connected uploaded ECO PDFs to saved ECO parsing after upload.
- Replaced Dependency Graph placeholder with a real graph explorer.
- Added graph API client for build, stats, affected parents, and affected children.
- Added frontend loading, empty, error, retry, and selection states around persisted workflows.

### Post-Phase 12 Debug Fixes

- Fixed stored upload path resolution so records saved as `uploads/{file}` can still resolve files stored under `backend/uploads/{file}`.
- Standardized new local uploads to save under `backend/uploads` when `UPLOAD_DIRECTORY=uploads`.
- Added parser-level missing-file handling so graph, BOM, ECO, and report workflows return useful API errors instead of unhandled `FileNotFoundError` exceptions.
- Added unit coverage for upload directory and legacy relative path resolution.
- Added an upload replacement option that marks older same-name uploads as `replaced` and archives older BOM imports/reports when possible.
- Added `npm run db:reset-data` for local development resets of app rows and stored upload files.

### Phase 13 - Background Jobs and Processing Pipeline

- Added persisted `jobs` table with queued, processing, completed, and failed statuses.
- Added Alembic migration `20260709_0004_create_jobs.py`.
- Added protected job APIs for BOM import, ECO PDF parsing, graph build, and impact report generation.
- Implemented FastAPI `BackgroundTasks` workers for MVP async processing.
- Added job progress, status messages, result metadata, failure messages, and job history endpoints.
- Connected Upload BOM, Upload ECO, Reports, and Dependency Graph frontend workflows to background jobs.
- Added reusable frontend job API client and job status/progress panel.
- Kept existing synchronous APIs available for compatibility and direct testing.
- Added backend unit coverage for job persistence and upload replacement behavior.

### Phase 14 - Security Hardening Baseline

- Added CSRF protection for cookie-authenticated mutation endpoints.
- Added `csrf_token` cookie and required `X-CSRF-Token` frontend header for protected mutations.
- Added in-memory rate limiting for login/register and authenticated mutation endpoints.
- Added security headers: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and `Permissions-Policy`.
- Added audit logging helper and audit events for register, login, logout, uploads, and background job creation.
- Added configurable rate-limit environment variables.
- Added backend unit coverage for CSRF policy, rate limiting, and security headers.

### Phase 15 - AI Provider Integration

- Added `OpenAILLMProvider` behind the existing `BaseLLMProvider` contract.
- Added provider factory driven by `LLM_PROVIDER`.
- Added OpenAI configuration:
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL`
  - `LLM_TIMEOUT_SECONDS`
  - `LLM_FALLBACK_TO_RULE_BASED`
- Kept `rule_based` as the default provider so local development works without API keys.
- Added structured JSON-schema ECO extraction for the OpenAI provider.
- Added provider timeout/error handling through `LLMProviderError`.
- Added deterministic fallback to `RuleBasedLLMProvider` when remote provider calls fail and fallback is enabled.
- Added unit coverage for OpenAI response parsing and fallback behavior.

### Phase 16 - Downstream Document Intelligence

- Added engineering document indexing for uploaded PDF manuals and downstream records.
- Added `engineering_documents` and `document_sections` persistence tables.
- Added document section extraction, document type inference, and part reference detection.
- Added protected document APIs for indexing, listing, detail inspection, and affected-section lookup.
- Added a frontend Documents page for PDF upload, indexing, document history, section previews, and detected part references.
- Connected saved impact reports to indexed document sections that reference ECO old/new parts.
- Added affected document sections to structured impact report JSON and report detail UI.
- Increased report risk scoring when affected downstream document sections are found.
- Added parser, report persistence, and document endpoint regression tests.

### Phase 17 - Advanced BOM and ECO Workflows

- Added BOM import version metadata:
  - `version_label`
  - `previous_import_id`
  - `import_notes`
- Added automatic `vN` labels for active BOM imports with the same filename.
- Added BOM-to-BOM diff service and protected `POST /api/v1/bom-imports/diff` endpoint.
- BOM diffs detect added parts, removed parts, revised common parts, unchanged parts, and likely replacement candidates.
- Added frontend BOM Compare page for selecting two normalized BOM imports and inspecting diff results.
- Added ECO workflow fields:
  - `workflow_status`
  - `correction_notes`
  - `approval_notes`
  - `reviewed_at`
  - `approved_at`
  - `rejected_at`
- Added ECO correction and review endpoints for updating parsed fields, marking reviewed, approving, and rejecting.
- Added ECO review controls to the Upload ECO page.
- Added Alembic migration `20260709_0006_advanced_bom_eco_workflows.py`.
- Added backend unit coverage for BOM diff behavior and ECO workflow transitions.

### Phase 18 - Reporting, Export, and Collaboration

- Added report review metadata:
  - `review_status`
  - `owner_user_id`
  - `assigned_user_id`
  - `signoff_notes`
  - `reviewed_at`
  - `signed_off_at`
- Added persisted `report_comments`.
- Added report review statuses:
  - `draft`
  - `in_review`
  - `changes_requested`
  - `signed_off`
- Added report review update endpoint.
- Added report comments endpoint.
- Added CSV report export.
- Added simple PDF report export without adding a new dependency.
- Added report generation from selected approved ECO records.
- Updated Reports page to use either pasted ECO text or an approved ECO record.
- Updated Report Detail page with export buttons, review/sign-off controls, and comments.
- Added Alembic migration `20260709_0007_report_collaboration_exports.py`.
- Added backend unit coverage for approved-ECO report generation, comments, review sign-off, and exports.

### Phase 19 - Production Infrastructure

- Added backend Dockerfile for FastAPI runtime.
- Added frontend Dockerfile and nginx config for serving the React build and proxying API/auth routes.
- Added production Compose file with Postgres, migration runner, backend, frontend, health checks, and persistent volumes.
- Added `.env.production.example`.
- Added `.dockerignore`.
- Added `/api/v1/ready` readiness endpoint with database connectivity check.
- Added GitHub Actions CI workflow for backend compile/tests, Alembic migration validation, frontend lint, and frontend build.
- Added production operations guide in `docs/PRODUCTION.md`.
- Added production npm scripts:
  - `npm run prod:build`
  - `npm run prod:up`
  - `npm run prod:down`
  - `npm run prod:logs`
- Documented backup, restore, deployment, security, and operational limits.

## Backend Endpoints

Public:

- `POST /register`
- `POST /login`
- `POST /logout`
- `GET /api/v1/health`
- `GET /api/v1/ready`

Protected:

- `GET /me`
- `POST /api/v1/uploads`
- `GET /api/v1/uploads`
- `POST /api/v1/bom/parse/{upload_id}`
- `POST /api/v1/graph/build/{upload_id}`
- `GET /api/v1/graph/{upload_id}/parents/{part_number}`
- `GET /api/v1/graph/{upload_id}/children/{part_number}`
- `GET /api/v1/graph/{upload_id}/paths?source={source}&target={target}`
- `GET /api/v1/graph/{upload_id}/stats`
- `POST /api/v1/eco/parse-text`
- `POST /api/v1/eco/parse-upload/{upload_id}`
- `POST /api/v1/intelligence/impact-report`
- `POST /api/v1/bom-imports/from-upload/{upload_id}`
- `GET /api/v1/bom-imports`
- `POST /api/v1/bom-imports/diff`
- `GET /api/v1/bom-imports/{import_id}`
- `DELETE /api/v1/bom-imports/{import_id}`
- `POST /api/v1/eco-records/parse-text`
- `POST /api/v1/eco-records/parse-upload/{upload_id}`
- `GET /api/v1/eco-records`
- `GET /api/v1/eco-records/{record_id}`
- `PATCH /api/v1/eco-records/{record_id}`
- `POST /api/v1/eco-records/{record_id}/review`
- `POST /api/v1/eco-records/{record_id}/approve`
- `POST /api/v1/eco-records/{record_id}/reject`
- `POST /api/v1/reports/impact-report`
- `GET /api/v1/reports`
- `GET /api/v1/reports/{report_id}`
- `GET /api/v1/reports/{report_id}/export.csv`
- `GET /api/v1/reports/{report_id}/export.pdf`
- `PATCH /api/v1/reports/{report_id}/review`
- `POST /api/v1/reports/{report_id}/comments`
- `DELETE /api/v1/reports/{report_id}`
- `POST /api/v1/jobs/bom-imports/from-upload/{upload_id}`
- `POST /api/v1/jobs/eco-records/parse-upload/{upload_id}`
- `POST /api/v1/jobs/graph/build/{upload_id}`
- `POST /api/v1/jobs/reports/impact-report`
- `GET /api/v1/jobs`
- `GET /api/v1/jobs/{job_id}`
- `POST /api/v1/documents/from-upload/{upload_id}`
- `GET /api/v1/documents`
- `GET /api/v1/documents/{document_id}`
- `GET /api/v1/documents/affected/{part_number}`

Authentication is also available under `/api/v1` through the API router for compatibility.

## Upload Constraints

Allowed file types:

- CSV: `.csv`
- Excel: `.xlsx`
- PDF: `.pdf`

Default maximum upload size:

- `25 MB`

Configurable environment variables:

- `UPLOAD_DIRECTORY`
- `MAX_UPLOAD_SIZE_MB`

Upload categories:

- `bom`
- `eco`
- `document`

Upload metadata stored:

- uploader user id
- original filename
- stored filename
- extension
- MIME type
- size in bytes
- storage path
- category
- status
- created timestamp

## BOM Parser

Supported input files:

- `.csv`
- `.xlsx`

Required normalized field:

- `part_number`

Optional normalized fields:

- `description`
- `parent_assembly`
- `child_assembly`
- `revision`

The parser supports common column aliases such as `Part Number`, `part_no`, `Item No`, `Description`, `desc`, `Parent Assembly`, `parent`, `Child Assembly`, `child`, `Revision`, `rev`, and `Version`.

Current parser behavior:

- Parses already uploaded files by upload id.
- Ensures the upload belongs to the authenticated user.
- Rejects non-CSV/XLSX files.
- Skips rows without a part number.
- Returns structured rows through the API.
- Does not persist normalized BOM rows yet.

## Dependency Graph

Graph library:

- NetworkX

Graph direction:

- `parent_assembly -> child_assembly`
- `child_assembly -> part_number` when both values exist and differ
- fallback: `parent_assembly -> part_number`

Graph endpoint behavior:

- Rebuilds graph on demand from uploaded CSV/XLSX files.
- Requires the upload to belong to the authenticated user.
- Returns parents with NetworkX ancestors.
- Returns children with NetworkX descendants.
- Returns simple dependency paths between source and target nodes.
- Returns graph statistics:
  - node count
  - edge count
  - root count
  - leaf count
  - cycle presence

Persistence behavior:

- Graphs can be rebuilt on demand.
- Graph snapshots are persisted when a BOM import is created.

## BOM Versioning and Diffing

Current behavior:

- Each normalized BOM import gets a simple version label such as `v1`, `v2`, or `v3` for the same active filename.
- Imports can be compared through the BOM Compare page or `/api/v1/bom-imports/diff`.
- Diff output includes:
  - added parts
  - removed parts
  - revised parts
  - possible replacement candidates
  - unchanged count

Replacement candidates are deterministic hints based on shared parent assembly, shared child assembly, and description overlap. They are not yet human-approved engineering decisions.

## Engineering Change Parser

Supported inputs:

- Plain text
- Uploaded PDF

Extracted fields:

- `change_type`
- `old_part`
- `new_part`
- `reason`
- `effective_date`

LLM abstraction:

- `BaseLLMProvider` defines the provider contract.
- `RuleBasedLLMProvider` is the current local implementation.
- Future providers can implement the same interface without changing API routes.

Current behavior:

- Plain text is parsed directly through `/api/v1/eco/parse-text`.
- Uploaded PDFs are loaded by upload id and must belong to the authenticated user.
- PDF parsing extracts text only before structured ECO parsing.
- Impact reports are not generated in this phase.

## ECO Review Workflow

Current workflow statuses:

- `draft`
- `reviewed`
- `approved`
- `rejected`

Current behavior:

- Parsed ECO fields can be manually corrected after parsing.
- Saving corrections marks the ECO as `reviewed`.
- Users can mark reviewed, approve, or reject ECO records.
- Approval and rejection notes are persisted.
- Review, approval, and rejection timestamps are persisted.

Current behavior:

- Report generation can use raw ECO text or a selected approved ECO record.

## Intelligence Layer

Input:

- Parsed BOM rows.
- Dependency graph.
- Parsed ECO.

Output:

- Structured impact report.
- Affected assemblies.
- Affected downstream record categories.
- Risk assessment.
- Suggested updates.

Downstream record categories:

- procurement
- installation guides
- commissioning procedures
- service manuals

Risk logic:

- High-impact change types: replacement, obsolescence, removal.
- Medium-impact change types: revision, addition.
- Risk score increases with affected parent/child graph scope, downstream record categories, and effective date presence.

Persistence behavior:

- The legacy intelligence endpoint still returns a transient report.
- `/api/v1/reports/impact-report` generates and persists saved reports.

## Downstream Document Intelligence

Supported input files:

- PDF engineering documents uploaded with category `document`

Indexed document types:

- installation guides
- commissioning procedures
- service manuals
- procurement records
- generic engineering documents

Current behavior:

- Extracts PDF text.
- Splits text into titled sections.
- Detects part references such as `PN-1212`, `PN 1212`, `ASM-1000`, and similar part-like identifiers.
- Persists each indexed document and section.
- Archives the older indexed document when the same upload is re-indexed.
- Lets users inspect indexed document sections in the frontend.
- Lets saved reports include exact downstream document sections when those sections reference the ECO old or new part.

Current limitation:

- Document parsing is deterministic text extraction and regex matching. It does not yet use semantic LLM matching or manual review/approval.

## Security Decisions

- Passwords are hashed with bcrypt.
- JWTs are stored in an HttpOnly cookie named `access_token`.
- Frontend JavaScript does not store JWTs in localStorage or sessionStorage.
- Cookies use `SameSite=Lax`.
- Cookie `Secure` is enabled automatically in staging and production environments.
- Production startup rejects the default development JWT secret.
- Protected backend routes require authentication middleware and current-user dependency checks.
- Uploaded filenames are not trusted for storage names; the backend generates UUID-based stored filenames.
- Upload validation happens server-side even though the frontend also validates before upload.
- Empty files are rejected.
- Oversized files are rejected and partially written files are removed.

## Out of Scope So Far

- Semantic LLM matching for downstream document sections.
- Visual frontend dependency graph rendering.
- Durable external worker queue such as Celery/RQ/Arq.
- Password reset and email verification flows.
- Server-side token revocation.
- Role-based access control.
- Team-wide report visibility and share links.
- Virus scanning.
- Advanced MIME/content sniffing.
- Object storage such as S3.

## Remaining Implementation Roadmap

### Phase 20 - End-to-End QA and Release Readiness

Goal: validate the complete application workflow.

Tasks:

- Add end-to-end tests for login, upload BOM, parse BOM, upload/parse ECO, generate report, view report.
- Add realistic fixtures for BOM CSV, BOM XLSX, ECO PDFs, and manuals.
- Add performance testing for larger BOMs.
- Add accessibility audit.
- Add security review checklist.
- Add release checklist.

Definition of done:

- The application is ready for pilot users with a documented set of known limitations.

## Recommended Next Phase

Proceed with Phase 20: End-to-End QA and Release Readiness.
