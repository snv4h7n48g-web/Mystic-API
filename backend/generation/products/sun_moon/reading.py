from __future__ import annotations

from .mapper import map_sun_moon_reading


def build_sun_moon_reading_payload(*, normalized, metadata):
    mapped = map_sun_moon_reading(normalized)
    sections = [
        {'id': 'opening_invocation', 'title': 'OPENING', 'text': mapped['opening_invocation']},
        {'id': 'astrological_foundation', 'title': 'SUN AND MOON FOUNDATION', 'text': mapped['astrological_foundation']},
        {'id': 'integrated_synthesis', 'title': 'SYNTHESIS', 'text': mapped['integrated_synthesis']},
        {'id': 'reflective_guidance', 'title': 'GUIDANCE', 'text': mapped['reflective_guidance']},
        {'id': 'closing_prompt', 'title': 'CLOSING', 'text': mapped['closing_prompt']},
    ]
    sections = [section for section in sections if section['text'] and section['text'].strip()]
    return {
        'sections': sections,
        'full_text': '\n\n'.join(section['text'] for section in sections),
        'metadata': {
            'persona_id': metadata.persona_id,
            'llm_profile_id': metadata.llm_profile_id,
            'prompt_version': metadata.prompt_version,
            'theme_tags': metadata.theme_tags,
            'headline': metadata.headline,
            'model': metadata.model_id,
            'flow_type': 'sun_moon_solo',
        },
    }
