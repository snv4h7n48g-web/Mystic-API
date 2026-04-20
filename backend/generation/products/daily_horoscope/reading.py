from __future__ import annotations

from .mapper import map_daily_reading


def _build_section(section_id: str, title: str, block: dict[str, str]) -> dict:
    headline = (block.get("headline") or "").strip()
    detail = (block.get("detail") or "").strip()
    text = (block.get("text") or detail or headline).strip()
    payload = {
        "id": section_id,
        "title": title,
        "text": text,
    }
    if headline:
        payload["headline"] = headline
    if detail:
        payload["detail"] = detail
    return payload


def build_daily_horoscope_reading_payload(*, normalized, metadata):
    mapped = map_daily_reading(normalized)
    sections = [
        _build_section("today_theme", "TODAY'S THEME", mapped["today_theme"]),
        _build_section("today_energy", "TODAY'S ENERGY", mapped["today_energy"]),
        _build_section("best_move", "BEST MOVE", mapped["best_move"]),
        _build_section("watch_out_for", "WATCH OUT FOR", mapped["watch_out_for"]),
        _build_section("people_energy", "PEOPLE ENERGY", mapped["people_energy"]),
        _build_section("work_focus", "WORK / FOCUS", mapped["work_focus"]),
        _build_section("timing", "TIMING", mapped["timing"]),
        _build_section(
            "closing_guidance",
            "CLOSING GUIDANCE",
            mapped["closing_guidance"],
        ),
    ]
    sections = [
        section
        for section in sections
        if str(section.get("text", "")).strip()
    ]
    return {
        "sections": sections,
        "full_text": "\n\n".join(section["text"] for section in sections),
        "metadata": {
            "persona_id": metadata.persona_id,
            "llm_profile_id": metadata.llm_profile_id,
            "prompt_version": metadata.prompt_version,
            "theme_tags": metadata.theme_tags,
            "headline": metadata.headline,
            "model": metadata.model_id,
            "flow_type": "daily_horoscope",
        },
    }
