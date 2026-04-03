from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from generation.product_contracts import get_product_contract
from generation.validators import ValidationResult, validate_product_payload


@dataclass
class SitValidationSummary:
    status: str
    checks: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    hard_failures: list[str] = field(default_factory=list)
    validator: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


_PREVIEW_REQUIRED_META = {"persona_id", "llm_profile_id", "prompt_version", "theme_tags", "headline"}
_COMPAT_WARNING_PREFIXES = {
    "compatibility_missing_strength_or_tension_language",
    "compatibility_missing_two_person_structure",
}


def _require(payload: dict, key: str, failures: list[str], *, parent: str = "") -> Any:
    container = payload if not parent else payload.get(parent) or {}
    if not isinstance(container, dict) or key not in container:
        failures.append(f"missing:{parent + '.' if parent else ''}{key}")
        return None
    return container.get(key)


def _validate_preview_contract_fields(payload: dict, checks: list[str], hard_failures: list[str]) -> None:
    unlock_price = _require(payload, "unlock_price", hard_failures)
    product_id = _require(payload, "product_id", hard_failures)

    if isinstance(unlock_price, dict) and unlock_price.get("currency") and "amount" in unlock_price:
        checks.append("unlock_price_present")
    elif unlock_price is not None:
        hard_failures.append("invalid:unlock_price")

    if isinstance(product_id, str) and product_id.strip():
        checks.append("product_id_present")
    elif product_id is not None:
        hard_failures.append("invalid:product_id")



def validate_preview_payload(*, case_id: str, product_key: str, payload: dict) -> SitValidationSummary:
    checks: list[str] = []
    warnings: list[str] = []
    hard_failures: list[str] = []

    teaser = _require(payload, "teaser_text", hard_failures)
    if isinstance(teaser, str) and teaser.strip():
        checks.append("teaser_text_present")
    else:
        hard_failures.append("invalid:teaser_text")

    meta = _require(payload, "meta", hard_failures)
    if isinstance(meta, dict):
        missing_meta = sorted(_PREVIEW_REQUIRED_META - set(meta.keys()))
        if missing_meta:
            hard_failures.extend(f"missing:meta.{key}" for key in missing_meta)
        else:
            checks.append("preview_meta_complete")

    _validate_preview_contract_fields(payload, checks, hard_failures)

    if case_id == "combined_preview":
        if isinstance(payload.get("astrology_facts"), dict):
            checks.append("astrology_facts_present")
        else:
            hard_failures.append("missing:astrology_facts")
        tarot = payload.get("tarot")
        if isinstance(tarot, dict) and isinstance(tarot.get("cards"), list) and tarot["cards"]:
            checks.append("tarot_cards_present")
        else:
            hard_failures.append("invalid:tarot.cards")
        if not payload.get("flow_type") == "combined":
            hard_failures.append("invalid:flow_type")

    sections = payload.get("sections")
    if case_id == "compatibility_preview":
        contract = get_product_contract(product_key)
        expected = contract.expected_section_ids if contract else []
        section_ids = [section.get("id") for section in sections or [] if isinstance(section, dict)]
        if section_ids == expected:
            checks.append("compatibility_preview_sections_match_contract")
        else:
            hard_failures.append(f"invalid:sections.expected={expected}.actual={section_ids}")

    validation = ValidationResult(product_key=product_key, passed=True)
    if case_id in {"combined_preview", "compatibility_preview"}:
        validation = validate_product_payload(product_key, payload)
        for issue in validation.issues:
            if case_id == "compatibility_preview" and issue in _COMPAT_WARNING_PREFIXES:
                warnings.append(issue)
            else:
                hard_failures.append(issue)
        if not validation.issues:
            checks.append("product_validator_passed")

    status = "failed" if hard_failures else "passed_with_warnings" if warnings else "passed"
    return SitValidationSummary(
        status=status,
        checks=checks,
        warnings=warnings,
        hard_failures=hard_failures,
        validator={
            "product_key": validation.product_key,
            "passed": validation.passed,
            "issues": validation.issues,
            "retry_hint": validation.retry_hint,
        },
    )
