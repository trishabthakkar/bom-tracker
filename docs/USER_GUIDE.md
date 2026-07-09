# AI-Assisted BOM Change Intelligence Layer - User Guide

This guide explains every current feature in the MVP, how to use it, and how it works behind the scenes.

## What The App Does

The application helps analyze engineering changes and understand downstream impact across BOM structures, assemblies, parts, and future engineering documentation.

Current MVP capabilities:

- User registration and login.
- Secure authenticated file uploads.
- BOM upload history.
- CSV/XLSX BOM parsing and persisted normalized BOM imports.
- Dependency graph construction through the backend API.
- Plain-text and PDF ECO parsing, with persisted text ECO records.
- Deterministic saved impact report generation.
- Engineering dashboard with real upload, report, import, and ECO activity data.
- Frontend report generation, ECO upload parsing, and dependency graph exploration.

Important current limitation:

- The dependency graph page is data-driven, but it is not yet a full interactive node-link canvas.

## How To Run The App

Start PostgreSQL:

```bash
cd /home/trishabimalthakkar/bom-tracker
sudo docker compose up -d postgres
```

Run database migrations:

```bash
npm run db:migrate
```

Start the backend:

```bash
npm run backend:dev
```

Start the frontend in another terminal:

```bash
npm run dev
```

Open the app:

```text
http://localhost:5173/
```

Backend API docs are available at:

```text
http://localhost:8000/docs
```

## Database

The app uses PostgreSQL for local development.

Default database URL:

```text
postgresql+psycopg://bom_tracker:bom_tracker_password@localhost:5432/bom_tracker
```

Docker Compose creates:

- database: `bom_tracker`
- user: `bom_tracker`
- password: `bom_tracker_password`
- container: `bom-tracker-postgres`

Tables are created by Alembic migrations.

Current persisted tables:

- `users`
- `uploaded_files`
- `bom_imports`
- `bom_parts`
- `assembly_relationships`
- `eco_records`
- `graph_snapshots`
- `impact_reports`
- `jobs`
- Alembic migration version table

## Authentication

### How To Use It

1. Open the frontend.
2. Select register.
3. Enter full name, email, and password.
4. After successful signup, the app logs you in and opens the dashboard.
5. Use logout from the top navigation when finished.

Existing users can use the login page with email and password.

### How It Works

The backend exposes:

```text
POST /register
POST /login
POST /logout
GET  /me
```

Security behavior:

- Passwords are hashed with bcrypt.
- JWT access tokens are stored in an HttpOnly cookie named `access_token`.
- Frontend JavaScript does not store the token in localStorage or sessionStorage.
- Protected routes call `/me` to recover the current session.
- Unauthenticated users are redirected to `/login`.
- Cookies use `SameSite=Lax`.
- Secure cookies are enabled automatically outside local development.
- Cookie-authenticated mutation requests require a matching CSRF cookie and `X-CSRF-Token` header.
- Login/register and authenticated mutation routes have in-memory rate limits for local MVP protection.
- Security headers are added to responses to reduce browser-side attack surface.
- Auth, upload, and background job creation events are written to audit logs.

If PostgreSQL is not running, signup/login will show:

```text
Database unavailable. Please start PostgreSQL and run migrations.
```

## Application Shell

### How To Use It

After logging in, the main app includes:

- collapsible sidebar
- top navigation bar
- footer
- dark mode toggle
- notifications icon
- settings icon
- user avatar
- logout button

Sidebar pages:

- Dashboard
- Upload BOM
- Upload ECO
- Reports
- Dependency Graph
- History
- Settings

### How It Works

React Router controls page navigation. The app shell is protected by authentication, so route content is only shown after `/me` confirms a valid session.

The layout is componentized into:

- `Sidebar`
- `Navbar`
- `Footer`
- `Layout`

## Dashboard

### How To Use It

Open:

```text
/
```

The dashboard shows:

- metric cards
- recent uploads
- recent reports
- quick actions
- recent activity

Use quick actions to move to upload, report, and dependency graph areas.

### How It Works

The dashboard calls the authenticated backend APIs for:

- upload history
- saved BOM imports
- saved ECO records
- saved impact reports

It combines those records into operational metrics, recent upload rows, report summaries, and recent activity. If an API request fails, the page shows an error state with a retry action.

## Upload BOM

### How To Use It

Open:

```text
/upload-bom
```

Accepted files:

- `.csv`
- `.xlsx`

Steps:

1. Drag a BOM file into the upload area, or click to select a file.
2. Confirm the selected filename appears.
3. Leave `Replace files with the same name` checked when the new file should become the active copy.
4. Click `Upload securely`.
5. Watch the progress bar.
6. After upload completes, the frontend queues a background BOM import job.
7. Watch the job status panel until the import completes or fails.
8. Review the latest normalized BOM summary and saved BOM imports list.

### How It Works

The frontend sends the file to:

```text
POST /api/v1/uploads
```

The upload is sent as `multipart/form-data` with:

- `file`
- `upload_category=bom`
- `replace_existing=true` when the replacement checkbox is enabled

The backend:

- verifies the user is authenticated
- validates file extension and MIME type
- enforces file size limits
- rejects empty files
- generates a safe stored filename
- saves the file under the backend upload directory
- marks older uploads with the same filename and category as `replaced` when replacement is enabled
- archives older BOM imports and reports connected to the replaced upload when possible
- stores upload metadata in PostgreSQL

The upload page also calls:

```text
GET /api/v1/uploads
```

and filters the result to show BOM uploads.

After upload, the page calls:

```text
POST /api/v1/jobs/bom-imports/from-upload/{upload_id}
```

The job status is polled through:

```text
GET /api/v1/jobs/{job_id}
```

When the job completes, it persists:

- normalized BOM import batch
- normalized BOM part rows
- assembly relationships
- dependency graph snapshot

## Upload ECO

### How To Use It

Open:

```text
/upload-eco
```

Accepted files:

- `.pdf`

Steps:

1. Drag an ECO PDF into the upload area, or click to select it.
2. Leave `Replace files with the same name` checked when the new PDF should become the active copy.
3. Click `Upload securely`.
4. The frontend queues a background ECO PDF parsing job.
5. Watch the job status panel until parsing completes or fails.
6. Review the saved ECO record list below the upload area.

### How It Works

The frontend uses the same upload system as BOM uploads, but sends:

```text
upload_category=eco
```

The upload is stored and tracked exactly like BOM files. After upload, the page calls:

```text
POST /api/v1/jobs/eco-records/parse-upload/{upload_id}
```

That queues a background job. The job extracts text from the PDF, parses structured ECO fields, and persists the ECO record.

The page also includes a plain-text ECO parser. Paste or edit ECO text and click `Save parsed ECO` to persist extracted fields.

## Upload History

### How To Use It

Upload history appears on the upload pages after login.

It shows uploaded files for the current user, including:

- original filename
- extension
- file size
- category
- status
- upload time

### How It Works

The backend stores upload metadata in `uploaded_files`.

The frontend requests:

```text
GET /api/v1/uploads
```

Only files owned by the current authenticated user are returned.

Uploads marked `replaced` are hidden from normal upload history and downstream selectors so duplicate filenames do not clutter active workflows.

## BOM Parser

### How To Use It

Open:

```text
/dependency-graph
```

Select a normalized BOM import from the dropdown. The page builds graph data from the selected BOM upload and shows:

- graph statistics
- whether cycles were detected
- a part lookup for affected parents and children
- graph edges in table form

You can enter a part number or assembly id, then run lookup to see connected upstream and downstream nodes.

The same data is also available through the backend API.

First upload a BOM through the UI or API. Then parse it with:

```text
POST /api/v1/bom/parse/{upload_id}
```

Example response fields:

- `upload_id`
- `filename`
- `row_count`
- `rows`

Each parsed row contains:

- `row_number`
- `part_number`
- `description`
- `parent_assembly`
- `child_assembly`
- `revision`

### How It Works

The parser supports CSV and XLSX files.

It normalizes common BOM column names such as:

- `Part Number`
- `part_no`
- `Item No`
- `Description`
- `desc`
- `Parent Assembly`
- `parent`
- `Child Assembly`
- `child`
- `Revision`
- `rev`
- `Version`

Rows without a part number are skipped. Parsed BOM rows can be returned through the parser API and can also be persisted through the BOM import API.

## Dependency Graph

### How To Use It

This feature is currently available through the backend API.

Build graph data from an uploaded BOM:

```text
POST /api/v1/graph/build/{upload_id}
```

Find parent assemblies affected by a part:

```text
GET /api/v1/graph/{upload_id}/parents/{part_number}
```

Find downstream children affected by a node:

```text
GET /api/v1/graph/{upload_id}/children/{part_number}
```

Find dependency paths:

```text
GET /api/v1/graph/{upload_id}/paths?source={source}&target={target}
```

Get graph statistics:

```text
GET /api/v1/graph/{upload_id}/stats
```

### How It Works

The backend uses NetworkX to build a directed graph from parsed BOM rows.

Graph direction:

```text
parent_assembly -> child_assembly
child_assembly  -> part_number
```

If no child assembly exists, the fallback edge is:

```text
parent_assembly -> part_number
```

The graph can be rebuilt on demand from the uploaded file. Graph snapshots are also persisted when a BOM import is created.

The current frontend graph explorer is intentionally table/list based for the MVP. A richer visual graph canvas is planned later.

## Engineering Change Parsing

### How To Use It

Parse plain text ECO input:

```text
POST /api/v1/eco/parse-text
```

Request body:

```json
{
  "text": "Replace old part PN-100 with new part PN-200. Reason: supplier obsolescence. Effective date: 2026-08-15."
}
```

Parse an uploaded ECO PDF:

```text
POST /api/v1/eco/parse-upload/{upload_id}
```

Returned fields:

- `change_type`
- `old_part`
- `new_part`
- `reason`
- `effective_date`
- `source`
- `confidence`

### How It Works

The current parser uses a provider abstraction:

- `BaseLLMProvider` defines the interface.
- `RuleBasedLLMProvider` provides local deterministic parsing.
- `OpenAILLMProvider` can call OpenAI for structured ECO extraction when configured.

The default provider is still `rule_based`, so the MVP remains usable without API keys.

To enable OpenAI-backed parsing, configure:

```text
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4.1-mini
LLM_TIMEOUT_SECONDS=20
LLM_FALLBACK_TO_RULE_BASED=true
```

When fallback is enabled, the backend returns to deterministic rule-based parsing if the remote provider fails.

For PDFs, the backend extracts text first, then sends that text to the same parser.

## Intelligence Layer

### How To Use It

This feature is currently available through the backend API.

Generate an impact report:

```text
POST /api/v1/intelligence/impact-report
```

Request body:

```json
{
  "bom_upload_id": 1,
  "eco_text": "Replace old part PN-100 with new part PN-200. Reason: supplier obsolescence. Effective date: 2026-08-15."
}
```

The response contains:

- summary
- parsed ECO
- affected part
- effective date
- affected assemblies
- downstream records
- suggested updates
- risk assessment

### How It Works

The backend:

1. Loads the uploaded BOM.
2. Parses the BOM into structured rows.
3. Builds a NetworkX dependency graph.
4. Parses the ECO text.
5. Finds affected parents, children, and dependency paths.
6. Generates downstream record impacts.
7. Produces a risk score and risk level.
8. Returns a structured impact report.

Downstream categories currently considered:

- procurement
- installation guides
- commissioning procedures
- service manuals

Saved reports are persisted in PostgreSQL and visible in the Reports page.

## Reports Page

### How To Use It

Open:

```text
/reports
```

The page supports:

- generating a saved impact report from a selected normalized BOM import and ECO text
- listing saved reports
- opening report detail pages

Steps:

1. Upload and import a BOM.
2. Open Reports.
3. Select the normalized BOM import.
4. Enter ECO text.
5. Click `Generate`.
6. Watch the impact report job status panel.
7. Open the saved report from the list after the job completes.

### How It Works

Report generation is queued through:

```text
POST /api/v1/jobs/reports/impact-report
```

The frontend polls job status until the report is generated or a failure message is available.

## Dependency Graph Page

### How To Use It

Open:

```text
/dependency-graph
```

The page shows real graph data from the backend. It is currently optimized for inspection through metrics, lookup results, and an edge table. A future phase can add an interactive visual node-link graph.

Manual graph builds are queued through:

```text
POST /api/v1/jobs/graph/build/{upload_id}
```

After the graph build job completes, the page refreshes graph statistics, edge data, and lookup tools.

## Background Jobs

### How To Use It

You do not need to open a separate page for jobs. Job status panels appear inside workflows that may take longer:

- BOM import after upload
- ECO PDF parsing after upload
- dependency graph build
- impact report generation

Each panel shows:

- job id
- status
- progress bar
- status message
- failure message if something goes wrong

### How It Works

The backend stores jobs in the `jobs` table with these statuses:

- `queued`
- `processing`
- `completed`
- `failed`

The MVP worker uses FastAPI `BackgroundTasks`. This keeps long-running work out of the initial API response while avoiding a separate worker dependency during local development.

## History Page

### How To Use It

Open:

```text
/history
```

### Current Status

This page is a placeholder.

### Planned Behavior

History will eventually show upload, parsing, graph, ECO, and report generation events.

## Settings Page

### How To Use It

Open:

```text
/settings
```

### Current Status

This page is a placeholder.

### Planned Behavior

Settings will eventually support user preferences, organization settings, AI provider configuration, and security settings.

## Dark Mode

### How To Use It

Click the sun/moon icon in the top navigation bar.

### How It Works

The frontend toggles the app theme by updating the document class and applying Tailwind dark-mode styles.

## Notifications

### How To Use It

The notifications icon appears in the top navigation bar.

### Current Status

It is currently visual only.

### Planned Behavior

It may later show upload completion, parsing failures, risk report readiness, or approval workflow events.

## API Error Handling

### How To Use It

Most users experience this through visible error messages in the frontend.

Common messages:

- `API unavailable. Confirm the backend is running on http://localhost:8000.`
- `Database unavailable. Please start PostgreSQL and run migrations.`
- `An account with this email already exists.`
- `Invalid email or password.`

### How It Works

The backend has a shared API error contract:

```json
{
  "error": {
    "code": "database_unavailable",
    "message": "Database unavailable. Please start PostgreSQL and run migrations.",
    "path": "/register"
  }
}
```

The frontend auth client reads both:

- FastAPI `detail` errors
- app-level `error.message` responses

This prevents generic browser errors from hiding the real backend problem.

## Troubleshooting

### Signup Says Database Unavailable

PostgreSQL is not running or migrations have not been applied.

Run:

```bash
cd /home/trishabimalthakkar/bom-tracker
sudo docker compose up -d postgres
npm run db:migrate
npm run backend:dev
```

### Signup Says API Unavailable

The backend is not running.

Run:

```bash
npm run backend:dev
```

Then test:

```bash
curl http://localhost:8000/api/v1/health
```

Expected:

```json
{"status":"ok"}
```

### Docker Permission Error

If Docker says permission denied, run Docker with sudo:

```bash
sudo docker compose up -d postgres
```

### Migrations Fail Immediately After Starting Postgres

PostgreSQL may still be initializing.

Run:

```bash
sudo docker compose exec postgres pg_isready -U bom_tracker -d bom_tracker
```

Wait until it says:

```text
accepting connections
```

Then run:

```bash
npm run db:migrate
```

### Frontend Opens On A Different Port

Vite usually opens:

```text
http://localhost:5173/
```

If that port is busy, it may use:

```text
http://localhost:5174/
```

Both are allowed by backend CORS config.

## Current MVP Limitations

- Dependency graph data is shown through metrics, lookup lists, and edge tables, not a full interactive graph canvas yet.
- No PDF export, report sharing, approval workflow, or team permissions yet.
- Background jobs use FastAPI in-process workers for MVP; a production queue such as Celery, RQ, or Arq is not connected yet.
- Password reset, email verification, server-side token revocation, RBAC, and virus scanning are not implemented yet.

## Recommended Next Phases

Phase 16 should add downstream document intelligence for procurement records, installation guides, commissioning procedures, and service manuals.
