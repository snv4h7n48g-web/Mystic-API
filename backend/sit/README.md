# Mystic SIT v2

Small additive system-integration test harness for Mystic preview and reading generation.

## Scope

v2 now covers:
- combined session preview via `MysticGenerationOrchestrator.build_session_preview_result`
- combined full reading via `MysticGenerationOrchestrator.build_session_reading_result`
- daily preview
- daily full reading
- tarot solo preview
- compatibility preview
- compatibility full reading
- feng shui preview
- static realistic fixtures
- shared structural / contract / metadata validation
- JSON + markdown report output

## What it does not do yet

- CI integration
- DB-backed setup / teardown
- feng shui full reading SIT coverage
- lunar / palm SIT coverage
- snapshot-style prose assertions
- retry orchestration for flaky external calls

## Current status

SIT v2 is now shipped for its bounded scope.

Shipped commits:
- `4382624` — Add Mystic SIT v1 preview harness
- `203c867` — Validate combined preview payloads in SIT

See `backend/sit/HANDOFF.md` for the phase handoff and next-step recommendation.
See `backend/sit/RELEASE_POLICY.md` for release-workflow placement and required checks before shipping.

## Run locally

From `backend/` with the existing virtualenv / AWS Bedrock credentials available:

```bash
python -m sit.runner
```

Run selected cases:

```bash
python -m sit.runner --case combined_preview
python -m sit.runner --case combined_full_reading
python -m sit.runner --case daily_preview --case daily_full_reading
python -m sit.runner --case tarot_solo_preview
python -m sit.runner --case compatibility_preview --case compatibility_full_reading
python -m sit.runner --case feng_shui_preview
```

Custom report directory:

```bash
python -m sit.runner --output-dir ./sit/reports-local
```

## Output

Reports are written under `backend/sit/reports/` by default:
- `mystic-sit-report-<timestamp>.json`
- `mystic-sit-report-<timestamp>.md`

## Validation approach

The harness checks:
- transport success or raised exception
- preview/readings payload structure
- required metadata fields
- contract-aligned section ids where applicable
- existing product validator output

Calibration notes:
- daily preview and tarot preview accept either the current shared preview envelope or future specialized preview formatter shapes
- daily full reading accepts a contract-aligned subset because the formatter legitimately drops blank optional sections
- compatibility preview still downgrades a couple of softer relational-quality issues to warnings so the run surfaces usable output without hiding real breakage
