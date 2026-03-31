PRODUCT_KEY = 'full_reading'

PROMPT_IDS = {
    'preview': 'session_preview',
    'reading': 'session_reading',
}

EXPECTED_SECTION_IDS = [
    'snapshot_core_theme',
    'snapshot_main_tension',
    'snapshot_best_next_move',
    'reading_opening',
    'palm_revelation',
    'tarot_message',
    'signals_agree',
    'what_this_is_asking_of_you',
    'your_next_move',
    'next_return_invitation',
]

CONTRACT_INSTRUCTION = """
This is the flagship full reading. It must feel complete, emotionally coherent, layered, and premium.
Do not write it as a stack of repeated headlines with lightly reworded paragraphs underneath.
For full/core readings, the structure must land as:
1. snapshot_core_theme
2. snapshot_main_tension
3. snapshot_best_next_move
4. reading_opening
5. palm_revelation
6. tarot_message
7. signals_agree
8. what_this_is_asking_of_you
9. your_next_move
10. next_return_invitation
Rules:
- The three snapshot lines must be short, high-signal, and not duplicates of the body sections.
- If palm is part of the flow, palm_revelation must clearly state what palm features/signals stood out, what they suggest, and how they relate to the user's question. If the palm contribution is subtle, say so honestly.
- tarot_message must name the actual cards or spread positions when available, explain what each card contributes, how they interact, and how the spread speaks to the question.
- signals_agree must synthesise across modalities instead of repeating palm_revelation or tarot_message.
- Deliver two distinct payoff sections:
  1. what_this_is_asking_of_you
  2. your_next_move
- Both payoff sections must be fully written, specific, emotionally coherent, and not duplicates of one another.
- Do not leave any required section as a stub, fragment, vague one-liner, or decorative paraphrase.
If you include numbered points, each point must be complete prose.
""".strip()
