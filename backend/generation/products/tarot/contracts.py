from __future__ import annotations

PRODUCT_KEY = "tarot"
PROMPT_IDS = {
    "preview": "tarot_preview",
    "reading": "tarot_reading",
}
EXPECTED_SECTION_IDS = [
    "spread_overview",
    "card_1",
    "card_2",
    "card_3",
    "spread_story",
    "reflective_guidance",
]
CONTRACT_INSTRUCTION = """TAROT CONTRACT:
- This is a tarot reading and must sound recognisably card-led.
- Name card symbolism, card positions, or spread dynamics when available.
- The reading should feel interpreted, not generic: symbol -> meaning -> synthesis -> guidance.
- For full tarot readings, return tarot_spread_overview, tarot_card_chapters, and tarot_spread_story.
- tarot_card_chapters must include one object per drawn card in draw order. Each chapter must explain card meaning, position meaning, reversal/upright orientation, question relevance, and personal implication.
- tarot_spread_story must tell the story the whole spread creates together. It must not simply recap each card chapter.
- Guidance must be populated with non-empty, grounded next-step language and at least one concrete action.
- The spread overview, card chapters, spread story, and guidance should each do different work rather than paraphrase one another.
- Use recognisably tarot language and do not drift into generic astrology, full-session, self-help prose, or vague mystical boilerplate detached from the cards.
"""
