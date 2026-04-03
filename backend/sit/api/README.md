# Mystic API SIT v3

Thin API-level system-integration tests for release-critical backend flows.

## Design

- Runs in-process against real FastAPI routes with `TestClient`
- Uses a dedicated local Postgres test database: `mystic_sit_api`
- Patches orchestrator output so the suite validates API wiring, gating, and persistence rather than live model behavior
- Keeps assertions structural and release-relevant

## Covered flows

1. combined preview API
2. combined full reading API
3. compatibility preview API
4. compatibility full reading API
5. daily preview API

## Run

From `backend/`:

```bash
pytest sit/api/test_api_sit_v3.py -q
```
