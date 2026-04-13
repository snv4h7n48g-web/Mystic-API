# Mystic API Code Review (2026-04-13)

## Scope
- Repository-wide static review of backend and test tooling.
- Quick execution check via `pytest -q` from `backend/`.

## High-priority defects

### 1) Unit test suite is effectively broken out-of-the-box (import path misconfiguration)
**Evidence**
- `backend/pytest.ini` does not configure `pythonpath`, so tests that import top-level modules (`import main`, `from pricing import ...`) fail during collection. 
- Running `pytest -q` from `backend/` produced `ModuleNotFoundError` across core modules.

**Impact**
- CI confidence is low; regressions can ship undetected because the default unit-test command fails before any assertions execute.

**Fix recommendation**
- Add `pythonpath = .` under `[pytest]` in `backend/pytest.ini`, or convert imports to package-style imports and run tests as a module (`python -m pytest`).
- Add this check to CI so collection failures block merges.

---

### 2) `UserService.set_subscription` can raise on unknown user IDs
**Evidence**
- `set_subscription` calls `self.get_user_by_id(user_id)` and immediately uses `user.get(...)` without checking for `None`.

**Impact**
- A bad/expired/stale user ID can raise an unhandled `AttributeError`, causing 500 errors on subscription update flows.

**Fix recommendation**
- Guard with `if not user: raise ValueError("User not found")` (or a domain-specific exception surfaced as HTTP 404/400).
- Add unit tests for unknown user IDs.

---

### 3) Duplicate dependency declaration in production requirements
**Evidence**
- `requests==2.31.0` appears twice in `backend/requirements.txt`.

**Impact**
- Low runtime risk, but signals dependency hygiene drift and can mask merge mistakes in dependency updates.

**Fix recommendation**
- Deduplicate and add a lock/check step (`pip-compile` or `uv pip compile`) in release workflow.

## Medium-priority defects / maintainability risks

### 4) Test runner script is fragile about execution directory
**Evidence**
- `scripts/unix/test-unit.sh` assumes `venv` is in current working directory and executes `./venv/bin/python3 -m pytest -q`.

**Impact**
- Running from repository root (common in CI) fails unless a root-level `venv` exists.

**Fix recommendation**
- Resolve script directory and `cd backend` explicitly, or make script path-agnostic.

---

### 5) Read-only queries are wrapped in write-style transactions
**Evidence**
- Many read operations use `with engine.begin()` (e.g., `get_user_by_email`, `get_user_by_id`, `get_user_sessions`).

**Impact**
- Slightly higher transaction overhead and lock bookkeeping under load versus using `engine.connect()` for read paths.

**Fix recommendation**
- Use `engine.connect()` for SELECT-only methods and reserve `engine.begin()` for writes.

## Dependency map (declared)

### Runtime dependencies (`backend/requirements.txt`)
- **API & validation:** `fastapi`, `pydantic`, `email-validator`
- **ASGI server:** `uvicorn[standard]`
- **Data layer:** `sqlalchemy`, `psycopg2-binary`
- **HTTP clients:** `httpx`, `requests`
- **Cloud integration:** `boto3` (AWS Bedrock)
- **Auth/security:** `bcrypt`, `PyJWT`, `python-dotenv`
- **Media/vision utility:** `Pillow`

### Dev/test dependencies (`backend/requirements-dev.txt`)
- `pytest`, `pytest-cov`

## Performance improvement opportunities

### A) Startup-time schema migration in application boot path
**Evidence**
- `main.py` runs `init_db()` by default at import/startup and performs many `CREATE TABLE`/`ALTER TABLE` statements.

**Why this matters**
- Increases cold-start latency and couples runtime startup to migration behavior.
- Can create contention/risk during multi-replica deployments.

**Recommendation**
- Move schema changes to explicit migrations (Alembic) and keep runtime startup minimal.

---

### B) Prompt payload inflation for Bedrock calls
**Evidence**
- Bedrock service injects a large, combined reference block (`ASTROLOGY_REFERENCE`, `TAROT_REFERENCE`, `PALMISTRY_REFERENCE`, `VOICE_LIBRARY`) into prompts.

**Why this matters**
- Larger tokenized context increases latency and cost per request.

**Recommendation**
- Use selective retrieval (only relevant snippets by product/flow) and cache reusable prompt fragments.
- Track prompt token contribution per section and set budget caps.

---

### C) Engine instantiation scattered across modules
**Evidence**
- Separate SQLAlchemy engines are created in both `main.py` and `user_service.py`.

**Why this matters**
- Can fragment pooling behavior and make connection tuning harder.

**Recommendation**
- Centralize engine/session factory in one module and import it everywhere.

## Suggested remediation order
1. Fix pytest collection/import path so test suite is enforceable.
2. Add `set_subscription` user existence guard and tests.
3. Move startup schema mutation to migration workflow.
4. Optimize prompt context size and observability around token/cost/latency.
5. Refactor DB engine ownership and read-only transaction usage.
