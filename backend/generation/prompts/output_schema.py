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
Do not include markdown fences or any text outside the JSON object.
"""
