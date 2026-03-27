from __future__ import annotations

PRODUCT_KEY = "tarot"
PROMPT_IDS = {
    "preview": "session_preview",
    "reading": "session_reading",
}
EXPECTED_SECTION_IDS = [
    "opening_invocation",
    "tarot_narrative",
    "integrated_synthesis",
    "reflective_guidance",
    "closing_prompt",
]
CONTRACT_INSTRUCTION = """TAROT CONTRACT:
- This is a tarot reading and must sound recognisably card-led.
- Name card symbolism, card positions, or spread dynamics when available.
- The reading should feel interpreted, not generic: symbol -> meaning -> synthesis -> guidance.
- The tarot narrative section should clearly carry the card-specific interpretation burden.
- Use recognisably tarot language and do not drift into generic astrology, full-session, or self-help prose.
"""
