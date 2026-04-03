# Mystic SIT Handoff

## Current status
Mystic SIT v1 is now implemented and in a usable state.

Shipped commits:
- `4382624` — Add Mystic SIT v1 preview harness
- `203c867` — Validate combined preview payloads in SIT

Related backend stability fix during this phase:
- `0e8481a` — Relax preview parser optional fields

## What SIT v1 covers
SIT v1 is a bounded, model-in-the-loop backend harness for real Bedrock-backed preview generation.

### Included
- harness / runner
- static fixture helpers
- shared validators
- combined preview SIT case
- compatibility preview SIT case
- JSON + markdown report output
- focused harness tests

### Entry point
Run from `backend/`:

```bash
python -m sit.runner
```

Single case:

```bash
python -m sit.runner --case combined_preview
python -m sit.runner --case compatibility_preview
```

## Implemented files
- `backend/sit/__init__.py`
- `backend/sit/runner.py`
- `backend/sit/fixtures.py`
- `backend/sit/validators.py`
- `backend/sit/reports.py`
- `backend/sit/README.md`
- `backend/sit/reports/.gitkeep`
- `backend/tests/test_sit_validators.py`
- `backend/tests/test_sit_reports.py`

## Verification completed
Implementation phase verification reported:
- `PYTHONPATH=. ./venv/bin/pytest tests/test_sit_validators.py tests/test_sit_reports.py tests/test_orchestration_payload_compatibility.py tests/test_product_routing_and_validators.py`
- result: passing
- real runner attempts completed for:
  - combined preview
  - compatibility preview

Follow-up fix verification:
- `PYTHONPATH=. ./venv/bin/pytest tests/test_sit_validators.py tests/test_product_quality_gates.py -q`
- result: passing

## What the follow-up fixed
The initial review correctly identified one meaningful gap:
- combined preview SIT was not running the product validator, which could create a false green

That is now fixed.

SIT v1 now:
- runs the product validator for combined preview too
- includes negative combined-preview validator coverage
- validates `unlock_price` more strictly
- validates `product_id` as a non-empty string

## What SIT v1 is good for
Use SIT v1 to catch:
- parser/schema mismatches in real model output
- missing required metadata/shape
- flow-specific preview contract regressions
- model-routing / prompt-path breakage on the preview surfaces

It is especially useful after:
- parser changes
- output-schema changes
- prompt changes
- orchestration changes
- model-routing changes

## What SIT v1 is not yet
It is not yet:
- a full release matrix across all flows
- a CI/nightly system
- full-reading SIT coverage
- a DB-backed end-to-end API harness
- a performance/load harness

## Recommended SIT v2
Best next expansion:

### Add full-reading coverage
Priority order:
1. combined full reading
2. daily preview
3. daily full reading
4. tarot solo preview
5. compatibility full reading
6. feng shui preview

### Improve reporting
- explicit warning taxonomy
- clearer summary of validator issues vs transport failures
- optional comparison to prior run metadata

### Add release grouping
- `--group previews`
- `--group release-critical`
- `--group daily`

### Optional later
- nightly automation
- lightweight artifact retention
- DB-backed fixture path for API-level SIT

See also: `backend/sit/RELEASE_POLICY.md` for the concrete release policy and no-ship rules.

## Recommended release workflow placement

### Always run on PRs
- deterministic unit tests
- parser/formatter/validator tests

### Run SIT v1 when
- prompts changed
- parser changed
- output schema changed
- orchestration changed
- model/provider routing changed
- before release candidates

### Good initial release gate
Treat these as release-critical:
- combined preview SIT
- compatibility preview SIT

If both pass, you have a real model-integration sanity check on the conversion-critical preview layer.

## Suggested next phase
If continuing SIT work, the highest-leverage next step is:

### SIT v2 = expand to full-reading + daily coverage
That gives you:
- preview + reading safety net
- better coverage of product drift
- better confidence before model/prompt/backend changes ship

## Notes for the next agent
Before extending SIT:
1. read this file
2. read `backend/sit/README.md`
3. inspect `4382624` and `203c867`
4. do not overcomplicate v2 with CI or DB setup unless explicitly requested
5. preserve the current principle: real model calls, structural assertions, not brittle prose snapshots
