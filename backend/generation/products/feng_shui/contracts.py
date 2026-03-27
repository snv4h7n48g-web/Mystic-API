from __future__ import annotations

PRODUCT_KEY = "feng_shui"
PROMPT_IDS = {
    "preview": "feng_shui_preview",
    "reading": "feng_shui_analysis",
}
EXPECTED_SECTION_IDS = [
    "opening_hook",
    "current_pattern",
    "emotional_truth",
    "practical_guidance",
    "next_return_invitation",
]
CONTRACT_INSTRUCTION = """FENG SHUI CONTRACT:
- This is a Feng Shui analysis of a space, room, or placement situation.
- Ground the reading in rooms, layout, placement, flow, clutter, direction, or environmental features.
- Guidance must include practical recommendations or next actions, not generic spiritual reassurance.
- Keep the tone as environmental analysis rather than a personal tarot or astrology reading.
"""
