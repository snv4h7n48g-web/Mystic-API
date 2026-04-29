from __future__ import annotations

PRODUCT_KEY = "palm"
PROMPT_IDS = {
    "preview": "palm_preview",
    "reading": "palm_reading",
}
EXPECTED_SECTION_IDS = [
    "opening_invocation",
    "palm_insight",
    "integrated_synthesis",
    "reflective_guidance",
    "closing_prompt",
]
CONTRACT_INSTRUCTION = """PALM CONTRACT:
- This is a palm reading and must be led by palm features, lines, mounts, hand shape, texture, or marks when available.
- Avoid generic tarot, horoscope, or vague spiritual prose detached from the observed palm details.
- The reading body should interpret palm symbolism into meaning, then guidance.
- Guidance should connect back to the palm features rather than drifting into unrelated mystic language.
"""
