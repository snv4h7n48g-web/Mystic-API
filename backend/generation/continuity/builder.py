from __future__ import annotations

from typing import Optional


def build_continuity_context(*, user_id: Optional[str], session_id: Optional[str]) -> dict | None:
    """Phase-1 placeholder: continuity remains opt-in and fact-backed only."""
    if not user_id and not session_id:
        return None
    return {
        "user_id": user_id,
        "session_id": session_id,
        "factual_callbacks": [],
    }
