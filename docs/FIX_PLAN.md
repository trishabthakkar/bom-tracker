# Fix Plan (Phases 21-29)

Remediation plan from the whole-project review on 2026-08-03.

Phases are ordered by dependency, not by severity. Phase 21 comes first because until
configuration loads deterministically, no later fix can be trusted to have been exercised.
Each phase is intended to be one commit, matching the existing `phase N` convention.

Every measured value in this document was produced by running the code, not by inspection.

## Status Summary

| Phase | Scope | Blocking? | Status |
| --- | --- | --- | --- |
| 21 | Deterministic configuration and local database | Yes | Done (2026-08-03) |
| 22 | Dependency graph edge direction | Yes | Done (2026-08-04) |
| 23 | Bound dependency path enumeration | No | Done (2026-08-05) |
| 24 | Unblock production deploy and CI | Yes | Done (2026-08-05) |
| 25 | Middleware ordering / rate limiting | No | Not started |
| 26 | Timezone-aware timestamps | No | Not started |
| 27 | Consolidate test fixtures | No | Not started |
| 28 | Remove rot | No | Not started |
| 29 | Consolidate workflow and docs | No | Not started |

Phases 21, 22, and 24 are the ones that change whether the project works. If only three
are done, do those.

## Baseline (verified 2026-08-03)

What already passes and must keep passing:

- `pytest` - 42 passed
- `npm run lint` - clean
- `tsc -b` - clean
- `scripts/e2e_api_workflow.py` - full workflow green against a live backend
- Alembic migrations - apply cleanly against PostgreSQL

---

## Phase 21 - Make configuration and the local database deterministic

### Problem

`npm run backend:dev` silently ignores `backend/.env`. `SettingsConfigDict(env_file=".env")`
resolves against the current working directory; the npm scripts run from the repository
root while the README instructs `cd backend`. Demonstrated by adding a marker to
`backend/.env`:

```text
from repo root (backend:dev, backend:test, qa:perf) -> app_name = AI-Assisted BOM Change Intelligence Layer
from backend/   (README, db:migrate, db:reset-data) -> app_name = LOADED-FROM-BACKEND-DOTENV
```

`db:migrate` reads the configured settings while `backend:dev` uses hardcoded defaults.
`DATABASE_URL`, `JWT_SECRET_KEY`, `LLM_PROVIDER`, and `OPENAI_API_KEY` are all dropped by
the dev server.

Separately, `docker-compose.yml` hardcodes host port `5432`. Where a native PostgreSQL
already owns that port, `npm run db:up` reports the container healthy while `db:migrate`
fails with `role "bom_tracker" does not exist` - the container is running but shadowed.

### Changes

1. `backend/app/core/config.py:37` - anchor the env file to the source tree:

   ```python
   from pathlib import Path

   BACKEND_ROOT = Path(__file__).resolve().parents[2]

   model_config = SettingsConfigDict(
       env_file=BACKEND_ROOT / ".env", env_file_encoding="utf-8"
   )
   ```

   `parents[2]` resolves to `backend/`. Inside the container it resolves to `/app/.env`,
   which does not exist; pydantic-settings tolerates a missing env file and falls through
   to real environment variables, so the production path is unaffected.

2. `docker-compose.yml:9` - stop hardcoding the host port:

   ```yaml
   ports:
     - "${POSTGRES_PORT:-5432}:5432"
   ```

3. `.env.example` (repository root, new file) - add `POSTGRES_PORT=5432`. `npm run db:up`
   runs `docker compose up -d postgres` with no `--env-file` flag, so Compose auto-loads a
   root-level `.env` for variable substitution - not `backend/.env`. Confirmed by testing:
   with `.env` absent, `${POSTGRES_PORT:-5432}` falls back to 5432; with root `.env`
   containing `POSTGRES_PORT=55432`, only port 55432 is published. On a machine with a
   native PostgreSQL already on 5432, copy this file to `.env` with `POSTGRES_PORT=55432`,
   and also update the port inside `DATABASE_URL` in `backend/.env` to match.

4. `package.json` - run every backend script from the same directory:

   ```json
   "backend:dev":  "cd backend && .venv/bin/uvicorn app.main:app --reload",
   "backend:test": "cd backend && .venv/bin/pytest",
   "qa:perf":      "cd backend && PYTHONPATH=. .venv/bin/python ../scripts/performance_smoke.py",
   ```

### Watch for

After this change `pytest` loads `backend/.env` where it previously loaded nothing. The
tests build their own in-memory SQLite engines and do not read `DATABASE_URL`, but confirm
that holds - a test that picks up `app.db.session` would now point at the real database.

### Verification

```bash
printf '\nAPP_NAME=MARKER\n' >> backend/.env
npm run backend:test
cd backend && PYTHONPATH=. .venv/bin/python -c "from app.core.config import settings; print(settings.app_name)"
```

`MARKER` must print from both the repository root and from `backend/`. Restore
`backend/.env` afterwards.

### Result (2026-08-03)

Implemented and verified:

- `backend/app/core/config.py` - `env_file` anchored to `BACKEND_ROOT / ".env"`.
- `docker-compose.yml` - `ports: ["${POSTGRES_PORT:-5432}:5432"]`.
- `.env.example` (root, new) - documents `POSTGRES_PORT`.
- `package.json` - `backend:dev`, `backend:test`, `qa:perf` now `cd backend &&` first.

Verification performed:

- `APP_NAME=MARKER` in `backend/.env` was read identically from the repo root and from
  `backend/`, from both a raw Python import and `npm run backend:test` (42 passed).
- Reproduced the port-shadowing bug directly: with the container already reporting
  `0.0.0.0:5432->5432/tcp` as healthy, `psql -h 127.0.0.1 -p 5432` returned
  `FATAL: role "bom_tracker" does not exist` - confirming 5432 was silently routing to a
  native PostgreSQL install, not the container.
- With root `.env` set to `POSTGRES_PORT=55432`, `npm run db:up` published only
  `0.0.0.0:55432->5432/tcp` (no accidental 5432 collision), `alembic upgrade head` reached
  `20260709_0007 (head)`, and `npm run backend:dev` served `/api/v1/health` correctly from
  a completely clean process start.
- `npm run qa:perf` ran correctly from the repo root via the new `cd backend &&` form.
- Full re-check after all changes: `pytest` 42 passed, `npm run lint` clean, `tsc -b` clean.

---

## Phase 22 - Correct the dependency graph edge direction

### Problem

`backend/app/services/dependency_graph.py:39` adds `child_assembly -> part_number`, making
a part a descendant of its own child, and never adds the direct `parent_assembly -> part_number`
edge. Measured against the shipped demo file:

```text
stats: node_count=25 edge_count=25 root_count=0 leaf_count=19 has_cycles=True
cycles found: [['ASM-1100', 'ASM-1000', 'ASM-1110']]
ASM-1000 (the top-level assembly) ancestors -> ['ASM-1100', 'ASM-1110']
PN-1111 (a leaf part)             descendants -> []
```

The Dependency Graph page displays `Roots 0` and `Cycles: Detected` on a clean tree BOM.
Every affected-parents/children list and every impact report is computed on inverted
topology.

### Changes

1. `backend/app/services/dependency_graph.py:26-43` - replace the edge block. A row means
   "`part_number` sits under `parent_assembly` and contains `child_assembly`":

   ```python
   for row in rows:
       graph.add_node(row.part_number)

       if row.parent_assembly and row.parent_assembly != row.part_number:
           graph.add_node(row.parent_assembly)
           graph.add_edge(row.parent_assembly, row.part_number)

       if row.child_assembly and row.child_assembly != row.part_number:
           graph.add_node(row.child_assembly)
           graph.add_edge(row.part_number, row.child_assembly)
   ```

   The `!= row.part_number` guards prevent a self-referential row creating a 1-node cycle.

2. `backend/app/tests/test_dependency_graph.py` - the current fixture gives every row a
   non-empty `parent_assembly`, which is precisely why it never caught this. The inversion
   only fires on a row with a blank parent, the shape used by the top-level assembly in
   `demo-bom-v2.csv`. Add such a row and update expectations to these measured values:

   | Assertion | Expected |
   | --- | --- |
   | `edges` | `ROOT->P-100, P-100->A-100, A-100->P-200, P-200->C-200, C-200->P-300` |
   | `node_count` / `edge_count` | `6` / `5` |
   | `root_count` / `has_cycles` | `1` / `False` |
   | `get_affected_parents("P-300")` | `['A-100','C-200','P-100','P-200','ROOT']` |
   | `get_affected_children("ROOT")` | `['A-100','C-200','P-100','P-200','P-300']` |
   | `get_dependency_paths("ROOT","P-300")` | `[['ROOT','P-100','A-100','P-200','C-200','P-300']]` |

3. Add a regression test parsing `demo-files/demo-bom-v2.csv` and asserting `root_count == 1`
   and `has_cycles is False`. This is the case the unit fixture structurally cannot reach.

4. `README.md` - the Dependency Graph section documents the current, incorrect direction
   ("from child assembly to part number"). Rewrite as parent -> part -> child.

### Data note

Existing `graph_snapshots` rows and every persisted `impact_reports.report_json` were
computed with inverted edges. They will not error, they will be wrong. Either wipe with
`npm run db:reset-data` or accept pre-Phase-22 reports as historical.

### Verification

```bash
cd backend && PYTHONPATH=. .venv/bin/python -c "from app.services.bom_parser import parse_bom_file; from app.services.dependency_graph import build_dependency_graph, get_graph_statistics; print(get_graph_statistics(build_dependency_graph(parse_bom_file('../demo-files/demo-bom-v2.csv').rows)))"
```

Expected: `node_count=25 edge_count=24 root_count=1 leaf_count=16 has_cycles=False`.
The Dependency Graph page should then show `Roots 1` and no Cycles badge.

### Result (2026-08-04)

Implemented and verified:

- `backend/app/services/dependency_graph.py:26-41` - edge direction corrected as specified.
- `backend/app/tests/test_dependency_graph.py` - fixture updated to include a blank-parent
  top-level row, all five existing tests updated to the corrected expected values, plus a
  new `test_demo_bom_v2_has_single_root_and_no_cycles` regression test parsing the shipped
  demo file directly.
- `backend/app/tests/test_intelligence_layer.py:63` - one fixture-dependent assertion also
  assumed the old direction (`build_sample_graph`'s "Legacy pump" row is a genuine ancestor
  of the sensor beneath it once edges are corrected); updated to
  `["A-100", "PN-100", "ROOT"]`.
- `README.md` - Dependency Graph section rewritten to describe the corrected direction.

Verification performed:

- `pytest`: 43 passed (42 baseline + 1 new regression test).
- Restarted the dev backend and rebuilt the graph for `demo-bom-v2.csv` (upload id 2)
  through the live UI: **Nodes 25, Edges 24, Roots 1, Leaves 16, Cycles: None** - matching
  the predicted fix output exactly.
- Called the graph API directly with a real session: `GET /api/v1/graph/2/parents/ASM-1000`
  now returns `[]` (the true root has no parents, previously returned two fake ancestors);
  `GET /api/v1/graph/2/parents/PN-1111` now returns `["ASM-1000","ASM-1100","ASM-1110"]`
  (previously returned `[]`).

Known caveat: `graph_snapshots` and `impact_reports.report_json` rows created before this
fix (from the earlier review session's E2E run) still hold data computed with the old,
inverted edges. `npm run db:reset-data` clears these but also deletes all users, including
the `qa-1785739649@example.com` test account currently in use - deferred rather than run
without confirmation. Newly built graphs and newly generated reports are correct; anything
viewed from before 2026-08-04 is not.

---

## Phase 23 - Bound dependency path enumeration

Do this after Phase 22 so the cap is measured against correct topology.

### Problem

`backend/app/services/intelligence_layer.py:76` enumerates every simple path from every
ancestor via `nx.all_simple_paths`, and `report_persistence.py:165` stores the entire
result in one JSON column via `model_dump()`. Measured on a lattice BOM (one common part
under several assemblies - a normal BOM shape, not a pathological one):

```text
nodes=25  edges= 84  paths=      5,460  0.02s
nodes=33  edges=116  paths=     87,380  0.40s  json=  6.8 MB
nodes=41  edges=148  paths=  1,398,100  6.61s  json=132 MB
```

A 41-node BOM produces a 132 MB database row that is also shipped to the browser.
`scripts/performance_smoke.py` misses this entirely because its generated BOM is a shallow
tree and it only measures parse plus graph build.

### Changes

1. `backend/app/schemas/impact.py:14` - add two fields to `AffectedAssembly`:

   ```python
   dependency_path_count: int = 0
   dependency_paths_truncated: bool = False
   ```

   Both have defaults, so `StructuredImpactReport.model_validate()` still parses existing
   `report_json` rows. No backfill required.

2. `backend/app/services/intelligence_layer.py:74-78` - cap enumeration lazily:

   ```python
   MAX_DEPENDENCY_PATHS = 50

   path_iter = (
       path
       for parent in parents
       for path in get_dependency_paths(graph, parent, affected_part)
   )
   paths = [[str(n) for n in p] for p in islice(path_iter, MAX_DEPENDENCY_PATHS + 1)]
   truncated = len(paths) > MAX_DEPENDENCY_PATHS
   paths = paths[:MAX_DEPENDENCY_PATHS]
   ```

   Using a generator is the point. Building the full list and slicing afterwards does not
   avoid the blowup.

3. `scripts/performance_smoke.py` - add a lattice case and assert report generation stays
   under a threshold.

4. `frontend/src/pages/ReportDetailPage.tsx` - show "showing 50 of N paths" when
   `dependency_paths_truncated` is set.

### Verification

Re-run the lattice benchmark. The 10-level case currently produces 1,398,100 paths in 6.6s
at 132 MB of JSON; after the cap it should return 50 paths effectively instantly.

### Result (2026-08-05)

Implemented with one correction to the plan, found during implementation: the plan's
sketch wrapped the aggregation loop in a generator, but
`dependency_graph.py`'s `get_dependency_paths` already fully materialized
`nx.all_simple_paths` into a list before returning - so a single parent with large fan-out
would still blow up before the outer `islice` ever got a chance to stop it. Fixed by adding
a genuinely lazy primitive underneath:

- `backend/app/services/dependency_graph.py` - added `iter_dependency_paths`, a generator
  that yields one path at a time straight from `nx.all_simple_paths`. `get_dependency_paths`
  now delegates to it (`list(iter_dependency_paths(...))`), so the existing `/paths` API
  endpoint and its tests are unaffected.
- `backend/app/services/intelligence_layer.py` - `_build_affected_assemblies` consumes
  `iter_dependency_paths` through `itertools.islice(..., MAX_DEPENDENCY_PATHS + 1)`,
  `MAX_DEPENDENCY_PATHS = 50`.
- `backend/app/schemas/impact.py` - added `dependency_path_count` and
  `dependency_paths_truncated` to `AffectedAssembly`, both defaulted (`0` / `False`) so
  existing persisted `report_json` rows still validate without a backfill.
- `scripts/performance_smoke.py` - added `build_lattice_rows` plus a lattice-shaped report
  generation benchmark through the real `IntelligenceLayer`, with a 2-second budget that
  raises `SystemExit` (so CI actually fails) if exceeded.
- `frontend/src/lib/reportApi.ts` / `ReportDetailPage.tsx` - added the two new fields to the
  type and rendered "Dependency paths: N (showing the first 50)" when truncated.
  `dependency_paths` itself was not rendered anywhere in the UI before this change - only
  `affected_parents` / `affected_children` were shown.
- `backend/app/tests/test_intelligence_layer.py` - two new tests: a high-fanout lattice
  graph triggers the cap (`len(dependency_paths) == 50`, `truncated is True`), and a normal
  small graph stays untruncated with `dependency_path_count == len(dependency_paths)`.

Verification performed:

- `pytest`: 45 passed (43 baseline + 2 new).
- Re-ran the exact benchmark from the original review. Before: `levels=10` produced
  1,398,100 paths in 6.61s at 132 MB of JSON. After: 50 paths, `truncated=True`, in
  0.0004s - reproduced again end-to-end through `npm run qa:perf`
  (`report_seconds=0.0016` on a 10-level, 4-way lattice).
- Confirmed live against the running app: an old report generated before this fix
  correctly falls back to `dependency_path_count=0` / `truncated=False` (the keys simply
  didn't exist in its stored `report_json`), while a freshly generated report on the same
  BOM correctly returns `dependency_path_count=2`, matching its actual path count.
- Frontend `tsc -b` and `eslint` clean.

---

## Phase 24 - Unblock production deploy and CI

### Problem A: the production stack cannot start

`docker-compose.prod.yml:60` health-checks `/api/v1/ready`, but
`backend/app/middleware/auth.py:20` whitelists only `/api/v1/health` while
`PROTECTED_PREFIXES` covers all of `/api/v1`:

```text
curl -fsS http://127.0.0.1:8000/api/v1/ready
curl: (22) The requested URL returned error: 401   (exit 22)
```

The backend never becomes healthy, so `frontend` blocks forever on
`condition: service_healthy`. `npm run prod:up` hangs.

### Problem B: CI is red on every push

The "Validate Alembic migrations" step runs `alembic upgrade head` against SQLite;
migration `0006` calls `op.create_foreign_key`:

```text
NotImplementedError: No support for ALTER of constraints in SQLite dialect.
```

Migrations apply cleanly against PostgreSQL.

### Changes

1. `backend/app/middleware/auth.py:20` - add `"/api/v1/ready"` to `PUBLIC_PATHS`.

2. `backend/app/api/v1/health.py:16-22` - return a real failure status. Currently readiness
   returns HTTP 200 with `{"status": "unavailable"}`, so fixing the 401 alone would produce
   a health check that passes with a dead database. Do both together:

   ```python
   from fastapi.responses import JSONResponse

   @router.get("/ready")
   def readiness_check() -> JSONResponse:
       try:
           with SessionLocal() as db:
               db.execute(text("SELECT 1"))
       except SQLAlchemyError:
           return JSONResponse(
               status_code=503,
               content={"status": "unavailable", "database": "error"},
           )
       return JSONResponse(content={"status": "ready", "database": "ok"})
   ```

3. `.github/workflows/ci.yml:37` - choose one:
   - Preferred: add a `postgres:16-alpine` service container and run migrations against it.
     This matches the deployment target, so it is the meaningful test.
   - Cheaper: set `render_as_batch=True` in `alembic/env.py`'s `context.configure(...)`.
     This validates a path production never takes.

4. `README.md` - remove the "SQLite-compatible via `DATABASE_URL` if needed for quick
   experiments" claim unless batch mode is adopted. It is not currently true.

5. Split `backend/requirements.txt` - move `pytest==8.3.4` into `requirements-dev.txt`.
   CI and local setup install both; `backend/Dockerfile` installs only the runtime file.
   Currently pytest ships inside the production image.

### Verification

```bash
npm run prod:build && npm run prod:up
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

All services should reach `healthy` and the frontend should be reachable. This is the first
time that command will complete.

### Result (2026-08-05)

Implemented as specified, plus test coverage the plan didn't call out explicitly:

- `backend/app/middleware/auth.py` - added `/api/v1/ready` to `PUBLIC_PATHS`.
- `backend/app/api/v1/health.py` - `readiness_check` now returns a real `JSONResponse` with
  `503` on a database failure instead of `200` with a body claiming `"unavailable"`.
- `backend/app/tests/test_errors.py` - two new tests using hand-rolled context-manager
  objects and `monkeypatch` (no mocking library introduced - none was used anywhere else in
  this suite) to exercise both the 503 and 200 paths of `readiness_check` directly.
- `.github/workflows/ci.yml` - added a `postgres:16-alpine` service container to the
  `backend` job and pointed the "Validate Alembic migrations" step at it instead of SQLite.
- `backend/requirements-dev.txt` (new) - `-r requirements.txt` plus `pytest==8.3.4`.
  `backend/requirements.txt` no longer has pytest, so `backend/Dockerfile` (which only ever
  installed `requirements.txt`) stops shipping it in the production image as a side effect -
  no Dockerfile edit was needed.
- `README.md` - install instructions now use `requirements-dev.txt` (needed since the
  "Run parser tests" section a few paragraphs later depends on `pytest` being installed);
  replaced the "SQLite-compatible... for quick experiments" claim with an explanation of
  why migrations specifically require PostgreSQL.

Verification performed:

- Reproduced the original failure directly: `curl -fsS http://127.0.0.1:8000/api/v1/ready`
  returned `401` (`curl: (22)`) before this fix. After: `200` with
  `{"status":"ready","database":"ok"}`.
- `pytest`: 47 passed (45 baseline + 2 new).
- Installed `backend/requirements-dev.txt` into a completely fresh venv - confirms both
  `pytest` and the runtime deps resolve correctly as one file.
- Started a disposable `postgres:16-alpine` container matching the new CI service
  definition exactly (fresh volume, same image, same credentials) and ran
  `alembic upgrade head` against it directly: all 7 migrations applied cleanly.
- Ran the full production stack end-to-end under an isolated Compose project name
  (`bom-tracker-prodcheck`, separate network/volumes from the dev stack) via
  `docker compose --env-file .env.production -p bom-tracker-prodcheck -f docker-compose.prod.yml up -d`.
  Result: `postgres` healthy, `migrate` ran all 7 migrations and exited 0, **`backend`
  reached `healthy`** (previously impossible - this is the deadlock the phase fixes),
  `frontend` came up and correctly proxied `/api/v1/health` through nginx. Torn down
  afterward with `down -v`; confirmed the real dev stack (port 8000/5173/55432) was
  untouched throughout.

---

## Phase 25 - Fix middleware ordering

### Problem

`backend/app/main.py:28-39` - `add_middleware` builds outside-in, so the last registered
middleware runs first. `InMemoryRateLimitMiddleware` therefore runs before
`JWTAuthenticationMiddleware` sets `request.state.user_id`. The `getattr(request.state,
"user_id", None)` lookup at `backend/app/middleware/rate_limit.py:69` is always `None`, so
the per-user branch never executes and every client behind one NAT shares a bucket.

### Changes

1. Register `InMemoryRateLimitMiddleware` before `JWTAuthenticationMiddleware` in source
   order.
2. Add a test in `test_security_middleware.py` asserting two authenticated users get
   independent rate-limit buckets - the behaviour that silently does not exist today.
3. Add a comment recording the intended execution order. This ordering is invisible when
   reading the file and will otherwise be broken again.

---

## Phase 26 - Timezone-aware timestamps

Scheduled late because it touches roughly 24 columns across 8 model files plus a data
migration, and is cosmetic in severity next to Phases 22 and 24. It is, however, visible on
every screen.

### Problem

33 uses of `datetime.utcnow()` write into naive `DateTime` columns. The API serializes
`2026-08-03T06:47:30` with no `Z`, and JavaScript `new Date(...)` parses a timezone-less ISO
string as local time. Files uploaded at 10:47 local display as `8/3/2026, 6:47:30 AM` for a
UTC+4 user. `utcnow()` is also deprecated in Python 3.12, which `backend/Dockerfile` and CI
both use.

### Changes

1. Replace all `datetime.utcnow` occurrences with `datetime.now(UTC)`.
2. Change every `mapped_column(DateTime, ...)` to `DateTime(timezone=True)` across
   `user.py`, `upload.py`, `bom.py`, `document.py`, `eco.py`, `job.py`, `report.py`, and
   `graph_snapshot.py`.
3. New Alembic migration `0008`. Existing values are UTC-naive, so the conversion is:

   ```python
   op.alter_column(
       "uploaded_files",
       "created_at",
       type_=sa.DateTime(timezone=True),
       postgresql_using="created_at AT TIME ZONE 'UTC'",
   )
   ```

   Repeat per column. Enumerate the full list with `grep -rn "DateTime" backend/app/models/`.

### Verification

Upload a file. The API should return `...+00:00`, and the dashboard should show local
wall-clock time rather than a UTC-offset-shifted value.

---

## Phase 27 - Consolidate test fixtures

Nine of eighteen test files each define their own `build_session()`; five redefine
`create_user()`; four redefine `create_upload()`. Each session rebuilt the fixture instead
of importing one.

1. Create `backend/app/tests/conftest.py` with `db_session`, `user`, and `upload` fixtures.
2. Delete the local copies file by file, running the suite after each.
3. Collapse the two `pytest.ini` files (root and `backend/`) into one at `backend/pytest.ini`,
   since Phase 21 makes every script run from there.

Removes several hundred lines and gives one place to change when the schema moves.

---

## Phase 28 - Remove rot

Small, independent, and safe. Batch into one commit.

- `frontend/src/data/dashboardData.ts:48,75,110,164` - delete `metrics`, `recentUploads`,
  `recentReports`, and `recentActivity` (about 115 lines of stale mock data left over from
  before `HomePage` was wired to the API). Nothing imports them as values. Keep the types,
  which are used.
- `backend/app/api/v1/uploads.py:135` - `from app.core.audit import audit_event` sits at the
  bottom of the file, below its callers. It works, but every other module imports at the
  top. Move it.
- `backend/app/services/file_storage.py:59` - with configuration pinned in Phase 21, make
  `UPLOAD_DIRECTORY` absolute and delete the six-candidate `resolve_storage_path` search,
  which silently resolves a stale path to a different file. Add a check that the resolved
  path stays inside the upload directory.
- `backend/app/services/intelligence_layer.py:103` - when nothing is affected,
  `procurement` gets `medium` while its three siblings get `low`, which then trips the
  `high_or_medium_records` bonus at line 187 and adds +5 risk for a change with no impact.
  Make it consistent.
- `backend/app/services/report_exports.py:90` - the hand-rolled PDF starts at `50 770 Td`
  with 14pt leading and has no pagination, so beyond roughly 55 lines content runs off the
  page and is silently invisible. Paginate, or truncate with an explicit "N more items" line.

---

## Phase 29 - Consolidate the workflow and docs

There are 2,786 lines across 7 documents (`README.md` 506, `docs/PROJECT_CONTEXT.md` 673,
`docs/USER_GUIDE.md` 1073, plus others), organised by build order ("Phase 6 adds..."). A
reader who wants to run the project has to reconstruct the steps from 20 phase sections.

- Rewrite `README.md` around one getting-started path: clone, `npm run setup`, `npm run dev`.
  Move phase history into `docs/PROJECT_CONTEXT.md`, where it already belongs.
- Add `npm run setup` performing venv creation, pip install, `npm ci`, and `.env` copies in
  one command. Nothing currently creates `backend/.venv`, so a fresh clone cannot run any
  backend script.
- Add `npm run dev:all` to start PostgreSQL, backend, and frontend together.
- Fold `docs/QA_PLAN.md` and `docs/RELEASE_CHECKLIST.md` into one file; they overlap heavily.
- Decide on `History` and `Settings`. Both still render `PagePlaceholder` ("intentionally
  empty until the next implementation phase") while the sidebar presents them as
  workspaces. Either build them or remove the nav entries.
