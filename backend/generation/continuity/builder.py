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


def _continuity_rank(item: dict, *, current_flow_type: str | None, current_object_type: str | None) -> tuple[int, int]:
    flow_type = str(item.get("flow_type") or "")
    source_type = str(item.get("source_type") or "")
    score = 0

    if current_flow_type and flow_type == current_flow_type:
        score += 4
    if current_object_type and current_object_type in source_type:
        score += 3
    if source_type.endswith("reading") or source_type.endswith("analysis"):
        score += 2
    elif source_type.endswith("preview"):
        score += 1

    # Secondary tiebreaker is recency order from repository query.
    return (score, 0)



def build_continuity_context(
    *,
    user_id: Optional[str],
    session_id: Optional[str],
    current_flow_type: Optional[str] = None,
    current_object_type: Optional[str] = None,
) -> dict | None:
    """Build a compact, fact-backed continuity payload.

    Continuity is primarily account-level. Keep the payload intentionally small
    so prompt cost and latency stay bounded.
    """
    if not user_id:
        return None

    items = get_recent_user_generation_metadata(user_id=user_id, limit=4)
    if not items:
        return None

    ranked_items = sorted(
        enumerate(items),
        key=lambda pair: (_continuity_rank(pair[1], current_flow_type=current_flow_type, current_object_type=current_object_type), -pair[0]),
        reverse=True,
    )
    selected_items = [item for _, item in ranked_items[:MAX_RECENT_ITEMS]]
    latest = selected_items[0]
    recent_items = selected_items

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
        "current_flow_type": current_flow_type,
        "current_object_type": current_object_type,
        "recent_theme_tags": _dedupe_tags(recent_theme_tags),
        "recent_persona_ids": recent_persona_ids[:2],
        "recent_flow_types": recent_flow_types[:2],
        "factual_callbacks": factual_callbacks[:1],
    }
