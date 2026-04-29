# Mystic Release Policy - Model-Integrated Safety

## Purpose

Mystic uses model-generated preview and reading outputs that can fail in ways normal unit tests will not catch:
- parser/schema mismatches
- flow-contract drift
- model-routing regressions
- prompt-output omissions
- provider/model behavior changes
- release config drift

This policy defines what must run before shipping.

---

## 1. Test Layers

### Layer A - Deterministic Checks

Run on every PR:
- unit tests
- parser tests
- formatter tests
- validator tests
- non-LLM backend tests
- Flutter analyze/tests for touched frontend files where applicable

These are the fast baseline.

### Layer B - Orchestration SIT

Run orchestration-level SIT for release-relevant generation paths:

```bash
python -m sit.runner
```

Use selected cases when the change is narrow:

```bash
python -m sit.runner --case combined_preview --case daily_preview
python -m sit.runner --case combined_full_reading --case compatibility_full_reading
```

### Layer C - API SIT

Run API-level SIT when routes, persistence, purchase gates, or response envelopes change:

```bash
pytest sit/api/test_api_sit_v3.py -q
```

### Layer D - Live LLM UAT

Run live Bedrock UAT before UAT signoff and before any production push that changes prompt, parser, formatter, validator, orchestration, model routing, or release config:

```bash
python verify_bedrock.py
python scripts/run_llm_uat.py --output-dir ./sit/reports
```

For local development with known non-release settings, use:

```bash
python scripts/run_llm_uat.py --allow-config-warnings --output-dir ./sit/reports-local
```

CI includes deterministic backend checks and a manual `workflow_dispatch` live LLM UAT job.

---

## 2. Required Checks By Change Type

### A. UI-Only Change

Examples:
- layout
- hierarchy
- CTA placement
- copy-only frontend change
- accessibility tweaks

Required:
- deterministic backend/frontend checks
- manual smoke test on affected flow

SIT/UAT:
- optional unless the change touches generation-state handling, payload assumptions, or preview/read flow wiring

### B. Prompt / Parser / Formatter / Validator / Orchestration / Model-Routing Change

Examples:
- output schema edits
- parser strictness changes
- orchestration changes
- persona routing changes
- model swap
- contract changes
- preview/read payload formatting changes

Required:
- deterministic checks
- applicable orchestration SIT cases
- Live LLM UAT release-critical group

Release rule:
- do not ship if any release-critical live UAT case hard-fails

### C. Preview-Path Backend Change

Examples:
- `/preview` route
- preview formatter
- preview contract
- unlock metadata changes
- preview model selection

Required:
- deterministic checks
- preview SIT/UAT subset
- manual app smoke on at least one real preview flow

Release rule:
- preview-path backend changes require at least one successful real preview generation outside unit tests

### D. Full-Reading Backend Change

Examples:
- `/reading` route
- full reading formatter
- full reading validator
- palm/tarot evidence payload changes

Required:
- deterministic checks
- full-reading SIT/UAT subset
- manual real-flow smoke test

---

## 3. Release-Critical Live UAT Group

The release-critical live UAT group is:
- `combined_preview`
- `combined_full_reading`
- `daily_preview`
- `daily_full_reading`
- `tarot_solo_preview`
- `compatibility_preview`
- `compatibility_full_reading`
- `feng_shui_preview`
- `feng_shui_analysis`

### Preview Subset

Use this subset when the change only affects preview surfaces:
- `combined_preview`
- `daily_preview`
- `tarot_solo_preview`
- `compatibility_preview`
- `feng_shui_preview`

### Full-Reading Subset

Use this subset when the change only affects full-reading or analysis surfaces:
- `combined_full_reading`
- `daily_full_reading`
- `compatibility_full_reading`
- `feng_shui_analysis`

### Pass Criteria

A release-critical live UAT case passes if:
- no transport failure
- no parser failure
- no hard validator failure
- payload contract is valid for the case
- generation metadata is captured
- report is emitted
- premium model routing is used for user-facing generation

### Fail Criteria

A release-critical live UAT case fails if:
- 5xx or raised exception
- parser error
- missing required contract fields
- hard validator failure
- unusable/empty payload
- unexpected fallback to legacy/Nova generation for a user-facing persona route

Warnings may be tolerated, but only if they are explicitly classified as soft and understood.

---

## 4. Manual Smoke Requirements

Even with SIT/UAT, require manual smoke for any externally visible release.

### Minimum Manual Smoke

Preview-affecting release:
- 1 combined preview in app
- 1 targeted affected preview flow in app

Reading-affecting release:
- 1 combined preview + unlock + full reading
- 1 targeted affected product flow if applicable

UX/frontend release:
- manual smoke on the touched surface
- one small-device check if layout changed
- one accessibility sanity check if semantics/tap-targets changed

---

## 5. Recommended Release Process

For normal backend/model-sensitive releases:
1. run deterministic suite
2. run applicable orchestration SIT/API SIT cases
3. run `python verify_bedrock.py`
4. run applicable `python scripts/run_llm_uat.py` cases
5. review markdown/json reports
6. run manual app smoke on affected flows
7. ship only if deterministic checks pass, applicable UAT passes, and manual smoke is clean or explicitly accepted

---

## 6. Report Handling

Every SIT/UAT run should produce:
- JSON artifact
- markdown summary

Reviewer should check:
- pass/fail per case
- model id used
- persona/profile used
- latency
- token counts
- cost
- hard failures vs warnings

Do not treat "runner executed" as sufficient. Review the result summary.

---

## 7. Severity Rules

### Hard Block

- parser/schema mismatch
- contract failure
- empty/unusable payload
- repeated 5xx
- missing required generation metadata
- non-premium or legacy model route used unexpectedly

### Soft Warning

- latency spike
- cost spike
- degraded but valid output
- validator warning explicitly classified as non-fatal

Soft warnings can ship only with deliberate acceptance.

---

## 8. Policy Summary

Must run on risky backend/model changes:
- deterministic tests
- applicable SIT/API SIT cases
- live LLM UAT

Must run before release:
- manual smoke on the affected flows

No-ship condition:
- any hard failure in the applicable release-critical group
