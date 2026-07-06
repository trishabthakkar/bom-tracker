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

- PDF text extraction.
- External AI/LLM provider integration.
- Impact report generation from real data.
- Server-side token revocation.
- Virus scanning.
- Object storage such as S3.

## Next Logical Phase

Phase 9 should persist normalized BOM data and graph snapshots:

- Store normalized parts and assembly relationships.
- Prepare dependency graph tables for later analysis.
- Use persisted data to power the frontend Dependency Graph page.
