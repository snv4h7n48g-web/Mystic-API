from __future__ import annotations


def _clean(text: str | None) -> str:
    return " ".join((text or "").split()).strip()


def _pick(used: set[str], *candidates: str) -> str:
    for candidate in candidates:
        cleaned = _clean(candidate)
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in used:
            continue
        used.add(key)
        return cleaned
    return ""


def _join_sentences(*parts: str) -> str:
    cleaned_parts: list[str] = []
    seen: set[str] = set()
    for part in parts:
        cleaned = _clean(part)
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        if cleaned[-1] not in ".!?":
            cleaned = f"{cleaned}."
        cleaned_parts.append(cleaned)
    return " ".join(cleaned_parts).strip()


def _strip_repeated_lead(summary: str, detail: str) -> str:
    cleaned_summary = _clean(summary)
    cleaned_detail = _clean(detail)
    if not cleaned_summary or not cleaned_detail:
        return cleaned_detail
    summary_key = cleaned_summary.casefold().rstrip(".!?")
    detail_key = cleaned_detail.casefold()
    if detail_key == summary_key or detail_key == f"{summary_key}.":
        return ""
    if detail_key.startswith(summary_key):
        remainder = cleaned_detail[len(cleaned_summary):].lstrip()
        if remainder.startswith("."):
            remainder = remainder[1:].lstrip()
        return remainder
    return cleaned_detail


def _year_label(lunar_context: dict) -> str:
    current_year = lunar_context.get("current_year") or {}
    return _clean(current_year.get("year_label"))


def _birth_combined(lunar_context: dict) -> str:
    birth = lunar_context.get("birth_zodiac") or {}
    return _clean(birth.get("combined"))


def _year_combined(lunar_context: dict) -> str:
    current_year = lunar_context.get("current_year") or {}
    year_animal = current_year.get("year_animal") or {}
    return _clean(year_animal.get("combined"))


def _default_cycle_theme(lunar_context: dict) -> str:
    birth = _birth_combined(lunar_context)
    year = _year_combined(lunar_context)
    interaction = (lunar_context.get("interaction") or {}).get("reading", "")
    year_headline = ((lunar_context.get("current_year") or {}).get("year_animal") or {}).get("headline", "")
    if birth and year:
        return _join_sentences(
            f"{_year_label(lunar_context)} opens as a {year} cycle for a {birth} soul",
            year_headline,
            interaction,
        )
    return _join_sentences(_year_label(lunar_context), year_headline)


def _default_year_symbolism(lunar_context: dict) -> str:
    current_year = lunar_context.get("current_year") or {}
    year_animal = current_year.get("year_animal") or {}
    year_element = current_year.get("year_element") or {}
    return _join_sentences(
        year_animal.get("symbolism", ""),
        year_animal.get("opportunity", ""),
        year_animal.get("caution", ""),
        f"The {year_element.get('element', '')} element brings a tone of {year_element.get('tone', '')}" if year_element.get("element") and year_element.get("tone") else "",
    )


def _default_welcome_release(lunar_context: dict) -> str:
    birth = lunar_context.get("birth_zodiac") or {}
    interaction = lunar_context.get("interaction") or {}
    welcome = ""
    release = ""
    if birth.get("gifts"):
        welcome = f"Welcome more of your native strength around {birth.get('gifts')}"
    if birth.get("cautions"):
        release = f"Release the pattern of {birth.get('cautions')}"
    return _join_sentences(interaction.get("reading", ""), welcome, release)


def _default_move_well(lunar_context: dict) -> str:
    birth = lunar_context.get("birth_zodiac") or {}
    current_year = lunar_context.get("current_year") or {}
    year_element = current_year.get("year_element") or {}
    return _join_sentences(
        birth.get("move_well", ""),
        year_element.get("move_well", ""),
        f"Let this year be guided by {birth.get('archetype')}" if birth.get("archetype") else "",
    )


def _default_closing(lunar_context: dict) -> str:
    birth = _birth_combined(lunar_context)
    year = _year_combined(lunar_context)
    if birth and year:
        return f"What would it look like for a {birth} person to move through this {year} year with intention rather than reaction?"
    return "What part of this new year-cycle are you being asked to enter more consciously?"


def _cycle_theme_detail(normalized, lunar_context: dict, summary: str) -> str:
    interaction = lunar_context.get("interaction") or {}
    birth = lunar_context.get("birth_zodiac") or {}
    detail = _join_sentences(
        getattr(normalized, "reading_opening", ""),
        getattr(normalized, "snapshot_main_tension", ""),
        interaction.get("reading", ""),
        f"Your native rhythm carries the themes of {', '.join(birth.get('themes', []))}" if birth.get("themes") else "",
    )
    detail = _strip_repeated_lead(summary, detail)
    if not detail:
        return _join_sentences(
            "This opening is less a prediction than a threshold marker: it names the mood of the year and the kind of choice it will keep pressing back into your hands.",
        )
    return _join_sentences(
        detail,
        "Read this opening as the threshold of the year rather than the whole story.",
    )


def _year_symbolism_detail(normalized, lunar_context: dict, summary: str) -> str:
    current_year = lunar_context.get("current_year") or {}
    year_animal = current_year.get("year_animal") or {}
    year_element = current_year.get("year_element") or {}
    detail = _join_sentences(
        getattr(normalized, "current_pattern", ""),
        year_animal.get("symbolism", ""),
        year_animal.get("opportunity", ""),
        year_animal.get("caution", ""),
        f"The {year_element.get('element', '')} element brings {year_element.get('gift', '')}" if year_element.get("element") and year_element.get("gift") else "",
        f"The {year_element.get('element', '')} element brings a tone of {year_element.get('tone', '')}" if year_element.get("element") and year_element.get("tone") and not year_element.get("gift") else "",
    )
    detail = _strip_repeated_lead(summary, detail)
    return detail or _join_sentences(
        year_animal.get("opportunity", ""),
        year_animal.get("caution", ""),
        f"The {year_element.get('element', '')} element brings a tone of {year_element.get('tone', '')}" if year_element.get("element") and year_element.get("tone") else "",
    )


def _welcome_release_detail(normalized, lunar_context: dict, summary: str) -> str:
    birth = lunar_context.get("birth_zodiac") or {}
    asking = getattr(normalized, "what_this_is_asking_of_you", "")
    emotional_truth = getattr(normalized, "emotional_truth", "")
    welcome_line = f"Welcome the side of yourself that knows how to work through {birth.get('gifts')}" if birth.get("gifts") else ""
    release_line = f"Release the habit of {birth.get('cautions')}" if birth.get("cautions") else ""
    detail = _join_sentences(
        emotional_truth,
        asking,
        welcome_line,
        release_line,
    )
    detail = _strip_repeated_lead(summary, detail)
    return detail or _join_sentences(welcome_line, release_line)


def _move_well_detail(normalized, lunar_context: dict, summary: str) -> str:
    birth = lunar_context.get("birth_zodiac") or {}
    year_element = ((lunar_context.get("current_year") or {}).get("year_element") or {})
    next_move = getattr(normalized, "your_next_move", "")
    practical = getattr(normalized, "practical_guidance", "")
    detail = _join_sentences(
        next_move,
        practical,
        birth.get("move_well", ""),
        year_element.get("move_well", ""),
    )
    detail = _strip_repeated_lead(summary, detail)
    return detail or _join_sentences(
        birth.get("move_well", ""),
        year_element.get("move_well", ""),
    )


def _closing_detail(normalized, lunar_context: dict, summary: str) -> str:
    detail = _join_sentences(
        getattr(normalized, "next_return_invitation", ""),
        getattr(normalized, "premium_teaser", ""),
        _default_closing(lunar_context),
    )
    detail = _strip_repeated_lead(summary, detail)
    return detail or _default_closing(lunar_context)


def map_lunar_preview(normalized, lunar_context: dict | None = None) -> dict:
    lunar_context = lunar_context or {}
    used: set[str] = set()
    cycle_theme = _pick(
        used,
        getattr(normalized, "opening_hook", ""),
        getattr(normalized, "snapshot_core_theme", ""),
        _default_cycle_theme(lunar_context),
    )
    year_symbolism = _pick(
        used,
        getattr(normalized, "current_pattern", ""),
        getattr(normalized, "premium_teaser", ""),
        _default_year_symbolism(lunar_context),
        getattr(normalized, "practical_guidance", ""),
    )
    welcome_release = _pick(
        used,
        getattr(normalized, "emotional_truth", ""),
        _default_welcome_release(lunar_context),
        getattr(normalized, "next_return_invitation", ""),
        getattr(normalized, "practical_guidance", ""),
    )
    movement_guidance = _pick(
        used,
        getattr(normalized, "practical_guidance", ""),
        _default_move_well(lunar_context),
        getattr(normalized, "next_return_invitation", ""),
        getattr(normalized, "premium_teaser", ""),
    )
    return {
        "headline": cycle_theme,
        "cycle_theme_teaser": cycle_theme,
        "year_symbolism_teaser": year_symbolism,
        "welcome_release_teaser": welcome_release,
        "movement_guidance_teaser": movement_guidance,
    }


def map_lunar_reading(normalized, lunar_context: dict | None = None) -> dict:
    lunar_context = lunar_context or {}
    used: set[str] = set()
    cycle_theme = _pick(
        used,
        getattr(normalized, "opening_hook", ""),
        getattr(normalized, "reading_opening", ""),
        getattr(normalized, "snapshot_core_theme", ""),
        _default_cycle_theme(lunar_context),
    )
    year_symbolism = _pick(
        used,
        getattr(normalized, "current_pattern", ""),
        getattr(normalized, "premium_teaser", ""),
        _default_year_symbolism(lunar_context),
        getattr(normalized, "practical_guidance", ""),
    )
    welcome_release = _pick(
        used,
        getattr(normalized, "emotional_truth", ""),
        getattr(normalized, "what_this_is_asking_of_you", ""),
        _default_welcome_release(lunar_context),
        getattr(normalized, "next_return_invitation", ""),
    )
    movement_guidance = _pick(
        used,
        getattr(normalized, "your_next_move", ""),
        getattr(normalized, "practical_guidance", ""),
        _default_move_well(lunar_context),
        getattr(normalized, "next_return_invitation", ""),
        getattr(normalized, "premium_teaser", ""),
    )
    closing = _pick(
        used,
        getattr(normalized, "next_return_invitation", ""),
        _default_closing(lunar_context),
        getattr(normalized, "premium_teaser", ""),
        getattr(normalized, "practical_guidance", ""),
    )
    return {
        "opening_invocation": cycle_theme,
        "opening_invocation_detail": _cycle_theme_detail(normalized, lunar_context, cycle_theme),
        "lunar_forecast": year_symbolism,
        "lunar_forecast_detail": _year_symbolism_detail(normalized, lunar_context, year_symbolism),
        "integrated_synthesis": welcome_release,
        "integrated_synthesis_detail": _welcome_release_detail(normalized, lunar_context, welcome_release),
        "reflective_guidance": movement_guidance,
        "reflective_guidance_detail": _move_well_detail(normalized, lunar_context, movement_guidance),
        "closing_prompt": closing,
        "closing_prompt_detail": _closing_detail(normalized, lunar_context, closing),
    }
