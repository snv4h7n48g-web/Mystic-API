from __future__ import annotations

import re
from typing import Any

from .schema import DAILY_HOROSCOPE_PREVIEW_FIELDS, DAILY_HOROSCOPE_READING_FIELDS

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _clean(text: str | None) -> str:
    return " ".join((text or "").split()).strip()


def _normalize(text: str) -> str:
    return re.sub(r"\W+", " ", text.casefold()).strip()


def _dedupe_sentences(text: str) -> str:
    cleaned = _clean(text)
    if not cleaned:
        return ""
    seen: set[str] = set()
    kept: list[str] = []
    for sentence in _SENTENCE_SPLIT_RE.split(cleaned):
        part = sentence.strip()
        if not part:
            continue
        marker = _normalize(part)
        if not marker or marker in seen:
            continue
        seen.add(marker)
        kept.append(part)
    return " ".join(kept).strip()


def _first_sentence(text: str) -> str:
    cleaned = _clean(text)
    if not cleaned:
        return ""
    parts = _SENTENCE_SPLIT_RE.split(cleaned, maxsplit=1)
    return parts[0].strip() if parts else cleaned


def _remaining_sentences(text: str) -> str:
    cleaned = _clean(text)
    if not cleaned:
        return ""
    parts = _SENTENCE_SPLIT_RE.split(cleaned, maxsplit=1)
    if len(parts) < 2:
        return ""
    return parts[1].strip()


def _split_first_clause(text: str) -> tuple[str, str]:
    cleaned = _clean(text)
    if not cleaned:
        return "", ""
    parts = re.split(r"(?<=[,;:])\s+", cleaned, maxsplit=1)
    if len(parts) < 2:
        return cleaned, ""
    return parts[0].strip(), parts[1].strip()


def _headline_and_detail(
    text: str,
    *,
    fallback_headline: str,
    fallback_detail: str = "",
) -> tuple[str, str]:
    cleaned = _dedupe_sentences(text)
    if not cleaned:
        return _clean(fallback_headline), _clean(fallback_detail)

    headline = _first_sentence(cleaned)
    detail = _remaining_sentences(cleaned)

    if not detail or _normalize(detail) == _normalize(headline):
        clause_headline, clause_detail = _split_first_clause(cleaned)
        if clause_detail:
            headline = clause_headline or headline
            detail = clause_detail

    if not detail or _normalize(detail) == _normalize(headline):
        detail = _clean(fallback_detail)

    if not headline:
        headline = _clean(fallback_headline)
    if not detail:
        detail = cleaned
    if _normalize(detail) == _normalize(headline):
        detail = ""
    return headline, detail


def _daily_block(
    normalized: Any,
    *,
    section_id: str,
    fallback_text: str = "",
    fallback_headline: str = "",
    fallback_detail: str = "",
) -> dict[str, str]:
    daily_sections = getattr(normalized, "daily_sections", {}) or {}
    raw_block = daily_sections.get(section_id, {})
    if not isinstance(raw_block, dict):
        raw_block = {}

    explicit_headline = _clean(raw_block.get("headline"))
    explicit_detail = _clean(raw_block.get("detail"))
    cleaned_fallback_text = _clean(fallback_text)
    if not explicit_headline and not explicit_detail and not cleaned_fallback_text:
        return {"headline": "", "detail": "", "text": ""}
    if explicit_headline and explicit_detail and _normalize(explicit_headline) != _normalize(explicit_detail):
        text = explicit_detail or explicit_headline
        return {
            "headline": explicit_headline,
            "detail": explicit_detail,
            "text": text,
        }

    combined = " ".join(
        part
        for part in [
            explicit_headline,
            explicit_detail,
            cleaned_fallback_text,
        ]
        if part
    ).strip()

    headline, detail = _headline_and_detail(
        combined,
        fallback_headline=fallback_headline,
        fallback_detail=fallback_detail,
    )
    text = detail or headline
    if not text:
        return {"headline": "", "detail": "", "text": ""}
    return {
        "headline": headline,
        "detail": detail,
        "text": text,
    }


def map_daily_preview(normalized) -> dict:
    headline = _clean(getattr(normalized, "opening_hook", ""))
    energy = _clean(getattr(normalized, "current_pattern", ""))
    best_move = _clean(
        getattr(normalized, "your_next_move", "")
        or getattr(normalized, "practical_guidance", "")
    )
    watch_out = _clean(getattr(normalized, "emotional_truth", ""))
    deeper = _clean(
        getattr(normalized, "premium_teaser", "")
        or getattr(normalized, "next_return_invitation", "")
    )
    return {
        "headline": headline,
        "today_energy": energy,
        "best_move_teaser": best_move,
        "watch_out_teaser": watch_out,
        "deeper_layer_teaser": deeper,
        "schema_fields": DAILY_HOROSCOPE_PREVIEW_FIELDS,
    }


def map_daily_reading(normalized) -> dict:
    today_theme = _daily_block(
        normalized,
        section_id="today_theme",
        fallback_text=_clean(
            getattr(normalized, "reading_opening", "")
            or getattr(normalized, "opening_hook", "")
        ),
        fallback_headline=_clean(getattr(normalized, "opening_hook", "")),
    )
    today_energy = _daily_block(
        normalized,
        section_id="today_energy",
        fallback_text=_clean(
            getattr(normalized, "astrological_foundation", "")
            or getattr(normalized, "current_pattern", "")
        ),
        fallback_headline=_clean(getattr(normalized, "current_pattern", "")),
    )
    best_move = _daily_block(
        normalized,
        section_id="best_move",
        fallback_text=_clean(
            getattr(normalized, "your_next_move", "")
            or getattr(normalized, "practical_guidance", "")
        ),
        fallback_headline=_clean(
            getattr(normalized, "your_next_move", "")
            or getattr(normalized, "practical_guidance", "")
        ),
    )
    watch_out = _daily_block(
        normalized,
        section_id="watch_out_for",
        fallback_text=_clean(
            getattr(normalized, "what_this_is_asking_of_you", "")
            or getattr(normalized, "emotional_truth", "")
        ),
        fallback_headline=_clean(getattr(normalized, "emotional_truth", "")),
    )
    people_energy = _daily_block(
        normalized,
        section_id="people_energy",
        fallback_headline="People energy needs a clearer read today.",
    )
    work_focus = _daily_block(
        normalized,
        section_id="work_focus",
        fallback_headline="Work and focus need a clearer read today.",
    )
    timing = _daily_block(
        normalized,
        section_id="timing",
        fallback_headline="Timing needs a clearer read today.",
    )
    closing_guidance = _daily_block(
        normalized,
        section_id="closing_guidance",
        fallback_text=_clean(
            getattr(normalized, "next_return_invitation", "")
            or getattr(normalized, "premium_teaser", "")
        ),
        fallback_headline=_clean(getattr(normalized, "next_return_invitation", "")),
    )

    return {
        "today_theme": today_theme,
        "today_energy": today_energy,
        "best_move": best_move,
        "watch_out_for": watch_out,
        "people_energy": people_energy,
        "work_focus": work_focus,
        "timing": timing,
        "closing_guidance": closing_guidance,
        "schema_fields": DAILY_HOROSCOPE_READING_FIELDS,
    }
