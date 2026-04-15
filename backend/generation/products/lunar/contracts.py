from __future__ import annotations

PRODUCT_KEY = "lunar"
PROMPT_IDS = {
    "preview": "lunar_new_year_preview",
    "reading": "lunar_new_year_reading",
}
EXPECTED_SECTION_IDS = [
    "opening_invocation",
    "lunar_forecast",
    "integrated_synthesis",
    "reflective_guidance",
    "closing_prompt",
]
CONTRACT_INSTRUCTION = """LUNAR NEW YEAR CONTRACT:
- This is a Lunar New Year year-ahead reading, not a daily horoscope.
- Frame the reading as the cycle the user is entering for the year ahead.
- If lunar_context is present, the user's birth zodiac and the current year animal/element must visibly shape the reading.
- Cover cycle theme, year symbolism, opportunity/luck areas, friction/caution areas, what to welcome, what to release, and how to move through the year well.
- Avoid today's-theme phrasing, generic horoscope filler, or same-paragraph repetition across sections.
"""
