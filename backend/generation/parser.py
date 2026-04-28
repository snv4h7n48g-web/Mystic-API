from __future__ import annotations

import json

from .types import NormalizedMysticOutput


class GenerationParseError(ValueError):
    """Raised when structured model output cannot be parsed."""


REQUIRED_KEYS: set[str] = set()

_DAILY_SECTION_IDS = {
    "today_theme",
    "today_energy",
    "best_move",
    "watch_out_for",
    "people_energy",
    "work_focus",
    "timing",
    "closing_guidance",
}

_FENG_SHUI_SECTION_IDS = {
    "overview",
    "bagua_map",
    "energy_flow",
    "what_helps",
    "what_blocks",
    "practical_fixes",
    "priority_actions",
    "recommendations",
    "action_plan",
    "guidance",
}


def _parse_daily_sections(value: object) -> dict[str, dict[str, str]]:
    if value in (None, ""):
        return {}
    if not isinstance(value, dict):
        raise GenerationParseError("daily_sections must be an object")

    parsed: dict[str, dict[str, str]] = {}
    for key, raw_block in value.items():
        section_id = str(key)
        if section_id not in _DAILY_SECTION_IDS:
            continue
        if raw_block in (None, ""):
            continue
        if not isinstance(raw_block, dict):
            raise GenerationParseError(
                f"daily_sections.{section_id} must be an object"
            )
        headline = str(raw_block.get("headline") or "")
        detail = str(raw_block.get("detail") or "")
        if not headline and not detail:
            continue
        parsed[section_id] = {
            "headline": headline,
            "detail": detail,
        }
    return parsed


def _parse_tarot_card_chapters(value: object) -> list[dict[str, str]]:
    if value in (None, ""):
        return []
    if not isinstance(value, list):
        raise GenerationParseError("tarot_card_chapters must be a list")

    parsed: list[dict[str, str]] = []
    allowed_keys = {
        "card",
        "position",
        "orientation",
        "card_meaning",
        "position_meaning",
        "reversal_message",
        "question_relevance",
        "personal_implication",
    }
    for raw_item in value:
        if raw_item in (None, ""):
            continue
        if not isinstance(raw_item, dict):
            raise GenerationParseError("tarot_card_chapters entries must be objects")
        chapter = {
            key: str(raw_item.get(key) or "").strip()
            for key in allowed_keys
            if str(raw_item.get(key) or "").strip()
        }
        if chapter:
            parsed.append(chapter)
    return parsed


def _coalesce_text(payload: dict, *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _coalesce_daily_section(
    daily_sections: dict[str, dict[str, str]],
    *section_ids: str,
) -> str:
    for section_id in section_ids:
        section = daily_sections.get(section_id)
        if not section:
            continue
        text = " ".join(
            value.strip()
            for value in (section.get("headline", ""), section.get("detail", ""))
            if value and value.strip()
        ).strip()
        if text:
            return text
    return ""


def parse_normalized_output(raw_text: str) -> NormalizedMysticOutput:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise GenerationParseError(f"Invalid JSON output: {exc}") from exc

    daily_sections = _parse_daily_sections(payload.get("daily_sections"))
    tarot_card_chapters = _parse_tarot_card_chapters(payload.get("tarot_card_chapters"))
    feng_shui_sections = {
        section_id: str(payload.get(section_id) or "").strip()
        for section_id in _FENG_SHUI_SECTION_IDS
        if str(payload.get(section_id) or "").strip()
    }

    missing = REQUIRED_KEYS - set(payload.keys())
    if missing:
        raise GenerationParseError(f"Missing required keys: {sorted(missing)}")

    opening_hook = _coalesce_text(
        payload,
        "opening_hook",
        "reading_opening",
        "snapshot_core_theme",
        "current_pattern",
        "overview",
        "cycle_theme",
        "year_opening",
        "opening_invocation",
        "today_theme",
    ) or _coalesce_daily_section(daily_sections, "today_theme", "today_energy")
    current_pattern = _coalesce_text(
        payload,
        "current_pattern",
        "reading_opening",
        "astrological_foundation",
        "signals_agree",
        "tarot_message",
        "snapshot_core_theme",
        "what_helps",
        "bagua_map",
        "overview",
        "energy_flow",
        "lunar_forecast",
        "year_symbolism",
        "cycle_theme",
        "today_energy",
        "best_move",
    ) or _coalesce_daily_section(daily_sections, "today_energy", "today_theme", "best_move")
    emotional_truth = _coalesce_text(
        payload,
        "emotional_truth",
        "signals_agree",
        "tarot_message",
        "palm_revelation",
        "snapshot_main_tension",
        "astrological_foundation",
        "energy_flow",
        "integrated_synthesis",
        "welcome_release",
        "what_to_welcome_and_release",
        "watch_out_for",
        "what_blocks",
        "recommendations",
    ) or _coalesce_daily_section(daily_sections, "watch_out_for", "people_energy", "closing_guidance")

    practical_guidance = _coalesce_text(
        payload,
        "practical_guidance",
        "your_next_move",
        "priority_actions",
        "action_plan",
        "practical_fixes",
        "recommendations",
        "guidance",
        "move_well",
        "movement_guidance",
        "closing_guidance",
    ) or _coalesce_daily_section(daily_sections, "best_move", "timing", "closing_guidance")
    what_this_is_asking_of_you = _coalesce_text(
        payload,
        "what_this_is_asking_of_you",
        "what_to_welcome_and_release",
        "welcome_release",
        "integrated_synthesis",
        "what_blocks",
    )
    your_next_move = _coalesce_text(
        payload,
        "your_next_move",
        "priority_actions",
        "action_plan",
        "practical_fixes",
        "move_well",
        "movement_guidance",
    )

    missing_derived = [
        key
        for key, value in {
            "opening_hook": opening_hook,
            "current_pattern": current_pattern,
            "emotional_truth": emotional_truth,
        }.items()
        if not value
    ]
    if missing_derived:
        raise GenerationParseError(f"Missing required keys: {sorted(missing_derived)}")

    has_legacy_guidance = bool(practical_guidance)
    has_split_guidance = bool(what_this_is_asking_of_you) and bool(your_next_move)
    if not has_legacy_guidance and not has_split_guidance:
        raise GenerationParseError(
            "Missing guidance payload: expected practical_guidance or both what_this_is_asking_of_you and your_next_move"
        )

    theme_tags = payload.get("theme_tags") or []
    if not isinstance(theme_tags, list):
        raise GenerationParseError("theme_tags must be a list")

    return NormalizedMysticOutput(
        opening_hook=opening_hook,
        current_pattern=current_pattern,
        emotional_truth=emotional_truth,
        practical_guidance=practical_guidance,
        what_this_is_asking_of_you=what_this_is_asking_of_you,
        your_next_move=your_next_move,
        continuity_callback=(
            None
            if payload.get("continuity_callback") is None
            else str(payload.get("continuity_callback"))
        ),
        next_return_invitation=str(payload.get("next_return_invitation") or payload.get("premium_teaser") or ""),
        premium_teaser=(
            None if payload.get("premium_teaser") is None else str(payload.get("premium_teaser"))
        ),
        theme_tags=[str(tag) for tag in theme_tags],
        snapshot_core_theme=str(payload.get("snapshot_core_theme") or ""),
        snapshot_main_tension=str(payload.get("snapshot_main_tension") or ""),
        snapshot_best_next_move=str(payload.get("snapshot_best_next_move") or ""),
        reading_opening=str(payload.get("reading_opening") or ""),
        astrological_foundation=str(payload.get("astrological_foundation") or ""),
        palm_revelation=str(payload.get("palm_revelation") or ""),
        tarot_message=str(payload.get("tarot_message") or ""),
        signals_agree=str(payload.get("signals_agree") or ""),
        daily_sections=daily_sections,
        feng_shui_sections=feng_shui_sections,
        tarot_spread_overview=str(payload.get("tarot_spread_overview") or ""),
        tarot_card_chapters=tarot_card_chapters,
        tarot_spread_story=str(payload.get("tarot_spread_story") or ""),
    )
