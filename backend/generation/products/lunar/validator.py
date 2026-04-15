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
    sections = payload.get("sections", [])
    if len(sections) < 4:
        issues.append("lunar_missing_sections")
    for phrase in ["today's theme", "today only", "today", "tomorrow", "this morning", "tonight"]:
        if phrase in text:
            issues.append(f"lunar_daily_drift:{phrase}")
    for phrase in ["horoscope", "star sign", "zodiac forecast"]:
        if phrase in text:
            issues.append(f"lunar_generic_horoscope_drift:{phrase}")
    section_texts = _normalized_section_texts(payload)
    if len(section_texts) != len(set(section_texts)):
        issues.append("lunar_duplicate_section_content")
    for required_id in ["opening_invocation", "lunar_forecast", "integrated_synthesis", "reflective_guidance"]:
        if not any((section.get("id") == required_id and (section.get("text") or "").strip()) for section in sections):
            issues.append(f"lunar_missing_required_section:{required_id}")
    for section in sections:
        text = " ".join((section.get("text") or "").split()).strip()
        if section.get("id") in {"lunar_forecast", "reflective_guidance"} and len(text) < 80:
            issues.append(f"lunar_section_too_thin:{section.get('id')}")
    return issues
