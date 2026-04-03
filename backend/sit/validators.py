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
_READING_REQUIRED_META = {"persona_id", "llm_profile_id", "prompt_version", "theme_tags", "headline"}
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


def _meta_container(payload: dict) -> tuple[str | None, dict[str, Any]]:
    candidates: list[tuple[str, dict[str, Any]]] = []
    for key in ("meta", "metadata"):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.append((key, value))
    if not candidates:
        return None, {}
    preferred = max(candidates, key=lambda item: len(item[1]))
    return preferred


def _validation_result_for(product_key: str, payload: dict) -> ValidationResult:
    return validate_product_payload(product_key, payload)


def _build_summary(*, checks: list[str], warnings: list[str], hard_failures: list[str], validation: ValidationResult) -> SitValidationSummary:
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


def _validate_contract_section_ids(
    *,
    payload: dict,
    product_key: str,
    checks: list[str],
    hard_failures: list[str],
    allow_subset: bool = False,
    required_subset: set[str] | None = None,
) -> None:
    contract = get_product_contract(product_key)
    if not contract:
        return
    sections = payload.get("sections")
    if not isinstance(sections, list):
        hard_failures.append("invalid:sections")
        return
    actual = [section.get("id") for section in sections if isinstance(section, dict)]
    expected = contract.expected_section_ids
    if allow_subset:
        unexpected = [section_id for section_id in actual if section_id not in expected]
        missing_required = sorted((required_subset or set()) - set(actual))
        if unexpected:
            hard_failures.append(f"invalid:sections.unexpected={unexpected}")
        if missing_required:
            hard_failures.extend(f"missing:sections.{section_id}" for section_id in missing_required)
        if not unexpected and not missing_required:
            checks.append("reading_sections_match_contract_subset")
        return
    if actual == expected:
        checks.append("reading_sections_match_contract")
    else:
        hard_failures.append(f"invalid:sections.expected={expected}.actual={actual}")


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

    meta_key, meta = _meta_container(payload)
    if meta_key:
        missing_meta = sorted(_PREVIEW_REQUIRED_META - set(meta.keys()))
        if missing_meta:
            hard_failures.extend(f"missing:{meta_key}.{key}" for key in missing_meta)
        else:
            checks.append(f"preview_meta_complete:{meta_key}")
    else:
        hard_failures.append("missing:meta")

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
        if payload.get("flow_type") != "combined":
            hard_failures.append("invalid:flow_type")

    elif case_id == "daily_preview":
        if payload.get("flow_type") != "daily_horoscope":
            hard_failures.append("invalid:flow_type")
        if isinstance(payload.get("astrology_facts"), dict) and payload["astrology_facts"]:
            checks.append("daily_astrology_facts_present")
        else:
            hard_failures.append("missing:astrology_facts")
        preview_shape = {"headline", "today_energy", "best_move_teaser", "watch_out_teaser", "deeper_layer_teaser"}
        if preview_shape & set(payload.keys()):
            checks.append("daily_preview_specialized_shape_detected")
        else:
            checks.append("daily_preview_generic_shape_accepted")

    elif case_id == "tarot_solo_preview":
        if payload.get("flow_type") != "tarot_solo":
            hard_failures.append("invalid:flow_type")
        tarot = payload.get("tarot")
        if isinstance(tarot, dict) and isinstance(tarot.get("cards"), list) and tarot["cards"]:
            checks.append("tarot_cards_present")
        else:
            hard_failures.append("invalid:tarot.cards")
        preview_shape = {"headline", "card_message", "guidance_teaser", "deeper_layer_teaser"}
        if preview_shape & set(payload.keys()):
            checks.append("tarot_preview_specialized_shape_detected")
        else:
            checks.append("tarot_preview_generic_shape_accepted")

    elif case_id == "compatibility_preview":
        _validate_contract_section_ids(payload=payload, product_key=product_key, checks=checks, hard_failures=hard_failures)

    elif case_id == "feng_shui_preview":
        if isinstance(payload.get("analysis_type"), str) and payload["analysis_type"].strip():
            checks.append("analysis_type_present")
        else:
            hard_failures.append("missing:analysis_type")
        _validate_contract_section_ids(payload=payload, product_key=product_key, checks=checks, hard_failures=hard_failures)

    validation = ValidationResult(product_key=product_key, passed=True)
    if case_id in {
        "combined_preview",
        "compatibility_preview",
        "daily_preview",
        "feng_shui_preview",
    }:
        validation = _validation_result_for(product_key, payload)
        for issue in validation.issues:
            if case_id == "compatibility_preview" and issue in _COMPAT_WARNING_PREFIXES:
                warnings.append(issue)
            else:
                hard_failures.append(issue)
        if not validation.issues:
            checks.append("product_validator_passed")

    return _build_summary(checks=checks, warnings=warnings, hard_failures=hard_failures, validation=validation)


def validate_reading_payload(*, case_id: str, product_key: str, payload: dict) -> SitValidationSummary:
    checks: list[str] = []
    warnings: list[str] = []
    hard_failures: list[str] = []

    sections = payload.get("sections")
    if isinstance(sections, list) and sections:
        checks.append("sections_present")
    else:
        hard_failures.append("invalid:sections")

    full_text = payload.get("full_text")
    if isinstance(full_text, str) and full_text.strip():
        checks.append("full_text_present")
    else:
        hard_failures.append("invalid:full_text")

    meta_key, meta = _meta_container(payload)
    if meta_key:
        missing_meta = sorted(_READING_REQUIRED_META - set(meta.keys()))
        if missing_meta:
            hard_failures.extend(f"missing:{meta_key}.{key}" for key in missing_meta)
        else:
            checks.append(f"reading_meta_complete:{meta_key}")
    else:
        hard_failures.append("missing:metadata")

    if case_id == "combined_full_reading":
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        if metadata.get("flow_type") == "combined":
            checks.append("combined_flow_type_metadata_present")
        else:
            hard_failures.append("invalid:metadata.flow_type")
        _validate_contract_section_ids(payload=payload, product_key=product_key, checks=checks, hard_failures=hard_failures)
    elif case_id == "daily_full_reading":
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        if metadata.get("flow_type") == "daily_horoscope":
            checks.append("daily_flow_type_metadata_present")
        else:
            hard_failures.append("invalid:metadata.flow_type")
        _validate_contract_section_ids(
            payload=payload,
            product_key=product_key,
            checks=checks,
            hard_failures=hard_failures,
            allow_subset=True,
            required_subset={"today_theme", "today_energy", "best_move", "watch_out_for", "closing_guidance"},
        )
    elif case_id == "compatibility_full_reading":
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        if metadata.get("flow_type") == "compatibility":
            checks.append("compatibility_flow_type_metadata_present")
        else:
            hard_failures.append("invalid:metadata.flow_type")
        _validate_contract_section_ids(payload=payload, product_key=product_key, checks=checks, hard_failures=hard_failures)

    validation = _validation_result_for(product_key, payload)
    for issue in validation.issues:
        hard_failures.append(issue)
    if not validation.issues:
        checks.append("product_validator_passed")

    return _build_summary(checks=checks, warnings=warnings, hard_failures=hard_failures, validation=validation)
