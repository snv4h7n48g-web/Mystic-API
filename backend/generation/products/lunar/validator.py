from __future__ import annotations


def _normalized_section_texts(payload: dict) -> list[str]:
    texts: list[str] = []
    for section in payload.get("sections", []):
        text = " ".join((section.get("text") or "").split()).strip()
        if text:
            texts.append(text.casefold())
    return texts


def validate_lunar_payload(payload: dict) -> list[str]:
    text = "\n".join(section.get("text", "") for section in payload.get("sections", [])).casefold()
    issues: list[str] = []
    for phrase in ["today's theme", "today only", "today", "tomorrow", "this morning", "tonight"]:
        if phrase in text:
            issues.append(f"lunar_daily_drift:{phrase}")
    for phrase in ["horoscope", "star sign", "zodiac forecast"]:
        if phrase in text:
            issues.append(f"lunar_generic_horoscope_drift:{phrase}")
    section_texts = _normalized_section_texts(payload)
    if len(section_texts) != len(set(section_texts)):
        issues.append("lunar_duplicate_section_content")
    return issues
