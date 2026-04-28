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
_REQUIRED_SECTION_IDS = {
    "today_theme",
    "today_energy",
    "best_move",
    "watch_out_for",
    "people_energy",
    "work_focus",
    "timing",
    "closing_guidance",
}
_CTA_LEAK_PATTERNS = [
    r"\bopen the full (?:daily )?reading\b",
    r"\bopen today'?s full horoscope\b",
    r"\bconsider exploring a personalized reading\b",
    r"\bfor a deeper dive\b",
]
_TIMING_WORDS = {
    "morning",
    "afternoon",
    "evening",
    "tonight",
    "today",
    "lunch",
    "late",
    "early",
    "hours",
}
_SENTENCE_RE = re.compile(r"[^.!?]+[.!?]")


def _normalize_text(text: str) -> str:
    return re.sub(r"\W+", " ", (text or "").casefold()).strip()


def _content_tokens(text: str) -> list[str]:
    return [token for token in _WORD_RE.findall((text or "").casefold()) if token not in _STOPWORDS]


def _sentence_count(text: str) -> int:
    cleaned = (text or "").strip()
    if not cleaned:
        return 0
    matches = _SENTENCE_RE.findall(cleaned)
    return len(matches) if matches else 1


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

    present_section_ids = {
        str(section.get("id", "")).strip()
        for section in sections
        if str(section.get("id", "")).strip()
    }
    missing = sorted(_REQUIRED_SECTION_IDS - present_section_ids)
    issues.extend(f"daily_missing_section:{section_id}" for section_id in missing)

    stems = [stem for stem in (_first_content_stem(section.get("text", "")) for section in sections) if stem]
    repeated_stems = [stem for stem, count in Counter(stems).items() if count >= 2]
    issues.extend(f"daily_repeated_section_stem:{stem}" for stem in repeated_stems)

    seen_bodies: dict[str, str] = {}
    for section in sections:
        section_id = str(section.get("id", ""))
        section_text = str(section.get("text", "") or "").strip()
        headline = str(section.get("headline", "") or "").strip()
        detail = str(section.get("detail", "") or "").strip()
        heading_issue = _headline_restate_issue(section_id, section_text)
        if heading_issue:
            issues.append(heading_issue)
        if headline and detail:
            normalized_headline = _normalize_text(headline)
            normalized_detail = _normalize_text(detail)
            if (
                normalized_headline == normalized_detail
                or normalized_detail.startswith(normalized_headline)
                or normalized_headline.startswith(normalized_detail)
            ):
                issues.append(f"daily_headline_detail_repetition:{section_id}")
        if section_id in _REQUIRED_SECTION_IDS and not detail:
            issues.append(f"daily_missing_section_detail:{section_id}")
        if detail and len(_content_tokens(detail)) < 24:
            issues.append(f"daily_section_too_short:{section_id}")
        if detail and section_id in _REQUIRED_SECTION_IDS and _sentence_count(detail) < 2:
            issues.append(f"daily_section_needs_more_depth:{section_id}")
        if section_id == "timing" and detail:
            timing_tokens = set(_content_tokens(detail))
            if not (_TIMING_WORDS & timing_tokens):
                issues.append("daily_timing_not_concrete")
        normalized = _normalize_text(section_text)
        if normalized:
            if normalized in seen_bodies and seen_bodies[normalized] != section_id:
                issues.append(f"daily_duplicate_section_text:{seen_bodies[normalized]}:{section_id}")
            else:
                seen_bodies[normalized] = section_id
        lowered_text = f"{headline} {detail} {section_text}".casefold()
        for pattern in _CTA_LEAK_PATTERNS:
            if re.search(pattern, lowered_text):
                issues.append(f"daily_cta_leak:{section_id}:{pattern}")

    return issues
