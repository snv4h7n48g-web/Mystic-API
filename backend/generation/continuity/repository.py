from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import text

from user_service import engine


def _coerce_tags(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def get_recent_user_generation_metadata(user_id: str, limit: int = 4) -> list[dict[str, Any]]:
    query = text(
        """
        SELECT * FROM (
            SELECT
                s.id::text AS source_id,
                'session_reading' AS source_type,
                s.created_at,
                s.reading_persona_id AS persona_id,
                s.reading_headline AS headline,
                s.reading_theme_tags AS theme_tags,
                COALESCE(s.inputs->>'flow_type', 'combined') AS flow_type
            FROM sessions s
            JOIN user_sessions us ON us.session_id = s.id
            WHERE us.user_id = :user_id
              AND s.reading_headline IS NOT NULL

            UNION ALL

            SELECT
                s.id::text AS source_id,
                'session_preview' AS source_type,
                s.created_at,
                s.preview_persona_id AS persona_id,
                s.preview_headline AS headline,
                s.preview_theme_tags AS theme_tags,
                COALESCE(s.inputs->>'flow_type', 'combined') AS flow_type
            FROM sessions s
            JOIN user_sessions us ON us.session_id = s.id
            WHERE us.user_id = :user_id
              AND s.preview_headline IS NOT NULL

            UNION ALL

            SELECT
                c.id::text AS source_id,
                'compatibility_reading' AS source_type,
                c.created_at,
                c.reading_persona_id AS persona_id,
                c.reading_headline AS headline,
                c.reading_theme_tags AS theme_tags,
                'compatibility' AS flow_type
            FROM compatibility_readings c
            WHERE c.user_id = :user_id
              AND c.reading_headline IS NOT NULL

            UNION ALL

            SELECT
                c.id::text AS source_id,
                'compatibility_preview' AS source_type,
                c.created_at,
                c.preview_persona_id AS persona_id,
                c.preview_headline AS headline,
                c.preview_theme_tags AS theme_tags,
                'compatibility' AS flow_type
            FROM compatibility_readings c
            WHERE c.user_id = :user_id
              AND c.preview_headline IS NOT NULL

            UNION ALL

            SELECT
                f.id::text AS source_id,
                'feng_shui_analysis' AS source_type,
                f.created_at,
                f.analysis_persona_id AS persona_id,
                f.analysis_headline AS headline,
                f.analysis_theme_tags AS theme_tags,
                'feng_shui' AS flow_type
            FROM feng_shui_analyses f
            WHERE f.user_id = :user_id
              AND f.analysis_headline IS NOT NULL

            UNION ALL

            SELECT
                f.id::text AS source_id,
                'feng_shui_preview' AS source_type,
                f.created_at,
                f.preview_persona_id AS persona_id,
                f.preview_headline AS headline,
                f.preview_theme_tags AS theme_tags,
                'feng_shui' AS flow_type
            FROM feng_shui_analyses f
            WHERE f.user_id = :user_id
              AND f.preview_headline IS NOT NULL
        ) history
        ORDER BY created_at DESC
        LIMIT :limit
        """
    )
    with engine.begin() as conn:
        rows = conn.execute(query, {"user_id": user_id, "limit": limit}).mappings().all()

    results: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["theme_tags"] = _coerce_tags(item.get("theme_tags"))
        results.append(item)
    return results


def get_latest_user_generation_metadata(user_id: str) -> Optional[dict[str, Any]]:
    items = get_recent_user_generation_metadata(user_id=user_id, limit=1)
    return items[0] if items else None
