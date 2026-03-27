from __future__ import annotations

from dataclasses import dataclass, field

from .products.daily_horoscope.validator import validate_daily_payload
from .products.lunar.validator import validate_lunar_payload
from .products.tarot.validator import validate_tarot_payload


@dataclass(frozen=True)
class ValidationResult:
    product_key: str
    valid: bool
    issues: list[str] = field(default_factory=list)


VALIDATORS = {
    "daily": validate_daily_payload,
    "lunar": validate_lunar_payload,
    "tarot": validate_tarot_payload,
}


def validate_product_payload(product_key: str, payload: dict) -> ValidationResult:
    validator = VALIDATORS.get(product_key)
    if validator is None:
        return ValidationResult(product_key=product_key, valid=True, issues=[])
    issues = validator(payload)
    return ValidationResult(product_key=product_key, valid=not issues, issues=issues)
