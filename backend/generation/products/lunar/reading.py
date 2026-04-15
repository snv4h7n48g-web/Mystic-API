from __future__ import annotations

from .mapper import map_lunar_reading


def build_lunar_reading_payload(*, normalized, metadata, lunar_context=None):
    mapped = map_lunar_reading(normalized, lunar_context=lunar_context or {})
    sections = [
        {'id': 'opening_invocation', 'title': 'CYCLE THEME', 'text': mapped['opening_invocation'], 'deep_text': mapped.get('opening_invocation_detail', '')},
        {'id': 'lunar_forecast', 'title': 'YEAR SYMBOLISM', 'text': mapped['lunar_forecast'], 'deep_text': mapped.get('lunar_forecast_detail', '')},
        {'id': 'integrated_synthesis', 'title': 'WELCOME AND RELEASE', 'text': mapped['integrated_synthesis'], 'deep_text': mapped.get('integrated_synthesis_detail', '')},
        {'id': 'reflective_guidance', 'title': 'HOW TO MOVE WELL THROUGH THE YEAR', 'text': mapped['reflective_guidance'], 'deep_text': mapped.get('reflective_guidance_detail', '')},
        {'id': 'closing_prompt', 'title': 'YEAR-AHEAD CLOSING', 'text': mapped['closing_prompt'], 'deep_text': mapped.get('closing_prompt_detail', '')},
    ]
    sections = [section for section in sections if section['text'] and section['text'].strip()]
    return {
        'sections': sections,
        'full_text': '\n\n'.join(section.get('deep_text') or section['text'] for section in sections),
        'metadata': {
            'persona_id': metadata.persona_id,
            'llm_profile_id': metadata.llm_profile_id,
            'prompt_version': metadata.prompt_version,
            'theme_tags': metadata.theme_tags,
            'headline': metadata.headline,
            'model': metadata.model_id,
            'flow_type': 'lunar_new_year_solo',
            'lunar_forecast': True,
            'lunar_context': lunar_context or {},
        },
    }
