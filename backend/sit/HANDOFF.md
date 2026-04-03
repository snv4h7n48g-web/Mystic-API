# Mystic SIT Handoff

## Current status
Mystic SIT is now materially established across three layers.

Shipped commit chain:
- `4382624` — Add Mystic SIT v1 preview harness
- `203c867` — Validate combined preview payloads in SIT
- `293b68e` — Document Mystic SIT v1 handoff
- `20d8848` — Add SIT release policy
- `27c8af5` — Cross-link SIT docs
- `b9a3db2` — Add Mystic SIT v2 coverage
- `50f8bc2` — Update SIT v2 release policy
- `34e12ae` — Add Mystic API SIT v3 coverage

Related backend stability fix during this broader phase:
- `0e8481a` — Relax preview parser optional fields

## What now exists

### SIT v1 — preview model-in-the-loop baseline
Covers:
- combined preview
- compatibility preview
- static fixtures
- shared validators
- JSON + markdown reporting

What it is for:
- catching parser/schema mismatches in real model output
- catching preview contract regressions
- catching model-routing / prompt-path breakage on the preview layer

### SIT v2 — expanded orchestration-level coverage
Adds:
- combined full reading
- daily preview
- daily full reading
- tarot solo preview
- compatibility full reading
- feng shui preview

What it is for:
- broader structural validation across major generation flows
- preview + full reading safety net at the orchestrator level
- release-critical structural checks on the current product set

### SIT v3 — API-level route/persistence/gating layer
Adds:
- combined preview API
- combined full reading API
- compatibility preview API
- compatibility full reading API
- daily preview API

What it is for:
- validating actual FastAPI route behavior
- validating response envelope wiring
- validating DB persistence side effects
- validating purchase/subscription gating behavior
- catching route-level breakage that v1/v2 cannot see

Important:
- SIT v3 intentionally uses patched orchestrator responses
- it is an API-level route/persistence/gating layer, not a real-model layer
- real-model coverage remains the responsibility of SIT v1/v2

---

## How the layers fit together

### Deterministic tests
Use for:
- parser
- formatter
- validator
- unit logic

### SIT v1 + v2
Use for:
- real model/model-routing/orchestration confidence
- contract and payload shape validation
- preview/full reading generation sanity

### SIT v3
Use for:
- API route correctness
- persistence correctness
- auth/subscription/purchase gate correctness
- response envelope correctness

Taken together, this gives Mystic:
- deterministic backend safety
- real-model orchestration safety
- API-level route/persistence safety

---

## Current release workflow recommendation
See `backend/sit/RELEASE_POLICY.md` for the concrete release policy.

Short version:
- always run deterministic tests
- run applicable SIT v2 release-critical cases for prompt/parser/orchestration/model-sensitive changes
- run manual smoke before release
- use SIT v3 for route/persistence/gating-sensitive backend work

### Practical use of SIT v3
SIT v3 is best run when changing:
- preview/read route handlers
- auth behavior in route handlers
- purchase/subscription gate logic
- DB persistence wiring
- response envelope construction

---

## Current SIT docs
- `backend/sit/README.md`
- `backend/sit/HANDOFF.md`
- `backend/sit/RELEASE_POLICY.md`
- `backend/sit/api/README.md`

---

## What is still not covered
These are next-phase candidates, not unfinished work inside the current SIT phase.

1. **API-level daily full reading SIT**
2. **API-level feng shui full analysis SIT**
3. **API-level palm/lunar specialist SIT**
4. **CI/nightly automation**
5. **cross-run comparison / drift reporting**
6. **cost/latency trend reporting**
7. **purchase/entitlement-specific deeper SIT beyond current route gates**

---

## Best next SIT phase
If continuing, the highest-leverage next move is not “more random cases.”

### Recommended next phase
**SIT v4 = targeted API expansion + release grouping refinement**

Good candidates:
1. daily full reading API
2. feng shui full analysis API
3. one purchase/entitlement-heavy route path beyond current gating checks
4. cleaner `--group` support in the runner (`preview`, `full`, `api`, `release-critical`)

Why this is the best next move:
- it builds directly on the safety-net shape already established
- it improves route-level release confidence
- it avoids premature CI/platform complexity

---

## Notes for the next agent
Before extending SIT again:
1. read this file
2. read `backend/sit/README.md`
3. read `backend/sit/RELEASE_POLICY.md`
4. inspect the commit chain from `4382624` through `34e12ae`
5. preserve the distinction between:
   - real-model SIT (v1/v2)
   - API route/persistence SIT (v3)
6. do not overcomplicate the next phase with CI or infra automation unless explicitly requested
