from __future__ import annotations

import re
from typing import Any

from .schema import DAILY_HOROSCOPE_PREVIEW_FIELDS, DAILY_HOROSCOPE_READING_FIELDS

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_WORD_RE = re.compile(r"[a-z0-9']+")

_SIGN_TRAITS: dict[str, dict[str, str]] = {
    "aries": {
        "gift": "initiative",
        "pace": "fast movement",
        "shadow": "rushing past nuance",
    },
    "taurus": {
        "gift": "steadiness",
        "pace": "deliberate follow-through",
        "shadow": "digging in too early",
    },
    "gemini": {
        "gift": "quick thinking",
        "pace": "variety and exchange",
        "shadow": "scattered attention",
    },
    "cancer": {
        "gift": "emotional sensitivity",
        "pace": "protective pacing",
        "shadow": "withdrawing when exposed",
    },
    "leo": {
        "gift": "visible confidence",
        "pace": "expressive momentum",
        "shadow": "performing instead of listening",
    },
    "virgo": {
        "gift": "precision",
        "pace": "careful refinement",
        "shadow": "over-correcting what is already good enough",
    },
    "libra": {
        "gift": "social balance",
        "pace": "relational calibration",
        "shadow": "stalling in indecision",
    },
    "scorpio": {
        "gift": "focus",
        "pace": "deep commitment",
        "shadow": "tightening around control",
    },
    "sagittarius": {
        "gift": "big-picture momentum",
        "pace": "expansive movement",
        "shadow": "skipping over practicalities",
    },
    "capricorn": {
        "gift": "discipline",
        "pace": "measured progress",
        "shadow": "treating every hour like a test",
    },
    "aquarius": {
        "gift": "perspective",
        "pace": "conceptual leaps",
        "shadow": "detaching from the human mood in the room",
    },
    "pisces": {
        "gift": "imagination",
        "pace": "intuitive flow",
        "shadow": "letting boundaries blur",
    },
}


def _clean(text: str | None) -> str:
    return " ".join((text or "").split()).strip()


def _normalize(text: str) -> str:
    return re.sub(r"\W+", " ", text.casefold()).strip()


def _word_count(text: str) -> int:
    return len(_WORD_RE.findall((text or "").casefold()))


def _sentence_count(text: str) -> int:
    cleaned = _clean(text)
    if not cleaned:
        return 0
    return len([part for part in _SENTENCE_SPLIT_RE.split(cleaned) if part.strip()])


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


def _first_sentences(text: str, count: int = 2) -> str:
    cleaned = _clean(text)
    if not cleaned:
        return ""
    parts = [part.strip() for part in _SENTENCE_SPLIT_RE.split(cleaned) if part.strip()]
    return " ".join(parts[:count]).strip()


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


def _sign_value(astrology_facts: dict[str, Any] | None, *keys: str) -> str:
    facts = astrology_facts or {}
    for key in keys:
        value = _clean(facts.get(key))
        if value:
            return value
    return ""


def _sign_trait(sign: str, field: str, fallback: str) -> str:
    if not sign:
        return fallback
    return _SIGN_TRAITS.get(sign.casefold(), {}).get(field, fallback)


def _daily_astrology_sentences(astrology_facts: dict[str, Any] | None) -> dict[str, str]:
    sun = _sign_value(astrology_facts, "sun_sign")
    moon = _sign_value(astrology_facts, "moon_sign")
    rising = _sign_value(astrology_facts, "ascendant", "rising_sign")

    sun_gift = _sign_trait(sun, "gift", "clarity")
    sun_shadow = _sign_trait(sun, "shadow", "overcommitting")
    moon_gift = _sign_trait(moon, "gift", "emotional steadiness")
    moon_pace = _sign_trait(moon, "pace", "measured pacing")
    rising_gift = _sign_trait(rising, "gift", "presence")
    rising_shadow = _sign_trait(rising, "shadow", "mixed signals")

    theme = _clean(
        " ".join(
            part
            for part in [
                f"Your {sun} Sun wants {sun_gift} today." if sun else "",
                f"Your {moon} Moon keeps the emotional pace closer to {moon_pace}." if moon else "",
                (
                    f"With {rising} rising, how you enter the room matters almost as much as what you do."
                    if rising
                    else ""
                ),
            ]
            if part
        )
    )
    people = _clean(
        " ".join(
            part
            for part in [
                (
                    f"{rising} rising makes your tone more noticeable than usual, so clean signals land better than over-explaining."
                    if rising
                    else ""
                ),
                (
                    f"Let {moon_gift} shape your delivery instead of letting {rising_shadow} creep into the room."
                    if moon or rising
                    else ""
                ),
            ]
            if part
        )
    )
    work = _clean(
        " ".join(
            part
            for part in [
                f"Work that rewards {sun_gift} and {moon_pace} is likely to pay off faster than open-ended multitasking.",
                (
                    f"Use the stronger {sun} part of your chart for decisions, edits, and practical follow-through."
                    if sun
                    else ""
                ),
            ]
            if part
        )
    )
    timing = _clean(
        " ".join(
            part
            for part in [
                (
                    f"Start the morning with anything that needs {sun_gift.lower()}, then use the afternoon for more visible or collaborative moves."
                    if sun or rising
                    else "Morning is better for clean decisions; the afternoon is better for looser collaboration."
                ),
                (
                    f"By tonight, guard against {sun_shadow} and let the day close on something simple and finished."
                    if sun
                    else "Tonight is better for closure than for starting something new."
                ),
            ]
            if part
        )
    )
    watch = _clean(
        " ".join(
            part
            for part in [
                f"The shadow to watch is {sun_shadow}." if sun else "",
                (
                    f"Once the emotional weather turns brittle, {moon_gift.lower()} works better than forcing the pace."
                    if moon
                    else ""
                ),
            ]
            if part
        )
    )
    closing = _clean(
        " ".join(
            part
            for part in [
                (
                    f"Let the day end with one completed loop so the stronger {sun_gift.lower()} of your chart stays intact into tomorrow."
                    if sun
                    else "End the day by closing one loop so your attention resets cleanly."
                ),
                (
                    f"{moon} Moon energy responds well to a quieter finish than a dramatic late push."
                    if moon
                    else ""
                ),
            ]
            if part
        )
    )

    return {
        "theme": theme,
        "people": people,
        "work": work,
        "timing": timing,
        "watch": watch,
        "closing": closing,
    }


def _append_unique_sentences(base_text: str, extras: list[str]) -> str:
    combined = [base_text.strip()] if base_text.strip() else []
    seen = {_normalize(base_text)} if base_text.strip() else set()
    for extra in extras:
        cleaned = _clean(extra)
        if not cleaned:
            continue
        marker = _normalize(cleaned)
        if not marker or marker in seen:
            continue
        seen.add(marker)
        combined.append(cleaned)
    return _dedupe_sentences(" ".join(combined))


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


def _enrich_block(
    block: dict[str, str],
    *,
    extras: list[str],
    minimum_words: int = 32,
    minimum_sentences: int = 2,
) -> dict[str, str]:
    headline = _clean(block.get("headline"))
    detail = _clean(block.get("detail"))
    text = _clean(block.get("text"))

    if (
        detail
        and _word_count(detail) >= minimum_words
        and _sentence_count(detail) >= minimum_sentences
    ):
        return {
            "headline": headline,
            "detail": detail,
            "text": detail or headline or text,
        }

    base_detail = detail or text or headline
    enriched_detail = _append_unique_sentences(base_detail, extras)
    if headline and _normalize(enriched_detail) == _normalize(headline):
        enriched_detail = ""

    return {
        "headline": headline,
        "detail": enriched_detail,
        "text": enriched_detail or headline or text,
    }


def map_daily_preview(normalized) -> dict:
    theme = _daily_block(
        normalized,
        section_id="today_theme",
        fallback_text=_clean(
            getattr(normalized, "opening_hook", "")
            or getattr(normalized, "reading_opening", "")
        ),
        fallback_headline=_clean(getattr(normalized, "opening_hook", "")),
    )
    energy = _daily_block(
        normalized,
        section_id="today_energy",
        fallback_text=_clean(
            getattr(normalized, "current_pattern", "")
            or getattr(normalized, "astrological_foundation", "")
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
            getattr(normalized, "emotional_truth", "")
            or getattr(normalized, "what_this_is_asking_of_you", "")
        ),
        fallback_headline=_clean(getattr(normalized, "emotional_truth", "")),
    )
    headline = _clean(theme.get("headline") or theme.get("text"))
    teaser = _first_sentences(
        _clean(theme.get("detail") or theme.get("text") or energy.get("text")),
        count=2,
    )
    if not teaser or _normalize(teaser) == _normalize(headline):
        teaser = _clean(energy.get("headline") or energy.get("text") or headline)
    deeper_layer = _clean(
        "Inside the full read: the best move, the watch-out, people/work energy, "
        "and the timing window that helps today land cleanly."
    )

    return {
        "headline": headline or _clean(getattr(normalized, "opening_hook", "")),
        "teaser_text": teaser or headline,
        "today_energy": _clean(energy.get("headline") or energy.get("text")),
        "best_move_teaser": _clean(best_move.get("headline") or best_move.get("text")),
        "watch_out_teaser": _clean(watch_out.get("headline") or watch_out.get("text")),
        "deeper_layer_teaser": deeper_layer,
        "schema_fields": DAILY_HOROSCOPE_PREVIEW_FIELDS,
    }


def map_daily_reading(normalized, astrology_facts: dict[str, Any] | None = None) -> dict:
    astro = _daily_astrology_sentences(astrology_facts)

    today_theme = _enrich_block(
        _daily_block(
            normalized,
            section_id="today_theme",
            fallback_text=_clean(
                getattr(normalized, "reading_opening", "")
                or getattr(normalized, "opening_hook", "")
            ),
            fallback_headline=_clean(getattr(normalized, "opening_hook", "")),
            fallback_detail=astro["theme"],
        ),
        extras=[
            _clean(getattr(normalized, "current_pattern", "")),
            astro["theme"],
        ],
    )
    today_energy = _enrich_block(
        _daily_block(
            normalized,
            section_id="today_energy",
            fallback_text=_clean(
                getattr(normalized, "astrological_foundation", "")
                or getattr(normalized, "current_pattern", "")
            ),
            fallback_headline=_clean(getattr(normalized, "current_pattern", "")),
            fallback_detail=astro["theme"],
        ),
        extras=[
            _clean(getattr(normalized, "astrological_foundation", "")),
            astro["theme"],
        ],
    )
    best_move = _enrich_block(
        _daily_block(
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
            fallback_detail="Choose the move that reduces friction, not the one that only feels busy.",
        ),
        extras=[
            _clean(getattr(normalized, "practical_guidance", "")),
            "Start with the task that makes the rest of the day easier to trust.",
            "Do not start with the loudest demand; start with the move that leaves the cleanest trail for the rest of the day.",
        ],
    )
    watch_out = _enrich_block(
        _daily_block(
            normalized,
            section_id="watch_out_for",
            fallback_text=_clean(
                getattr(normalized, "what_this_is_asking_of_you", "")
                or getattr(normalized, "emotional_truth", "")
            ),
            fallback_headline=_clean(getattr(normalized, "emotional_truth", "")),
            fallback_detail=astro["watch"],
        ),
        extras=[
            _clean(getattr(normalized, "emotional_truth", "")),
            astro["watch"],
        ],
    )
    people_energy = _enrich_block(
        _daily_block(
            normalized,
            section_id="people_energy",
            fallback_headline="Clear communication is more useful than extra charm today.",
            fallback_detail=astro["people"],
        ),
        extras=[
            astro["people"],
            "Ask directly for what you need and keep your wording clean.",
        ],
    )
    work_focus = _enrich_block(
        _daily_block(
            normalized,
            section_id="work_focus",
            fallback_headline="The day is stronger for practical progress than loose multitasking.",
            fallback_detail=astro["work"],
        ),
        extras=[
            astro["work"],
            _clean(getattr(normalized, "practical_guidance", "")),
        ],
    )
    timing = _enrich_block(
        _daily_block(
            normalized,
            section_id="timing",
            fallback_headline="Morning is sharper; the afternoon is better for looser collaboration.",
            fallback_detail=astro["timing"],
        ),
        extras=[
            astro["timing"],
            "Use the first half of the day for anything that needs discernment, and leave catch-up or softer conversations for later.",
        ],
    )
    closing_guidance = _enrich_block(
        _daily_block(
            normalized,
            section_id="closing_guidance",
            fallback_text=_clean(
                getattr(normalized, "next_return_invitation", "")
                or getattr(normalized, "premium_teaser", "")
            ),
            fallback_headline=_clean(
                getattr(normalized, "next_return_invitation", "")
                or getattr(normalized, "premium_teaser", "")
            ),
            fallback_detail=astro["closing"],
        ),
        extras=[
            astro["closing"],
            "Before tonight ends, close one loop so tomorrow begins with less drag.",
        ],
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
