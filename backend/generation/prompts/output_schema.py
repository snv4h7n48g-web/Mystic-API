_TEXT_FIELD = {"type": "string"}
_NULLABLE_TEXT_FIELD = {"type": "string"}
_DAILY_SECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "headline": _TEXT_FIELD,
        "detail": _TEXT_FIELD,
    },
    "required": ["headline", "detail"],
    "additionalProperties": False,
}

NORMALIZED_OUTPUT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "opening_hook": _TEXT_FIELD,
        "current_pattern": _TEXT_FIELD,
        "emotional_truth": _TEXT_FIELD,
        "continuity_callback": _NULLABLE_TEXT_FIELD,
        "next_return_invitation": _TEXT_FIELD,
        "premium_teaser": _NULLABLE_TEXT_FIELD,
        "theme_tags": {"type": "array", "items": _TEXT_FIELD},
        "practical_guidance": _TEXT_FIELD,
        "what_this_is_asking_of_you": _TEXT_FIELD,
        "your_next_move": _TEXT_FIELD,
        "snapshot_core_theme": _TEXT_FIELD,
        "snapshot_main_tension": _TEXT_FIELD,
        "snapshot_best_next_move": _TEXT_FIELD,
        "reading_opening": _TEXT_FIELD,
        "astrological_foundation": _TEXT_FIELD,
        "palm_revelation": _TEXT_FIELD,
        "tarot_message": _TEXT_FIELD,
        "signals_agree": _TEXT_FIELD,
        "daily_sections": {
            "type": "object",
            "properties": {
                "today_theme": _DAILY_SECTION_SCHEMA,
                "today_energy": _DAILY_SECTION_SCHEMA,
                "best_move": _DAILY_SECTION_SCHEMA,
                "watch_out_for": _DAILY_SECTION_SCHEMA,
                "people_energy": _DAILY_SECTION_SCHEMA,
                "work_focus": _DAILY_SECTION_SCHEMA,
                "timing": _DAILY_SECTION_SCHEMA,
                "closing_guidance": _DAILY_SECTION_SCHEMA,
            },
            "additionalProperties": False,
        },
        "overview": _TEXT_FIELD,
        "what_helps": _TEXT_FIELD,
        "what_blocks": _TEXT_FIELD,
        "practical_fixes": _TEXT_FIELD,
        "action_plan": _TEXT_FIELD,
        "tarot_spread_overview": _TEXT_FIELD,
        "tarot_card_chapters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "card": _TEXT_FIELD,
                    "position": _TEXT_FIELD,
                    "orientation": _TEXT_FIELD,
                    "card_meaning": _TEXT_FIELD,
                    "position_meaning": _TEXT_FIELD,
                    "reversal_message": _TEXT_FIELD,
                    "question_relevance": _TEXT_FIELD,
                    "personal_implication": _TEXT_FIELD,
                },
                "required": [
                    "card",
                    "position",
                    "orientation",
                    "card_meaning",
                    "position_meaning",
                    "reversal_message",
                    "question_relevance",
                    "personal_implication",
                ],
                "additionalProperties": False,
            },
        },
        "tarot_spread_story": _TEXT_FIELD,
    },
    "required": [
        "opening_hook",
        "current_pattern",
        "emotional_truth",
        "continuity_callback",
        "next_return_invitation",
        "premium_teaser",
        "theme_tags",
        "practical_guidance",
    ],
    "additionalProperties": False,
}


NORMALIZED_OUTPUT_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "opening_hook": _TEXT_FIELD,
        "current_pattern": _TEXT_FIELD,
        "emotional_truth": _TEXT_FIELD,
        "continuity_callback": _TEXT_FIELD,
        "next_return_invitation": _TEXT_FIELD,
        "premium_teaser": _TEXT_FIELD,
        "theme_tags": {"type": "array", "items": _TEXT_FIELD},
        "practical_guidance": _TEXT_FIELD,
        "what_this_is_asking_of_you": _TEXT_FIELD,
        "your_next_move": _TEXT_FIELD,
        "snapshot_core_theme": _TEXT_FIELD,
        "snapshot_main_tension": _TEXT_FIELD,
        "snapshot_best_next_move": _TEXT_FIELD,
        "reading_opening": _TEXT_FIELD,
        "astrological_foundation": _TEXT_FIELD,
        "palm_revelation": _TEXT_FIELD,
        "tarot_message": _TEXT_FIELD,
        "signals_agree": _TEXT_FIELD,
        "daily_sections": {"type": "object"},
        "overview": _TEXT_FIELD,
        "what_helps": _TEXT_FIELD,
        "what_blocks": _TEXT_FIELD,
        "practical_fixes": _TEXT_FIELD,
        "action_plan": _TEXT_FIELD,
        "tarot_spread_overview": _TEXT_FIELD,
        "tarot_card_chapters": {"type": "array", "items": {"type": "object"}},
        "tarot_spread_story": _TEXT_FIELD,
    },
    "required": [
        "opening_hook",
        "current_pattern",
        "emotional_truth",
        "continuity_callback",
        "next_return_invitation",
        "premium_teaser",
        "theme_tags",
        "practical_guidance",
    ],
}


_BASE_PROPERTIES = {
    "opening_hook": _TEXT_FIELD,
    "current_pattern": _TEXT_FIELD,
    "emotional_truth": _TEXT_FIELD,
    "continuity_callback": _TEXT_FIELD,
    "next_return_invitation": _TEXT_FIELD,
    "premium_teaser": _TEXT_FIELD,
    "theme_tags": {"type": "array", "items": _TEXT_FIELD},
    "practical_guidance": _TEXT_FIELD,
}
_BASE_REQUIRED = [
    "opening_hook",
    "current_pattern",
    "emotional_truth",
    "continuity_callback",
    "next_return_invitation",
    "premium_teaser",
    "theme_tags",
    "practical_guidance",
]
_PREVIEW_PROPERTIES = {
    "opening_hook": {"type": "string", "maxLength": 220},
    "current_pattern": {"type": "string", "maxLength": 420},
    "emotional_truth": {"type": "string", "maxLength": 420},
    "continuity_callback": {"type": "string", "maxLength": 180},
    "next_return_invitation": {"type": "string", "maxLength": 180},
    "premium_teaser": {"type": "string", "maxLength": 220},
    "theme_tags": {"type": "array", "items": {"type": "string", "maxLength": 40}},
    "practical_guidance": {"type": "string", "maxLength": 420},
}
_FULL_READING_PROPERTIES = {
    "snapshot_core_theme": _TEXT_FIELD,
    "snapshot_main_tension": _TEXT_FIELD,
    "snapshot_best_next_move": _TEXT_FIELD,
    "reading_opening": _TEXT_FIELD,
    "astrological_foundation": _TEXT_FIELD,
    "palm_revelation": _TEXT_FIELD,
    "tarot_message": _TEXT_FIELD,
    "signals_agree": _TEXT_FIELD,
    "what_this_is_asking_of_you": _TEXT_FIELD,
    "your_next_move": _TEXT_FIELD,
}
_DAILY_SECTIONS_SCHEMA = {
    "type": "object",
    "properties": NORMALIZED_OUTPUT_JSON_SCHEMA["properties"]["daily_sections"]["properties"],
    "required": list(NORMALIZED_OUTPUT_JSON_SCHEMA["properties"]["daily_sections"]["properties"].keys()),
    "additionalProperties": False,
}
_TAROT_PROPERTIES = {
    "tarot_spread_overview": _TEXT_FIELD,
    "tarot_card_chapters": NORMALIZED_OUTPUT_JSON_SCHEMA["properties"]["tarot_card_chapters"],
    "tarot_spread_story": _TEXT_FIELD,
}
_FENG_SHUI_PROPERTIES = {
    "overview": _TEXT_FIELD,
    "what_helps": _TEXT_FIELD,
    "what_blocks": _TEXT_FIELD,
    "practical_fixes": _TEXT_FIELD,
    "action_plan": _TEXT_FIELD,
}


def output_schema_for_flow(flow_id: str) -> dict:
    if flow_id == "session_preview" or flow_id.endswith("_preview"):
        return {
            "type": "object",
            "properties": dict(_PREVIEW_PROPERTIES),
            "required": list(_BASE_REQUIRED),
            "additionalProperties": False,
        }

    properties = dict(_BASE_PROPERTIES)
    required = list(_BASE_REQUIRED)
    if flow_id == "session_reading":
        properties.update(_FULL_READING_PROPERTIES)
        required.extend(_FULL_READING_PROPERTIES)
    elif flow_id == "daily_horoscope_reading":
        properties["daily_sections"] = _DAILY_SECTIONS_SCHEMA
        required.append("daily_sections")
    elif flow_id == "tarot_reading":
        properties.update(_TAROT_PROPERTIES)
        required.extend(_TAROT_PROPERTIES)
    elif flow_id == "feng_shui_analysis":
        properties.update(_FENG_SHUI_PROPERTIES)
        required.extend(_FENG_SHUI_PROPERTIES)
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


PREVIEW_OUTPUT_SCHEMA_INSTRUCTION = """Return compact JSON with exactly these keys:
{
  \"opening_hook\": string,
  \"current_pattern\": string,
  \"emotional_truth\": string,
  \"continuity_callback\": string,
  \"next_return_invitation\": string,
  \"premium_teaser\": string,
  \"theme_tags\": string[],
  \"practical_guidance\": string
}
Preview length rules:
- Keep each prose field short enough for a paid-preview card.
- opening_hook, next_return_invitation, and premium_teaser should each be one concise sentence.
- current_pattern, emotional_truth, and practical_guidance should each be one or two compact sentences.
- theme_tags should contain 3-6 short labels.
- Do not include full-reading sections, chapter text, markdown fences, or any prose outside the JSON object.
"""


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
When the API provides a structured output tool, put these fields directly in that tool input and do not write separate prose.
When no structured output tool is provided, do not include markdown fences or any text outside the JSON object.
"""


def output_instruction_for_flow(flow_id: str) -> str:
    if flow_id == "session_preview" or flow_id.endswith("_preview"):
        return PREVIEW_OUTPUT_SCHEMA_INSTRUCTION
    return OUTPUT_SCHEMA_INSTRUCTION
