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
Field rules:
- Each field must contain distinct content, not repeated or lightly reworded copies of another field.
- opening_hook = opening frame only.
- current_pattern = the core pattern/theme only.
- emotional_truth = the emotional or symbolic truth only.
- what_this_is_asking_of_you = the deeper invitation, demand, or inner adjustment this reading is pointing toward.
- your_next_move = the clearest grounded action or decision to take next.
- practical_guidance = concrete guidance only when a flow still uses a single guidance field.
- next_return_invitation = closing line only.
Do not include markdown fences or any text outside the JSON object.
"""
