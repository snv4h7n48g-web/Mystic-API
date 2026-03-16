# Mystic API Testing

## Install unit test dependencies

```bash
python -m pip install -r requirements-dev.txt
```

## Run backend unit tests

```bash
python -m pytest -q
```

## Current unit test coverage

- `tests/test_pricing.py`
  - Product validation rules, seasonal gating, revenue aggregation.
- `tests/test_astrology_engine.py`
  - Chinese zodiac calculation and chart/synastry structure checks.
- `tests/test_bedrock_service_unit.py`
  - Flow schema selection, section parser behavior, anchor building, cost math.
- `tests/test_auth_service.py`
  - Password hashing, token generation/verification, Apple token checks, token hashing.
- `tests/test_geocoding_service.py`
  - Geocode cache normalization, suggestions, fallback behavior.
- `tests/test_models_validation.py`
  - Pydantic validation for account payloads and auth provider defaults.

## Notes

- `pytest.ini` scopes discovery to `tests/` and excludes `venv/`.
- Existing `test_api.py` / `test_accounts.py` / `test_palm_api.py` remain integration scripts.
