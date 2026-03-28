from __future__ import annotations

import re

_STUB_PATTERN = re.compile(r'^\s*(?:\d+[.):-]?|[-*])\s*$')
_DANGLING_LIST_PATTERN = re.compile(r'(?:steps?|guidance|next steps?)\s*:\s*1\.?\s*$', re.IGNORECASE)


def validate_full_reading_payload(payload: dict) -> list[str]:
    sections = payload.get('sections', [])
    issues: list[str] = []
    guidance = next((section.get('text', '') for section in sections if section.get('id') in {'practical_guidance', 'reflective_guidance'}), '')
    cleaned = guidance.strip()
    if not cleaned:
        issues.append('full_reading_missing_guidance')
    elif (
        _STUB_PATTERN.match(cleaned)
        or _DANGLING_LIST_PATTERN.search(cleaned)
        or len(cleaned) < 40
    ):
        issues.append('full_reading_stub_guidance')
    return issues
