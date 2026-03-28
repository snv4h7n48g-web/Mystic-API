from __future__ import annotations

import re

_STUB_PATTERN = re.compile(r'^\s*(?:\d+[.):-]?|[-*])\s*$')


def validate_full_reading_payload(payload: dict) -> list[str]:
    sections = payload.get('sections', [])
    issues: list[str] = []
    guidance = next((section.get('text', '') for section in sections if section.get('id') in {'practical_guidance', 'reflective_guidance'}), '')
    cleaned = guidance.strip()
    if not cleaned:
        issues.append('full_reading_missing_guidance')
    elif _STUB_PATTERN.match(cleaned) or len(cleaned) < 16:
        issues.append('full_reading_stub_guidance')
    return issues
