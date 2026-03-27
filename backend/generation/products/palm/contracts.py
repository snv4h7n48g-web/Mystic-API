from __future__ import annotations

PRODUCT_KEY = "palm"
PROMPT_IDS = {
    "preview": "palm_preview",
    "reading": "palm_reading",
}
EXPECTED_SECTION_IDS = [
    "opening_hook",
    "current_pattern",
    "emotional_truth",
    "practical_guidance",
    "next_return_invitation",
]
CONTRACT_INSTRUCTION = """PALM CONTRACT:
- This is a palm reading and must be led by palm features, lines, mounts, hand shape, texture, or marks when available.
- Avoid generic tarot, horoscope, or vague spiritual prose detached from the observed palm details.
- The reading body should interpret palm symbolism into meaning, then guidance.
- Guidance should connect back to the palm features rather than drifting into unrelated mystic language.
"""
