from __future__ import annotations

from dataclasses import dataclass, field

from .products.compatibility.validator import validate_compatibility_payload
from .products.daily_horoscope.validator import validate_daily_payload
from .products.feng_shui.validator import validate_feng_shui_payload
from .products.lunar.validator import validate_lunar_payload
from .products.palm.validator import validate_palm_payload
from .products.tarot.validator import validate_tarot_payload


@dataclass(frozen=True)
class ValidationResult:
    product_key: str
    passed: bool
    issues: list[str] = field(default_factory=list)
    retry_hint: str | None = None

    @property
    def valid(self) -> bool:
        return self.passed


VALIDATORS = {
    "daily": validate_daily_payload,
    "lunar": validate_lunar_payload,
    "tarot": validate_tarot_payload,
    "compatibility": validate_compatibility_payload,
    "palm": validate_palm_payload,
    "feng_shui": validate_feng_shui_payload,
}

RETRY_HINTS = {
    "daily": "Correct the output into a true daily horoscope about today only. Use a recognisable daily structure and remove any year-ahead or Lunar framing.",
    "lunar": "Correct the output into a Lunar New Year year-ahead reading. Remove today-style wording, avoid duplicate sections, and keep the year-cycle frame explicit.",
    "tarot": "Correct the output into a card-led tarot reading. Name the actual cards or spread logic, explain symbolism, and synthesise the cards into guidance.",
    "compatibility": "Correct the output into a two-person compatibility reading. Make the relationship dynamics, strengths, tensions, and grounded guidance explicit.",
    "palm": "Correct the output into a palm-feature-led reading. Refer to palm lines, mounts, hand shape, or observed features and avoid generic divination prose.",
    "feng_shui": "Correct the output into a Feng Shui space analysis. Refer to rooms, layout, placement, flow, and practical recommendations.",
}


def validate_product_payload(product_key: str, payload: dict) -> ValidationResult:
    validator = VALIDATORS.get(product_key)
    if validator is None:
        return ValidationResult(product_key=product_key, passed=True, issues=[])
    issues = validator(payload)
    return ValidationResult(
        product_key=product_key,
        passed=not issues,
        issues=issues,
        retry_hint=None if not issues else RETRY_HINTS.get(product_key),
    )
