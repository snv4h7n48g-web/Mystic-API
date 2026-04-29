from __future__ import annotations

import re
from typing import Any

_NUMBERED_STEP_RE = re.compile(r"(?:(?<=^)|(?<=\s))([1-9]\d?)\.\s+")


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


def _split_numbered_steps(text: str) -> list[str]:
    cleaned = _clean(text)
    matches = list(_NUMBERED_STEP_RE.finditer(cleaned))
    if not matches:
        return []
    if len(matches) == 1 and not cleaned.startswith(f"{matches[0].group(1)}."):
        return []

    steps: list[str] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(cleaned)
        body = cleaned[start:end].strip()
        if body:
            steps.append(f"{match.group(1)}. {body}")
    return steps


def _format_step_section(text: str, *, intro: str) -> str:
    cleaned = _clean(text)
    if not cleaned:
        return ""
    steps = _split_numbered_steps(cleaned)
    if not steps:
        return _paragraphs(cleaned)
    return f"{_ensure_sentence(intro)}\n\n" + "\n\n".join(steps)


def _trim_practical_fixes_tail(text: str) -> str:
    cleaned = _clean(text)
    cut_points = [
        cleaned.find(marker)
        for marker in (
            " Start by ",
            " First, ",
            " 1. Clear one obvious obstruction",
        )
        if cleaned.find(marker) > 0
    ]
    if not cut_points:
        return cleaned
    return cleaned[: min(cut_points)].strip()


def format_practical_fixes_text(text: str) -> str:
    return _format_step_section(
        _trim_practical_fixes_tail(text),
        intro="Focus on these practical fixes.",
    )


def format_action_plan_text(text: str) -> str:
    return _format_step_section(
        text,
        intro="Move through the space in this order.",
    )


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


def _section_value(normalized, *keys: str) -> str:
    sections = getattr(normalized, "feng_shui_sections", {}) or {}
    for key in keys:
        value = _clean(sections.get(key))
        if value:
            return value
    return ""


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


def _what_helps_fallback(analysis: dict[str, Any]) -> str:
    room = _room_label(analysis)
    direction = _direction_label(analysis)
    goals = _goals_label(analysis)
    direction_line = (
        f"The {direction} emphasis can help this {room} when that side is kept clear, intentional, and connected to the room's main purpose."
        if direction
        else f"The strongest support in this {room} will come from anything that makes the room's purpose obvious as soon as someone enters."
    )
    goal_line = (
        f"Because the space is being asked to support {goals}, protect the zones that already feel steady, visible, and easy to use."
        if goals
        else "Keep the pieces that create calm sightlines, easy circulation, and a clear place for the eye to rest."
    )
    return _paragraphs(
        direction_line,
        goal_line,
        "Those strengths matter because Feng Shui works best when the useful parts of a room are amplified before new cures are added.",
    )


def _what_blocks_fallback(analysis: dict[str, Any]) -> str:
    room = _room_label(analysis)
    direction = _direction_label(analysis)
    direction_phrase = f" near the {direction} emphasis" if direction else ""
    return _paragraphs(
        f"The main block to watch in this {room} is fragmented attention: too many visual anchors, unclear pathways, or crowded surfaces{direction_phrase} can make the room feel busy before it feels supportive.",
        "When circulation, focal points, and storage are all competing, chi turns into small hesitation points: the body pauses, the eye bounces, and the room asks for effort instead of giving support.",
    )


def _practical_fixes_fallback(analysis: dict[str, Any]) -> str:
    room = _room_label(analysis)
    direction = _direction_label(analysis)
    target = f" on the {direction} side" if direction else ""
    return _paragraphs(
        f"1. Clear one obvious obstruction{target} so the {room} has a cleaner entry point for attention and movement; this improves flow before any decorative cure is needed.",
        f"2. Anchor one focal zone in the {room} with the strongest piece already present, then remove nearby items that compete with it; the room should know what it is organised around.",
        "3. Open the main circulation path by shifting furniture, baskets, side tables, or trailing objects out of the body's natural route; chi follows the path people actually use.",
        "4. Add one balancing cue only after clearing: warmer light, a living plant, a calmer textile, or one meaningful object that reinforces the goal instead of adding more noise.",
    )


def _action_plan_fallback(analysis: dict[str, Any]) -> str:
    room = _room_label(analysis)
    goals = _goals_label(analysis)
    goal_clause = (
        f" and whether the room makes {goals} easier to sustain"
        if goals
        else ""
    )
    return _paragraphs(
        f"Start with the one change that clears movement through the {room}; if the path feels easier, every later adjustment will read more clearly.",
        "Next, stabilise the focal zone and remove the object that creates the most visual static. Do not add new decor until the room has stopped scattering attention.",
        f"After 24 hours, return and notice whether your body settles faster on entry{goal_clause}. That felt response is the best early measure of whether the Feng Shui adjustment is working.",
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
        _what_blocks_fallback(analysis),
    )
    actions = _pick(
        used,
        getattr(normalized, "practical_guidance", ""),
        getattr(normalized, "your_next_move", ""),
        _practical_fixes_fallback(analysis),
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
    explicit_overview = _section_value(normalized, "overview")
    explicit_what_helps = _section_value(normalized, "what_helps", "bagua_map")
    explicit_what_blocks = _section_value(normalized, "what_blocks", "energy_flow")
    explicit_practical_fixes = _section_value(normalized, "practical_fixes", "priority_actions", "recommendations")
    explicit_action_plan = _section_value(normalized, "action_plan", "guidance")

    overview = _pick(
        used,
        explicit_overview,
        getattr(normalized, "reading_opening", ""),
        getattr(normalized, "opening_hook", ""),
        _overview_fallback(analysis),
    )
    what_helps = _pick(
        used,
        explicit_what_helps,
        getattr(normalized, "current_pattern", ""),
        getattr(normalized, "snapshot_core_theme", ""),
        _what_helps_fallback(analysis),
    )
    what_blocks = _pick(
        used,
        explicit_what_blocks,
        getattr(normalized, "emotional_truth", ""),
        getattr(normalized, "continuity_callback", ""),
        getattr(normalized, "snapshot_main_tension", ""),
        _what_blocks_fallback(analysis),
    )
    practical_fixes = _pick(
        used,
        explicit_practical_fixes,
        getattr(normalized, "practical_guidance", ""),
        getattr(normalized, "your_next_move", ""),
        getattr(normalized, "snapshot_best_next_move", ""),
        _practical_fixes_fallback(analysis),
    )
    action_plan = _pick(
        used,
        explicit_action_plan,
        getattr(normalized, "what_this_is_asking_of_you", ""),
        getattr(normalized, "your_next_move", ""),
        getattr(normalized, "next_return_invitation", ""),
        _action_plan_fallback(analysis),
    )

    return {
        "overview": _paragraphs(explicit_overview) if explicit_overview else _section_text(
            overview,
            _dedupe_join(
                getattr(normalized, "reading_opening", ""),
                getattr(normalized, "opening_hook", ""),
                _overview_fallback(analysis),
            ),
        ),
        "what_helps": _paragraphs(explicit_what_helps) if explicit_what_helps else _section_text(
            what_helps,
            _dedupe_join(
                getattr(normalized, "current_pattern", ""),
                _what_helps_fallback(analysis),
            ),
        ),
        "what_blocks": _paragraphs(explicit_what_blocks) if explicit_what_blocks else _section_text(
            what_blocks,
            _dedupe_join(
                getattr(normalized, "emotional_truth", ""),
                getattr(normalized, "continuity_callback", ""),
                _what_blocks_fallback(analysis),
            ),
        ),
        "practical_fixes": format_practical_fixes_text(
            explicit_practical_fixes or practical_fixes,
        ),
        "action_plan": format_action_plan_text(explicit_action_plan) if explicit_action_plan else _section_text(
            action_plan,
            _dedupe_join(
                getattr(normalized, "what_this_is_asking_of_you", ""),
                getattr(normalized, "next_return_invitation", ""),
                _action_plan_fallback(analysis),
            ),
        ),
    }
