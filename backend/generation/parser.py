from __future__ import annotations

import json

from .types import NormalizedMysticOutput


class GenerationParseError(ValueError):
    """Raised when structured model output cannot be parsed."""


REQUIRED_KEYS = {
    "opening_hook",
    "current_pattern",
    "emotional_truth",
    "continuity_callback",
    "premium_teaser",
    "theme_tags",
}


def parse_normalized_output(raw_text: str) -> NormalizedMysticOutput:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise GenerationParseError(f"Invalid JSON output: {exc}") from exc

    missing = REQUIRED_KEYS - set(payload.keys())
    if missing:
        raise GenerationParseError(f"Missing required keys: {sorted(missing)}")

    has_legacy_guidance = "practical_guidance" in payload
    has_split_guidance = (
        "what_this_is_asking_of_you" in payload and "your_next_move" in payload
    )
    if not has_legacy_guidance and not has_split_guidance:
        raise GenerationParseError(
            "Missing guidance payload: expected practical_guidance or both what_this_is_asking_of_you and your_next_move"
        )

    theme_tags = payload.get("theme_tags") or []
    if not isinstance(theme_tags, list):
        raise GenerationParseError("theme_tags must be a list")

    return NormalizedMysticOutput(
        opening_hook=str(payload["opening_hook"]),
        current_pattern=str(payload["current_pattern"]),
        emotional_truth=str(payload["emotional_truth"]),
        practical_guidance=str(payload.get("practical_guidance") or ""),
        what_this_is_asking_of_you=str(payload.get("what_this_is_asking_of_you") or ""),
        your_next_move=str(payload.get("your_next_move") or ""),
        continuity_callback=(
            None if payload["continuity_callback"] is None else str(payload["continuity_callback"])
        ),
        next_return_invitation=str(payload.get("next_return_invitation") or payload.get("premium_teaser") or ""),
        premium_teaser=None if payload["premium_teaser"] is None else str(payload["premium_teaser"]),
        theme_tags=[str(tag) for tag in theme_tags],
    )
