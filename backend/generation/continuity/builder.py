from __future__ import annotations

from typing import Optional

from .repository import get_recent_user_generation_metadata

MAX_THEME_TAGS = 5
MAX_RECENT_ITEMS = 2
MAX_HEADLINE_CHARS = 140


def _trim_text(value: str | None, max_chars: int = MAX_HEADLINE_CHARS) -> str | None:
    if not value:
        return None
    text = " ".join(str(value).split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def _dedupe_tags(items: list[str], limit: int = MAX_THEME_TAGS) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = item.strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(item.strip())
        if len(result) >= limit:
            break
    return result


def build_continuity_context(*, user_id: Optional[str], session_id: Optional[str]) -> dict | None:
    """Build a compact, fact-backed continuity payload.

    Continuity is primarily account-level. Keep the payload intentionally small
    so prompt cost and latency stay bounded.
    """
    if not user_id:
        return None

    items = get_recent_user_generation_metadata(user_id=user_id, limit=4)
    if not items:
        return None

    latest = items[0]
    recent_items = items[:MAX_RECENT_ITEMS]

    recent_theme_tags: list[str] = []
    recent_persona_ids: list[str] = []
    recent_flow_types: list[str] = []
    for item in recent_items:
        recent_theme_tags.extend(item.get("theme_tags") or [])
        persona_id = item.get("persona_id")
        flow_type = item.get("flow_type")
        if persona_id and persona_id not in recent_persona_ids:
            recent_persona_ids.append(str(persona_id))
        if flow_type and flow_type not in recent_flow_types:
            recent_flow_types.append(str(flow_type))

    latest_headline = _trim_text(latest.get("headline"))
    factual_callbacks: list[str] = []
    if latest_headline:
        factual_callbacks.append(f"Your latest reading focused on: {latest_headline}")

    return {
        "user_id": user_id,
        "session_id": session_id,
        "latest_headline": latest_headline,
        "latest_flow_type": latest.get("flow_type"),
        "latest_persona_id": latest.get("persona_id"),
        "recent_theme_tags": _dedupe_tags(recent_theme_tags),
        "recent_persona_ids": recent_persona_ids[:2],
        "recent_flow_types": recent_flow_types[:2],
        "factual_callbacks": factual_callbacks[:1],
    }
