OUTPUT_SCHEMA_INSTRUCTION = """Return JSON with exactly these keys:
{
  \"opening_hook\": string,
  \"current_pattern\": string,
  \"emotional_truth\": string,
  \"practical_guidance\": string,
  \"continuity_callback\": string|null,
  \"next_return_invitation\": string,
  \"premium_teaser\": string|null,
  \"theme_tags\": string[]
}
Field rules:
- Each field must contain distinct content, not repeated or lightly reworded copies of another field.
- opening_hook = opening frame only.
- current_pattern = the core pattern/theme only.
- emotional_truth = the emotional or symbolic truth only.
- practical_guidance = concrete guidance only; when a flow asks for multiple actions, include all of them in this field as a short numbered or clearly separated list.
- next_return_invitation = closing line only.
Do not include markdown fences or any text outside the JSON object.
"""
