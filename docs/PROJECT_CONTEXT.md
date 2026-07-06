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

- BOM parsing.
- Excel parsing.
- PDF text extraction.
- ECO interpretation.
- Dependency graph construction.
- AI/LLM services.
- Impact report generation from real data.
- Server-side token revocation.
- Virus scanning.
- Object storage such as S3.

## Next Logical Phase

Phase 6 should implement BOM parsing and normalization:

- Parse CSV/XLSX files.
- Detect required columns.
- Preview parsed rows.
- Store normalized parts and assembly relationships.
- Prepare dependency graph tables for later analysis.
