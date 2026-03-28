PRODUCT_KEY = 'full_reading'

PROMPT_IDS = {
    'preview': 'session_preview',
    'reading': 'session_reading',
}

EXPECTED_SECTION_IDS = [
    'opening_hook',
    'current_pattern',
    'emotional_truth',
    'practical_guidance',
    'next_return_invitation',
]

CONTRACT_INSTRUCTION = """
This is the flagship full reading. It must feel complete, emotionally coherent, and premium.
Make the guidance section fully written and genuinely useful.
Do not leave guidance as a stub, fragment, or incomplete numbered list marker.
If you use numbered guidance, each point must be complete and meaningful.
""".strip()
