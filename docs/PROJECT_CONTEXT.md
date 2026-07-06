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
  FastAPI + SQLAlchemy + Alembic + SQLite for local MVP development
```

The frontend and backend run independently. The frontend calls protected backend APIs with cookie-based authentication.

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
- Kept data in `frontend/src/data/dashboardData.ts` so future API integration can replace placeholder data cleanly.

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

## Backend Endpoints

Public:

- `POST /register`
- `POST /login`
- `POST /logout`
- `GET /api/v1/health`

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

Current limitation:

- Graphs are not persisted or cached yet.

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

Current limitation:

- Impact reports are returned through the API but not persisted yet.

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

- Manual/service/installation/commissioning document parsing.
- Exact downstream document section matching.
- External AI/LLM provider integration.
- Persisted impact report history.
- Persisted normalized BOM records.
- Persisted dependency graph snapshots.
- Frontend integration for graph/report APIs.
- Server-side token revocation.
- Virus scanning.
- Object storage such as S3.

## Remaining Implementation Roadmap

### Phase 11 - Persistence for Normalized BOMs, Graphs, ECOs, and Reports

Goal: move from on-demand parsing/report generation to persisted application data.

Backend tasks:

- Store normalized parts and assembly relationships.
- Store parsed BOM import batches.
- Store parsed ECO records.
- Store dependency graph nodes and edges or graph snapshots.
- Store generated impact reports for the Reports page.
- Add Alembic migrations for normalized BOM, ECO, graph, and report tables.
- Add report history and report detail endpoints.
- Add delete/archive behavior for uploads, parsed data, and reports.

Frontend tasks:

- Connect Reports page to saved report history.
- Add report detail view.
- Show parsed BOM import status.
- Show parsed ECO records.

Definition of done:

- Reports survive server restarts.
- Users can revisit generated reports.
- Graph data can be reused without reparsing the original file on every request.

### Phase 12 - Frontend Data Integration

Goal: connect existing frontend pages to real backend APIs.

Tasks:

- Connect dashboard cards to upload/report/activity APIs.
- Connect Upload BOM page to parse preview and normalized import results.
- Connect Upload ECO page to ECO parsing and structured field preview.
- Connect Dependency Graph page to graph APIs.
- Connect Reports page to persisted reports.
- Add consistent loading, empty, error, retry, and success states.
- Add frontend API client structure by domain.

Definition of done:

- The main navigation pages display real user data instead of placeholders.
- Users can complete a basic workflow from upload to report in the UI.

### Phase 13 - Background Jobs and Processing Pipeline

Goal: support larger files and longer-running parsing/analysis safely.

Tasks:

- Add job model for upload parsing, graph construction, ECO parsing, and report generation.
- Add job statuses: queued, processing, completed, failed.
- Add background worker approach such as Celery/RQ/Arq/FastAPI background tasks for MVP.
- Add job status endpoints.
- Add retry and failure metadata.
- Move heavy parsing/report generation out of request-response paths.

Definition of done:

- Large uploads do not block API requests.
- Users can see processing progress and failure reasons.

### Phase 14 - Security Hardening

Goal: strengthen production security posture.

Tasks:

- Add CSRF protection for cookie-authenticated mutation endpoints.
- Add rate limiting for auth and upload endpoints.
- Add password reset flow.
- Add email verification.
- Add server-side logout/token revocation strategy.
- Add role-based access control.
- Add audit logging for login, logout, uploads, parsing, graph generation, and report generation.
- Add virus scanning for uploaded files.
- Improve MIME/content sniffing beyond extension/content-type checks.
- Add secure object storage option such as S3, Azure Blob, or GCS.

Definition of done:

- The app has a documented security model and mitigates common auth/upload risks.

### Phase 15 - AI Provider Integration

Goal: replace or augment the rule-based ECO provider with real provider-backed extraction.

Tasks:

- Implement an external provider behind `BaseLLMProvider`.
- Add provider configuration and secrets management.
- Add prompt templates and versioning.
- Add model fallback behavior.
- Add provider timeout/retry handling.
- Add structured output validation.
- Keep deterministic fallback for local development and resilience.

Definition of done:

- ECO parsing can use a real LLM provider without changing API routes or business workflows.

### Phase 16 - Downstream Document Intelligence

Goal: identify exact downstream documents and sections affected by engineering changes.

Tasks:

- Add models for procurement records, installation guides, commissioning procedures, and service manuals.
- Upload and parse engineering documentation.
- Extract document sections and part references.
- Link parts and assemblies to document sections.
- Identify exact sections needing updates.
- Generate structured recommended changes per downstream artifact.

Definition of done:

- Impact reports can name the real downstream records and sections that need review.

### Phase 17 - Advanced BOM and ECO Workflows

Goal: support realistic engineering operations beyond single-file analysis.

Tasks:

- Add BOM versioning.
- Add BOM-to-BOM diffing.
- Detect added, removed, replaced, and revised parts between BOM versions.
- Add ECO versioning and approval states.
- Add manual correction workflow for parsed ECO fields.
- Add field-level confidence and validation warnings.
- Add user approval/rejection of suggested updates.

Definition of done:

- Users can manage iterative engineering change workflows, not only one-off analysis.

### Phase 18 - Reporting, Export, and Collaboration

Goal: make impact reports usable by real teams.

Tasks:

- Add PDF export.
- Add CSV/Excel export.
- Add report sharing links or team visibility controls.
- Add comments and review workflow.
- Add report comparison/versioning.
- Add sign-off statuses and ownership.

Definition of done:

- Reports can be reviewed, shared, exported, and tracked through a decision workflow.

### Phase 19 - Production Infrastructure

Goal: make the system deployable and maintainable.

Tasks:

- Add Dockerfiles for frontend and backend.
- Add docker-compose for local full-stack development.
- Add PostgreSQL production setup.
- Add deployment configuration.
- Add CI pipeline for lint, tests, build, and migrations.
- Add structured logging and error monitoring integration.
- Add health and readiness endpoints.
- Add backup and retention strategy for database and uploaded files.
- Add environment-specific configuration documentation.

Definition of done:

- A new developer can run the full app locally.
- The app can be deployed with documented production settings.

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

Proceed with Phase 11: Persistence for Normalized BOMs, Graphs, ECOs, and Reports.
