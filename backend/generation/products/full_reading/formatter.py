from __future__ import annotations

import re
from datetime import datetime, timezone

from ...types import GenerationMetadata, NormalizedMysticOutput


_SENTENCE_SPLIT_PATTERN = re.compile(r'(?<=[.!?])\s+')
_NUMBERED_SPLIT_PATTERN = re.compile(r'\n\s*(?:2[.)-]|2:)\s*', re.IGNORECASE)
_LABEL_ASKING_PATTERN = re.compile(
    r'(?:^|\n)\s*(?:1[.)-]?\s*)?(?:what this is asking of you|what this asks of you|what it is asking of you)\s*:?\s*',
    re.IGNORECASE,
)
_INLINE_ASKING_PATTERN = re.compile(
    r'^\s*(?:1[.)-]?\s*)?(?:what this is asking of you|what this asks of you|what it is asking of you)\s*:?\s*',
    re.IGNORECASE,
)
_LABEL_NEXT_MOVE_PATTERN = re.compile(
    r'(?:^|\n|\s)(?:2[.)-]?\s*)?(?:your next move|next move)\s*:?\s*',
    re.IGNORECASE,
)


def _clean(text: str | None) -> str:
    return (text or '').strip()


def _split_legacy_guidance(guidance: str) -> tuple[str, str]:
    cleaned = _clean(guidance)
    if not cleaned:
        return '', ''

    asking_match = _LABEL_ASKING_PATTERN.search(cleaned)
    next_move_match = _LABEL_NEXT_MOVE_PATTERN.search(cleaned)
    if next_move_match:
        asking_source = cleaned[:next_move_match.start()].strip()
        asking = _INLINE_ASKING_PATTERN.sub('', asking_source).strip(' \n:-')
        next_move = cleaned[next_move_match.end():].strip(' \n:-')
        if asking and next_move:
            return asking, next_move

    if asking_match and next_move_match and next_move_match.start() > asking_match.end():
        asking = cleaned[asking_match.end():next_move_match.start()].strip(' \n:-')
        next_move = cleaned[next_move_match.end():].strip(' \n:-')
        if asking and next_move:
            return asking, next_move

    numbered_parts = _NUMBERED_SPLIT_PATTERN.split(cleaned, maxsplit=1)
    if len(numbered_parts) == 2:
        first = re.sub(r'^\s*(?:1[.)-]|1:)\s*', '', numbered_parts[0]).strip()
        second = numbered_parts[1].strip()
        if first and second:
            return first, second

    sentences = [segment.strip() for segment in _SENTENCE_SPLIT_PATTERN.split(cleaned) if segment.strip()]
    if len(sentences) >= 3:
        pivot = max(1, len(sentences) // 2)
        return ' '.join(sentences[:pivot]).strip(), ' '.join(sentences[pivot:]).strip()
    if len(sentences) == 2:
        return sentences[0], sentences[1]

    return cleaned, ''


def build_full_reading_payload(*, normalized: NormalizedMysticOutput, metadata: GenerationMetadata) -> dict:
    asking = _clean(normalized.what_this_is_asking_of_you)
    next_move = _clean(normalized.your_next_move)

    if not asking or not next_move:
        legacy_asking, legacy_next_move = _split_legacy_guidance(normalized.practical_guidance)
        asking = asking or legacy_asking
        next_move = next_move or legacy_next_move

    sections = [
        {"id": "opening_hook", "title": "OPENING", "text": normalized.opening_hook},
        {"id": "current_pattern", "title": "CURRENT PATTERN", "text": normalized.current_pattern},
        {"id": "emotional_truth", "title": "EMOTIONAL TRUTH", "text": normalized.emotional_truth},
        {
            "id": "what_this_is_asking_of_you",
            "title": "WHAT THIS IS ASKING OF YOU",
            "text": asking,
        },
        {
            "id": "your_next_move",
            "title": "YOUR NEXT MOVE",
            "text": next_move,
        },
        {
            "id": "next_return_invitation",
            "title": "NEXT RETURN",
            "text": normalized.next_return_invitation,
        },
    ]

    full_text = "\n\n".join(section["text"] for section in sections if section["text"])

    return {
        "sections": sections,
        "full_text": full_text,
        "metadata": {
            "persona_id": metadata.persona_id,
            "llm_profile_id": metadata.llm_profile_id,
            "prompt_version": metadata.prompt_version,
            "theme_tags": metadata.theme_tags,
            "headline": metadata.headline,
            "model": metadata.model_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "payoff_contract": {
                "what_this_is_asking_of_you": asking,
                "your_next_move": next_move,
                "practical_guidance_legacy": _clean(normalized.practical_guidance),
            },
        },
    }
