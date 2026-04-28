OUTPUT_SCHEMA_INSTRUCTION = """Return JSON with exactly these base keys:
{
  \"opening_hook\": string,
  \"current_pattern\": string,
  \"emotional_truth\": string,
  \"continuity_callback\": string|null,
  \"next_return_invitation\": string,
  \"premium_teaser\": string|null,
  \"theme_tags\": string[]
}
Guidance payload rules:
- For full/core session readings, include both additional keys:\n  \"what_this_is_asking_of_you\": string\n  \"your_next_move\": string
- For other flows, you may return:\n  \"practical_guidance\": string
- You may include practical_guidance as a compatibility fallback, but full/core readings should prioritise the two explicit payoff keys.
- For full/core session readings, also include these layered premium keys:\n  \"snapshot_core_theme\": string\n  \"snapshot_main_tension\": string\n  \"snapshot_best_next_move\": string\n  \"reading_opening\": string\n  \"astrological_foundation\": string\n  \"palm_revelation\": string\n  \"tarot_message\": string\n  \"signals_agree\": string
- For full daily horoscope readings, also include:\n  \"daily_sections\": {\n    \"today_theme\": {\"headline\": string, \"detail\": string},\n    \"today_energy\": {\"headline\": string, \"detail\": string},\n    \"best_move\": {\"headline\": string, \"detail\": string},\n    \"watch_out_for\": {\"headline\": string, \"detail\": string},\n    \"people_energy\": {\"headline\": string, \"detail\": string},\n    \"work_focus\": {\"headline\": string, \"detail\": string},\n    \"timing\": {\"headline\": string, \"detail\": string},\n    \"closing_guidance\": {\"headline\": string, \"detail\": string}\n  }
- For full Feng Shui analyses, also include:\n  \"overview\": string\n  \"what_helps\": string\n  \"what_blocks\": string\n  \"practical_fixes\": string\n  \"action_plan\": string
- For full tarot readings, also include:\n  \"tarot_spread_overview\": string\n  \"tarot_card_chapters\": [\n    {\"card\": string, \"position\": string, \"orientation\": string, \"card_meaning\": string, \"position_meaning\": string, \"reversal_message\": string, \"question_relevance\": string, \"personal_implication\": string}\n  ]\n  \"tarot_spread_story\": string
Field rules:
- Each field must contain distinct content, not repeated or lightly reworded copies of another field.
- opening_hook = opening frame only.
- current_pattern = the core pattern/theme only.
- emotional_truth = the emotional or symbolic truth only.
- snapshot_core_theme = one line that names the central pattern without repeating body copy.
- snapshot_main_tension = one line that names the central friction without repeating body copy.
- snapshot_best_next_move = one line that names the clearest move without repeating the full next-move section.
- reading_opening = the opening paragraph for the layered body.
- astrological_foundation = interpret the actual astrology factors present and explain how they shape the pattern, identity, or tension in this reading. In combined/full readings, astrology must feel materially present rather than invisible setup.
- palm_revelation = what palm features/signals stood out, what they suggest, and how they apply to the question. If the palm contribution is subtle, say so honestly.
- tarot_message = name the actual cards when available, explain what each contributes, how they interact as a spread, and how that speaks to the question. For full/core readings with tarot, this should usually be a substantial multi-paragraph block rather than a one-paragraph summary.
- signals_agree = where the palm, tarot, and broader reading align or productively differ.
- daily_sections = for full daily horoscope readings only. Each daily section must have a short headline and a fuller detail block that adds fresh material instead of restating the headline. Detail blocks should usually be 2-4 concrete sentences, roughly 35-70 words, with at least one usable cue, action, timing note, or relationship/work implication. Keep the timing immediate and concrete. People energy, work/focus, and timing should all be materially filled, not omitted or marked unavailable.
- Feng Shui fields = for full Feng Shui analyses only. overview diagnoses the space, what_helps names existing support to protect, what_blocks names room friction, practical_fixes gives concrete room changes with reasons, and action_plan orders the first moves. These fields must not paraphrase one another.
- tarot_spread_overview = for full tarot readings only. It introduces the exact drawn spread, positions, and central tension without doing every card explanation.
- tarot_card_chapters = for full tarot readings only. Include one object per drawn card, in draw order. Each object must explain: the card's core meaning, what its spread position changes, what reversed orientation means when reversed or what upright orientation strengthens when upright, why it matters to the user's question, and the personal implication.
- tarot_spread_story = for full tarot readings only. It synthesises how the cards move together as one story. Do not recap each card chapter sentence by sentence.
- what_this_is_asking_of_you = the deeper invitation, demand, or inner adjustment this reading is pointing toward.
- your_next_move = the clearest grounded action or decision to take next.
- practical_guidance = concrete guidance only when a flow still uses a single guidance field.
- next_return_invitation = closing line only.
Do not include markdown fences or any text outside the JSON object.
"""
