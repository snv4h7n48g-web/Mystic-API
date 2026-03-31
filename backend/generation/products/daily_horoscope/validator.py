from __future__ import annotations

import re
from collections import Counter

ANNUAL_DRIFT_PATTERNS = [
    r"\bthis year\b",
    r"\byear ahead\b",
    r"\bcoming year\b",
    r"\bmonths ahead\b",
    r"\blunar new year\b",
    r"\bseason ahead\b",
    r"\byour cycle this year\b",
]

_WORD_RE = re.compile(r"[a-z0-9']+")
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from", "if", "in", "into", "is", "it", "its",
    "of", "on", "or", "so", "than", "that", "the", "their", "there", "this", "to", "today", "tonight", "up", "with", "your",
}


def _normalize_text(text: str) -> str:
    return re.sub(r"\W+", " ", (text or "").casefold()).strip()


def _content_tokens(text: str) -> list[str]:
    return [token for token in _WORD_RE.findall((text or "").casefold()) if token not in _STOPWORDS]


def _first_content_stem(text: str, size: int = 4) -> str:
    tokens = _content_tokens(text)
    return " ".join(tokens[:size])


def _headline_restate_issue(section_id: str, text: str) -> str | None:
    if not text:
        return None
    pieces = [piece.strip() for piece in re.split(r"[\n:—-]+", text, maxsplit=1) if piece.strip()]
    if len(pieces) < 2:
        return None
    head, body = pieces[0], pieces[1]
    normalized_head = _normalize_text(head)
    normalized_body = _normalize_text(body)
    if not normalized_head or not normalized_body:
        return None
    if normalized_head == normalized_body:
        return f"daily_heading_body_repetition:{section_id}"
    if normalized_body.startswith(normalized_head) or normalized_head.startswith(normalized_body):
        return f"daily_heading_body_repetition:{section_id}"
    head_tokens = set(_content_tokens(head))
    body_tokens = set(_content_tokens(body))
    if head_tokens and len(head_tokens & body_tokens) >= max(2, len(head_tokens)):
        return f"daily_heading_body_repetition:{section_id}"
    return None


def validate_daily_payload(payload: dict) -> list[str]:
    sections = payload.get("sections", [])
    text = "\n".join(section.get("text", "") for section in sections)
    lowered = text.casefold()
    issues: list[str] = []
    for pattern in ANNUAL_DRIFT_PATTERNS:
        if re.search(pattern, lowered):
            issues.append(f"daily_drift_detected:{pattern}")

    stems = [stem for stem in (_first_content_stem(section.get("text", "")) for section in sections) if stem]
    repeated_stems = [stem for stem, count in Counter(stems).items() if count >= 2]
    issues.extend(f"daily_repeated_section_stem:{stem}" for stem in repeated_stems)

    seen_bodies: dict[str, str] = {}
    for section in sections:
        section_id = str(section.get("id", ""))
        section_text = str(section.get("text", "") or "").strip()
        heading_issue = _headline_restate_issue(section_id, section_text)
        if heading_issue:
            issues.append(heading_issue)
        normalized = _normalize_text(section_text)
        if normalized:
            if normalized in seen_bodies and seen_bodies[normalized] != section_id:
                issues.append(f"daily_duplicate_section_text:{seen_bodies[normalized]}:{section_id}")
            else:
                seen_bodies[normalized] = section_id

    return issues
