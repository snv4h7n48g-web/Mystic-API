# Mystic SIT v1

Small additive system-integration test harness for Mystic preview generation.

## Scope

v1 currently covers:
- combined session preview via `MysticGenerationOrchestrator.build_session_preview_result`
- compatibility preview via `MysticGenerationOrchestrator.build_compatibility_preview_result`
- static realistic fixtures
- shared structural / contract / metadata validation
- JSON + markdown report output

## What it does not do yet

- CI integration
- DB-backed setup / teardown
- full reading SIT coverage
- snapshot-style prose assertions
- retry orchestration for flaky external calls

## Run locally

From `backend/` with the existing virtualenv / AWS Bedrock credentials available:

```bash
python -m sit.runner
```

Run one case only:

```bash
python -m sit.runner --case combined_preview
python -m sit.runner --case compatibility_preview
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
- preview payload structure
- required metadata fields
- contract-aligned section ids where applicable
- existing product validator output

For compatibility preview, transport/parser/schema failures are treated as hard failures. Some softer quality issues can be downgraded to warnings so the run still captures usable output without hiding real breakage.
