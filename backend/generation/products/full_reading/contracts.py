PRODUCT_KEY = 'full_reading'

PROMPT_IDS = {
    'preview': 'session_preview',
    'reading': 'session_reading',
}

EXPECTED_SECTION_IDS = [
    'opening_hook',
    'current_pattern',
    'emotional_truth',
    'what_this_is_asking_of_you',
    'your_next_move',
    'next_return_invitation',
]

CONTRACT_INSTRUCTION = """
This is the flagship full reading. It must feel complete, emotionally coherent, and premium.
For the payoff, do not collapse everything into one generic guidance paragraph.
Deliver two distinct payoff sections:
1. what_this_is_asking_of_you
2. your_next_move
Both sections must be fully written, specific, and emotionally coherent.
Do not leave either section as a stub, fragment, vague one-liner, duplicated phrasing, or an incomplete numbered list marker.
If you include numbered points, each point must be complete prose.
""".strip()
