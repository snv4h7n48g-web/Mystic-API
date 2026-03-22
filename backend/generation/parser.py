from __future__ import annotations

import json

from .types import NormalizedMysticOutput


class GenerationParseError(ValueError):
    """Raised when structured model output cannot be parsed."""


REQUIRED_KEYS = {
    "opening_hook",
    "current_pattern",
    "emotional_truth",
    "practical_guidance",
    "continuity_callback",
    "next_return_invitation",
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

    theme_tags = payload.get("theme_tags") or []
    if not isinstance(theme_tags, list):
        raise GenerationParseError("theme_tags must be a list")

    return NormalizedMysticOutput(
        opening_hook=str(payload["opening_hook"]),
        current_pattern=str(payload["current_pattern"]),
        emotional_truth=str(payload["emotional_truth"]),
        practical_guidance=str(payload["practical_guidance"]),
        continuity_callback=(
            None if payload["continuity_callback"] is None else str(payload["continuity_callback"])
        ),
        next_return_invitation=str(payload["next_return_invitation"]),
        premium_teaser=None if payload["premium_teaser"] is None else str(payload["premium_teaser"]),
        theme_tags=[str(tag) for tag in theme_tags],
    )
