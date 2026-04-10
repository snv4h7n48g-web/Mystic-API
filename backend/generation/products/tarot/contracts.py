from __future__ import annotations

PRODUCT_KEY = "tarot"
PROMPT_IDS = {
    "preview": "tarot_preview",
    "reading": "tarot_reading",
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
- Guidance must be populated with non-empty, grounded next-step language and at least one concrete action.
- The opening, tarot narrative, synthesis, and guidance should each do different work rather than paraphrase one another.
- Use recognisably tarot language and do not drift into generic astrology, full-session, self-help prose, or vague mystical boilerplate detached from the cards.
"""
