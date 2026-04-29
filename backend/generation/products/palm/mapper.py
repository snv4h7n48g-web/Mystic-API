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


def _sentence(text: str) -> str:
    cleaned = _clean(text)
    if not cleaned:
        return ""
    return cleaned if cleaned[-1] in ".!?" else f"{cleaned}."


def _feature_labels(palm_features: list[dict] | None) -> list[str]:
    labels: list[str] = []
    for feature in palm_features or []:
        name = _clean(str(feature.get("feature") or "")).replace("_", " ")
        value = _clean(str(feature.get("value") or ""))
        if not name or value.casefold() in {"", "unknown", "none", "null"}:
            continue
        labels.append(f"{name}: {value}")
    return labels[:4]


def _feature_summary(palm_features: list[dict] | None) -> str:
    labels = _feature_labels(palm_features)
    if not labels:
        return (
            "The palm lines suggest a pattern that is best read signal by signal: "
            "what appears in the hand points to how energy, attention, and feeling are being carried."
        )
    return (
        "The palm signals most visible here are "
        f"{'; '.join(labels)}. Together, these hand features suggest where your energy is being held, "
        "where it wants more room, and what the next choice needs to respect."
    )


def _guidance_from_features(palm_features: list[dict] | None) -> str:
    labels = _feature_labels(palm_features)
    if not labels:
        return (
            "Use the palm as a practical mirror: choose one line of pressure you can name, "
            "then make the next action smaller and clearer than the feeling around it."
        )
    first = labels[0].split(":", 1)[0]
    return (
        f"Let the {first} be the anchor for the next move: name what it points to, "
        "then choose one grounded action that gives that part of your life more honesty and less strain."
    )


def map_palm_reading(normalized, palm_features: list[dict] | None = None) -> dict[str, str]:
    used: set[str] = set()
    feature_summary = _feature_summary(palm_features)
    feature_guidance = _guidance_from_features(palm_features)

    opening = _pick(
        used,
        getattr(normalized, "opening_hook", ""),
        "Your palm is emphasizing a pattern that wants to be interpreted rather than rushed.",
    )
    palm_insight = _pick(
        used,
        getattr(normalized, "palm_revelation", ""),
        getattr(normalized, "current_pattern", ""),
        feature_summary,
    )
    synthesis = _pick(
        used,
        getattr(normalized, "signals_agree", ""),
        getattr(normalized, "emotional_truth", ""),
        getattr(normalized, "what_this_is_asking_of_you", ""),
        feature_summary,
    )
    guidance = _pick(
        used,
        getattr(normalized, "your_next_move", ""),
        getattr(normalized, "practical_guidance", ""),
        feature_guidance,
    )
    closing = _pick(
        used,
        getattr(normalized, "next_return_invitation", ""),
        "Return to this reading when the hand's signal feels active again, and ask what has changed in how you are carrying it.",
    )

    if "palm" not in palm_insight.casefold() and "line" not in palm_insight.casefold():
        palm_insight = _sentence(feature_summary) + " " + palm_insight
    if "suggest" not in palm_insight.casefold() and "points to" not in palm_insight.casefold():
        palm_insight = palm_insight + " This suggests the hand is showing meaning, not just surface detail."

    return {
        "opening_invocation": opening,
        "palm_insight": palm_insight,
        "integrated_synthesis": synthesis,
        "reflective_guidance": guidance,
        "closing_prompt": closing,
    }
