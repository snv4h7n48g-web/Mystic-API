# Mystic Release Policy — Model-Integrated Safety

## Purpose
Mystic uses model-generated preview and reading outputs that can fail in ways normal unit tests will not catch:
- parser/schema mismatches
- flow-contract drift
- model-routing regressions
- prompt-output omissions
- provider/model behavior changes

This policy defines what must run before shipping.

---

## 1. Test layers

### Layer A — deterministic checks
Run on every PR:
- unit tests
- parser tests
- formatter tests
- validator tests
- non-LLM backend tests
- Flutter analyze/tests for touched frontend files where applicable

These are the fast baseline.

### Layer B — SIT
Run real model-in-the-loop System Integration Tests for release-relevant generation paths.

Current SIT status:
- SIT v2 has landed
- current case set:
  - `combined_preview`
  - `combined_full_reading`
  - `daily_preview`
  - `daily_full_reading`
  - `tarot_solo_preview`
  - `compatibility_preview`
  - `compatibility_full_reading`
  - `feng_shui_preview`

---

## 2. Required checks by change type

### A. UI-only change
Examples:
- layout
- hierarchy
- CTA placement
- copy-only frontend change
- accessibility tweaks

#### Required
- deterministic backend/frontend checks
- manual smoke test on affected flow

#### SIT
- optional unless the change touches generation-state handling, payload assumptions, or preview/read flow wiring

---

### B. Prompt / parser / formatter / validator / orchestration / model-routing change
Examples:
- output schema edits
- parser strictness changes
- orchestration changes
- persona routing changes
- model swap
- contract changes
- preview/read payload formatting changes

#### Required
- deterministic checks
- **SIT v2 release-critical group required**

#### Release rule
Do not ship if any release-critical SIT case hard-fails.

---

### C. Preview-path backend change
Examples:
- `/preview` route
- preview formatter
- preview contract
- unlock metadata changes
- preview model selection

#### Required
- deterministic checks
- **SIT v2 preview release-critical cases required**
- manual app smoke on at least one real preview flow

#### Release rule
Preview-path backend changes require at least one successful real preview generation outside unit tests.

---

### D. Full-reading backend change
Examples:
- `/reading` route
- full reading formatter
- full reading validator
- palm/tarot evidence payload changes

#### Required
- deterministic checks
- **SIT v2 full-reading release-critical cases required**
- manual real-flow smoke test

---

## 3. Current release-critical SIT group

The post-v2 release-critical SIT group is:
- `combined_preview`
- `combined_full_reading`
- `daily_preview`
- `daily_full_reading`
- `tarot_solo_preview`
- `compatibility_preview`
- `compatibility_full_reading`
- `feng_shui_preview`

### Preview subset
Use this subset when the change only affects preview surfaces:
- `combined_preview`
- `daily_preview`
- `tarot_solo_preview`
- `compatibility_preview`
- `feng_shui_preview`

### Full-reading subset
Use this subset when the change only affects full-reading surfaces:
- `combined_full_reading`
- `daily_full_reading`
- `compatibility_full_reading`

### Pass criteria
A release-critical SIT case passes if:
- no transport failure
- no parser failure
- no hard validator failure
- payload contract is valid for the case
- metadata is captured
- report is emitted

### Fail criteria
A release-critical SIT case fails if:
- 5xx or raised exception
- parser error
- missing required contract fields
- hard validator failure
- unusable/empty payload

Warnings may be tolerated, but only if they are explicitly classified as soft and understood.

---

## 4. Manual smoke requirements

Even with SIT, require manual smoke for any externally visible release.

### Minimum manual smoke
#### Preview-affecting release
- 1 combined preview in app
- 1 targeted affected preview flow in app

#### Reading-affecting release
- 1 combined preview + unlock + full reading
- 1 targeted affected product flow if applicable

#### UX/frontend release
- manual smoke on the touched surface
- one small-device check if layout changed
- one accessibility sanity check if semantics/tap-targets changed

---

## 5. Recommended release process

### For normal backend/model-sensitive releases
1. run deterministic suite
2. run the applicable SIT v2 release-critical group
3. review SIT markdown/json report
4. run manual app smoke on affected flows
5. ship only if:
   - deterministic suite passes
   - applicable release-critical SIT passes
   - manual smoke is clean or known issues are accepted explicitly

---

## 6. SIT report handling

Every SIT run should produce:
- JSON artifact
- markdown summary

### Reviewer should check
- pass/fail per case
- model id used
- persona/profile used
- latency
- token counts
- cost
- hard failures vs warnings

Do not treat “runner executed” as sufficient. Review the result summary.

---

## 7. Severity rules

### Hard block
- parser/schema mismatch
- contract failure
- empty/unusable payload
- repeated 5xx
- missing required generation metadata

### Soft warning
- latency spike
- cost spike
- degraded but valid output
- validator warning explicitly classified as non-fatal

Soft warnings can ship only with deliberate acceptance.

---

## 8. Policy summary

### Must run on risky backend/model changes
- deterministic tests
- applicable SIT v2 release-critical cases

### Must run before release
- manual smoke on the affected flow(s)

### No-ship condition
- any hard SIT failure in the applicable release-critical group
