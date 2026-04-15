from __future__ import annotations

from typing import Any


def _clean(text: str | None) -> str:
    return " ".join((text or "").split()).strip()


def _ensure_sentence(text: str) -> str:
    cleaned = _clean(text)
    if not cleaned:
        return ""
    if cleaned[-1] in ".!?":
        return cleaned
    return f"{cleaned}."


def _paragraphs(*parts: str) -> str:
    paragraphs = [_ensure_sentence(part) for part in parts if _clean(part)]
    return "\n\n".join(paragraphs).strip()


def _dedupe_join(*parts: str) -> str:
    seen: set[str] = set()
    cleaned_parts: list[str] = []
    for part in parts:
        cleaned = _clean(part)
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned_parts.append(cleaned)
    return " ".join(cleaned_parts).strip()


def _pick(used: set[str], *candidates: str) -> str:
    for candidate in candidates:
        cleaned = _clean(candidate)
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in used:
            continue
        used.add(key)
        return cleaned
    return ""


def _room_label(analysis: dict[str, Any]) -> str:
    return _clean(analysis.get("room_purpose")) or "space"


def _direction_label(analysis: dict[str, Any]) -> str:
    return _clean(analysis.get("compass_direction"))


def _goals_label(analysis: dict[str, Any]) -> str:
    return _clean(analysis.get("user_goals"))


def _overview_fallback(analysis: dict[str, Any]) -> str:
    room = _room_label(analysis)
    goals = _goals_label(analysis)
    direction = _direction_label(analysis)
    direction_phrase = f", facing {direction}," if direction else ""
    goals_phrase = f" in support of {goals}" if goals else ""
    return (
        f"This {room}{direction_phrase} is carrying the strongest Feng Shui signal first: "
        f"how the room is currently holding or scattering momentum{goals_phrase}."
    )


def _bagua_fallback(analysis: dict[str, Any]) -> str:
    room = _room_label(analysis)
    direction = _direction_label(analysis)
    goals = _goals_label(analysis)
    direction_sentence = (
        f"The directional emphasis is {direction}, so placement, sightlines, and what occupies that side of the {room} matter more than surface styling."
        if direction
        else f"Bagua pressure in this {room} is less about decoration than about whether the most important parts of the layout are supported or obstructed."
    )
    goal_sentence = (
        f"Because the room is being asked to support {goals}, the strongest symbolic read comes from whether the layout reinforces that goal or keeps splitting attention away from it."
        if goals
        else "The key symbolic question is whether the layout reinforces the room's purpose or quietly drains it."
    )
    return _paragraphs(direction_sentence, goal_sentence)


def _energy_fallback(analysis: dict[str, Any]) -> str:
    room = _room_label(analysis)
    return _paragraphs(
        f"Energy flow in this {room} should feel guided, not crowded: paths need to be legible, anchor points need breathing room, and the eye should know where to settle first.",
        "When a room holds too many competing signals at once, chi tends to fragment into low-grade friction rather than steady support.",
    )


def _priority_fallback(analysis: dict[str, Any]) -> str:
    room = _room_label(analysis)
    direction = _direction_label(analysis)
    target = f" on the {direction} side" if direction else ""
    return _paragraphs(
        f"1. Clear one obvious obstruction{target} so the {room} has a cleaner entry point for attention and movement.",
        f"2. Choose one focal zone in the {room} and make it visually stable instead of letting several competing objects lead the eye.",
        "3. Remove or relocate anything that creates visual noise near the main circulation path, because flow improves fastest when the room stops making the body hesitate.",
    )


def _recommendations_fallback(analysis: dict[str, Any]) -> str:
    goals = _goals_label(analysis)
    goal_line = (
        f"Treat every adjustment as a test of whether the room is helping {goals} become easier to sustain."
        if goals
        else "Treat each adjustment as a test of whether the room feels easier to inhabit and easier to use well."
    )
    return _paragraphs(
        goal_line,
        "Favor changes that improve placement, circulation, and visual calm before adding more symbolic cures or decorative fixes.",
        "The most effective Feng Shui recommendation is usually the one that removes confusion from the room first and only then adds support.",
    )


def _guidance_fallback(analysis: dict[str, Any]) -> str:
    room = _room_label(analysis)
    return _paragraphs(
        f"Return to this {room} after the first round of changes and notice whether your body relaxes, focuses, or keeps bracing in the same places.",
        "A good Feng Shui adjustment should feel measurable in how the room moves, not just in how it photographs.",
    )


def _section_text(summary: str, detail: str) -> str:
    summary_clean = _clean(summary)
    detail_clean = _clean(detail)
    if not summary_clean:
        return _paragraphs(detail_clean)
    if not detail_clean:
        return _ensure_sentence(summary_clean)
    if detail_clean.casefold().startswith(summary_clean.casefold()):
        return _paragraphs(detail_clean)
    return _paragraphs(summary_clean, detail_clean)


def map_feng_shui_preview(normalized, analysis: dict[str, Any] | None = None) -> dict[str, str]:
    analysis = analysis or {}
    used: set[str] = set()
    overview = _pick(
        used,
        getattr(normalized, "opening_hook", ""),
        getattr(normalized, "reading_opening", ""),
        _overview_fallback(analysis),
    )
    energy = _pick(
        used,
        getattr(normalized, "current_pattern", ""),
        getattr(normalized, "emotional_truth", ""),
        _energy_fallback(analysis),
    )
    actions = _pick(
        used,
        getattr(normalized, "practical_guidance", ""),
        getattr(normalized, "your_next_move", ""),
        _priority_fallback(analysis),
    )
    teaser = _dedupe_join(overview, energy, actions)
    return {
        "headline": overview,
        "teaser_text": teaser or overview,
    }


def map_feng_shui_analysis(
    normalized,
    *,
    analysis: dict[str, Any] | None = None,
    vision_result: dict[str, Any] | None = None,
) -> dict[str, str]:
    analysis = analysis or {}
    _ = vision_result or {}
    used: set[str] = set()

    overview = _pick(
        used,
        getattr(normalized, "reading_opening", ""),
        getattr(normalized, "opening_hook", ""),
        _overview_fallback(analysis),
    )
    bagua = _pick(
        used,
        getattr(normalized, "current_pattern", ""),
        getattr(normalized, "snapshot_core_theme", ""),
        _bagua_fallback(analysis),
    )
    energy = _pick(
        used,
        getattr(normalized, "emotional_truth", ""),
        getattr(normalized, "continuity_callback", ""),
        getattr(normalized, "snapshot_main_tension", ""),
        _energy_fallback(analysis),
    )
    priority = _pick(
        used,
        getattr(normalized, "practical_guidance", ""),
        getattr(normalized, "your_next_move", ""),
        getattr(normalized, "snapshot_best_next_move", ""),
        _priority_fallback(analysis),
    )
    recommendations = _pick(
        used,
        getattr(normalized, "what_this_is_asking_of_you", ""),
        getattr(normalized, "premium_teaser", ""),
        getattr(normalized, "practical_guidance", ""),
        _recommendations_fallback(analysis),
    )
    guidance = _pick(
        used,
        getattr(normalized, "next_return_invitation", ""),
        getattr(normalized, "premium_teaser", ""),
        _guidance_fallback(analysis),
    )

    return {
        "overview": _section_text(
            overview,
            _dedupe_join(
                getattr(normalized, "reading_opening", ""),
                getattr(normalized, "opening_hook", ""),
                _overview_fallback(analysis),
            ),
        ),
        "bagua_map": _section_text(
            bagua,
            _dedupe_join(
                getattr(normalized, "current_pattern", ""),
                _bagua_fallback(analysis),
            ),
        ),
        "energy_flow": _section_text(
            energy,
            _dedupe_join(
                getattr(normalized, "emotional_truth", ""),
                getattr(normalized, "continuity_callback", ""),
                _energy_fallback(analysis),
            ),
        ),
        "priority_actions": _section_text(
            priority,
            _dedupe_join(
                getattr(normalized, "practical_guidance", ""),
                getattr(normalized, "your_next_move", ""),
                _priority_fallback(analysis),
            ),
        ),
        "recommendations": _section_text(
            recommendations,
            _dedupe_join(
                getattr(normalized, "what_this_is_asking_of_you", ""),
                getattr(normalized, "premium_teaser", ""),
                _recommendations_fallback(analysis),
            ),
        ),
        "guidance": _section_text(
            guidance,
            _dedupe_join(
                getattr(normalized, "next_return_invitation", ""),
                _guidance_fallback(analysis),
            ),
        ),
    }
