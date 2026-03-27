# Mystic RC QA Checklist (Purchases/Auth/Entitlements)

## Auth hardening
- [ ] Email/password login still works with valid credentials.
- [ ] Invalid password returns `401` and never leaks account existence details.
- [ ] Apple Sign-In rejects identity tokens when `ALLOW_INSECURE_APPLE_SIGN_IN` is not enabled.
- [ ] Apple Sign-In succeeds in dev only when insecure flag is explicitly enabled.

## Purchase verification + restore
- [ ] iOS purchase fails fast when receipt is missing in non-dev builds.
- [ ] Production receipt endpoint retries sandbox on Apple `21007` and succeeds.
- [ ] Subscription activation stores `original_transaction_id` and reflects active status.
- [ ] Restore flow returns merged entitlements (`verified_products`) + restored product IDs.
- [ ] Canceled/expired subscription transactions do not grant active entitlement.

## Entitlements and access control
- [ ] `/v1/entitlements/refresh` includes expected `verified_products` and transaction list.
- [ ] Reading endpoint blocks full reading without entitlement (`402`) and allows with entitlement.
- [ ] Compatibility/Feng Shui access is denied for non-owner users (`403`).
- [ ] Admin-only endpoints reject normal users (`403`) and allow admins.

## Bundle + product mapping
- [ ] Bundle purchase grants intended feature gates (compatibility/feng-shui/lunar where applicable).
- [ ] Flow-specific products (e.g. lunar-only) map to correct unlock SKU and remain isolated.

## Regression smoke
- [ ] Existing unit tests pass (backend + frontend).
- [ ] No new warnings in CI that indicate skipped/ignored async tests.
- [ ] Purchase-related telemetry/logging still captures provider, environment, transaction IDs.
