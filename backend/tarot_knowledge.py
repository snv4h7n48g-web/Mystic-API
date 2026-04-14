from __future__ import annotations

import re
from functools import lru_cache
from typing import Any, Dict, List

from reference_knowledge import TAROT_REFERENCE


_CARD_ALIAS = {
    "the hanged one": "the hanged man",
}

_GUIDEBOOK_MAJOR_ARCANA = {
    "the fool": {
        "guidebook_upright": "new beginnings, adventure, innocence, and taking a leap of faith",
        "guidebook_reversed": "foolishness, recklessness, naivety, and poor judgment",
        "guidebook_shadow": "caution, lack of planning, and risk of failure due to carelessness",
    },
    "the magician": {
        "guidebook_upright": "manifestation, power, resourcefulness, and creativity",
        "guidebook_reversed": "manipulation, deceit, or blocked potential",
        "guidebook_shadow": "misuse of power, dishonesty, or lack of clear direction",
    },
    "the high priestess": {
        "guidebook_upright": "intuition, mystery, subconscious wisdom, and inner knowledge",
        "guidebook_reversed": "secrets, disconnected intuition, or hidden agendas",
        "guidebook_shadow": "confusion, superficial thinking, or being out of touch with your inner voice",
    },
    "the empress": {
        "guidebook_upright": "fertility, abundance, beauty, and nurturing energy",
        "guidebook_reversed": "dependence, neglect, or creative blocks",
        "guidebook_shadow": "self-doubt, feeling creatively blocked, or experiencing unfulfilled potential",
    },
    "the emperor": {
        "guidebook_upright": "authority, structure, control, and stability",
        "guidebook_reversed": "tyranny, rigidity, or power struggles",
        "guidebook_shadow": "inflexibility, overbearing authority, or lack of personal control",
    },
    "the hierophant": {
        "guidebook_upright": "tradition, spirituality, conformity, and religious guidance",
        "guidebook_reversed": "rebellion, non-conformity, or questioning tradition",
        "guidebook_shadow": "being overly rigid, dogmatic, or rejecting useful advice",
    },
    "the lovers": {
        "guidebook_upright": "love, harmony, choices, and union",
        "guidebook_reversed": "imbalance, disharmony, or difficult choices",
        "guidebook_shadow": "disharmony, relationship struggles, or poor decisions regarding love",
    },
    "the chariot": {
        "guidebook_upright": "willpower, determination, and victory",
        "guidebook_reversed": "lack of control, direction, or self-discipline",
        "guidebook_shadow": "being directionless, lacking willpower, or giving up on your goals",
    },
    "strength": {
        "guidebook_upright": "inner strength, courage, compassion, and patience",
        "guidebook_reversed": "self-doubt, weakness, or lack of confidence",
        "guidebook_shadow": "insecurity, a lack of self-control, or struggling with inner turmoil",
    },
    "the hermit": {
        "guidebook_upright": "introspection, solitude, and wisdom",
        "guidebook_reversed": "isolation, loneliness, or avoiding reflection",
        "guidebook_shadow": "isolation, withdrawal from society, or ignoring important inner work",
    },
    "wheel of fortune": {
        "guidebook_upright": "change, cycles, and destiny",
        "guidebook_reversed": "bad luck, resistance to change, or unexpected setbacks",
        "guidebook_shadow": "misfortune, stagnation, or the inability to break free from repetitive patterns",
    },
    "justice": {
        "guidebook_upright": "fairness, truth, balance, and legal matters",
        "guidebook_reversed": "injustice, dishonesty, or imbalance",
        "guidebook_shadow": "dishonesty, bias, or unfair outcomes in situations involving justice",
    },
    "the hanged man": {
        "guidebook_upright": "surrender, letting go, and new perspectives",
        "guidebook_reversed": "stagnation, resistance, or delay",
        "guidebook_shadow": "procrastination, fear of change, or clinging to old ways",
    },
    "death": {
        "guidebook_upright": "transformation, endings, and new beginnings",
        "guidebook_reversed": "resistance to change, stagnation, or holding on to the past",
        "guidebook_shadow": "avoidance of necessary endings, fear of change, or emotional stagnation",
    },
    "temperance": {
        "guidebook_upright": "balance, moderation, and harmony",
        "guidebook_reversed": "imbalance, excess, or lack of harmony",
        "guidebook_shadow": "extremes, chaos, or lacking control over situations",
    },
    "the devil": {
        "guidebook_upright": "bondage, materialism, temptation, and addiction",
        "guidebook_reversed": "release, liberation, or overcoming addiction",
        "guidebook_shadow": "repression, denial, or continued entrapment by unhealthy influences",
    },
    "the tower": {
        "guidebook_upright": "sudden upheaval, destruction, and revelation",
        "guidebook_reversed": "avoidance of disaster or fear of change",
        "guidebook_shadow": "denial of impending change, fear of loss, or lingering instability",
    },
    "the star": {
        "guidebook_upright": "hope, inspiration, and spiritual renewal",
        "guidebook_reversed": "hopelessness, lack of faith, or feeling disconnected from purpose",
        "guidebook_shadow": "despair, lack of direction, or giving up hope",
    },
    "the moon": {
        "guidebook_upright": "illusion, intuition, and the subconscious",
        "guidebook_reversed": "clarity, releasing fears, or overcoming confusion",
        "guidebook_shadow": "paranoia, delusion, or clinging to fear-based thinking",
    },
    "the sun": {
        "guidebook_upright": "joy, success, vitality, and positivity",
        "guidebook_reversed": "delayed success, lack of confidence, or temporary setbacks",
        "guidebook_shadow": "self-doubt, temporary challenges, or the inability to see the good in a situation",
    },
    "judgment": {
        "guidebook_upright": "awakening, renewal, and self-reflection",
        "guidebook_reversed": "self-doubt, failure to heed a calling, or stagnation",
        "guidebook_shadow": "avoiding necessary change or refusing to learn from past experiences",
    },
    "the world": {
        "guidebook_upright": "completion, fulfilment, and integration",
        "guidebook_reversed": "incomplete projects, delays, or feeling stuck",
        "guidebook_shadow": "dissatisfaction, delays in success, or obstacles preventing completion",
    },
}


def _normalize_card_name(name: str) -> str:
    cleaned = re.sub(r"\s+", " ", (name or "").strip().lower())
    return _CARD_ALIAS.get(cleaned, cleaned)


def _parse_section_line(block: str, prefix: str) -> str:
    match = re.search(rf"{re.escape(prefix)}\s*(.+)", block, re.IGNORECASE)
    return match.group(1).strip() if match else ""


@lru_cache(maxsize=1)
def tarot_reference_index() -> Dict[str, Dict[str, str]]:
    index: Dict[str, Dict[str, str]] = {}
    lines = TAROT_REFERENCE.splitlines()
    current_name = ""
    current_kind = ""
    bucket: List[str] = []

    def flush() -> None:
        nonlocal current_name, current_kind, bucket
        if not current_name:
            return
        block = "\n".join(bucket).strip()
        key = _normalize_card_name(current_name)
        index[key] = {
            "name": current_name,
            "kind": current_kind,
            "core": _parse_section_line(block, "Core symbolism suggests:"),
            "past": _parse_section_line(block, "Past position indicates:"),
            "present": _parse_section_line(block, "Present position indicates:"),
            "guidance": _parse_section_line(block, "Guidance position points toward:"),
            "shadow": _parse_section_line(block, "Shadow expression suggests:"),
            "traditional": _parse_section_line(block, "Traditional note:"),
            "meaning": _parse_section_line(block, "This card suggests"),
            "balanced": _parse_section_line(block, "Balanced expression indicates"),
        }
        supplement = _GUIDEBOOK_MAJOR_ARCANA.get(key, {})
        if supplement:
            index[key].update(supplement)
        current_name = ""
        current_kind = ""
        bucket = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("Major Arcana: "):
            flush()
            current_name = line.split(": ", 1)[1].strip()
            current_kind = "major"
            continue
        if line.startswith("Minor Arcana: "):
            flush()
            current_name = line.split(": ", 1)[1].strip()
            current_kind = "minor"
            continue
        if current_name:
            bucket.append(line)
    flush()
    return index


def tarot_reference_for_card(name: str) -> Dict[str, str]:
    if not name:
        return {}
    return tarot_reference_index().get(_normalize_card_name(name), {})


def _position_focus(position: str) -> str:
    normalized = position.strip().lower()
    if normalized == "past":
        return "what has already been shaping the situation"
    if normalized == "present":
        return "the live pressure point in the current moment"
    if normalized == "guidance":
        return "the clearest way to respond"
    if normalized == "crossing":
        return "the friction complicating the question"
    if normalized == "card":
        return "the main message of the draw"
    if normalized:
        return f"the role of {normalized} in the spread"
    return "its place in the spread"


def _position_hint(entry: Dict[str, str], position: str) -> str:
    normalized = position.strip().lower()
    if normalized == "past":
        return entry.get("past", "")
    if normalized == "present":
        return entry.get("present", "")
    if normalized == "guidance":
        return entry.get("guidance", "")
    return ""


def build_tarot_card_prompt(card: Dict[str, Any]) -> str:
    name = str(card.get("card") or card.get("name") or "").strip()
    if not name:
        return ""
    position = str(card.get("position") or "").strip()
    orientation = str(card.get("orientation") or "upright").strip().lower()
    entry = tarot_reference_index().get(_normalize_card_name(name), {})
    label_parts = [name]
    if position:
        label_parts.append(position)
    if orientation:
        label_parts.append(orientation)
    label = " | ".join(label_parts)

    core = entry.get("core") or entry.get("meaning")
    guidebook_upright = entry.get("guidebook_upright", "")
    position_hint = _position_hint(entry, position)
    shadow = entry.get("guidebook_reversed") or entry.get("guidebook_shadow") or entry.get("shadow", "")
    traditional = entry.get("traditional", "")
    position_focus = _position_focus(position)

    lines = [f"- {label}"]
    if orientation == "reversed":
        if shadow:
            lines.append(f"  Reversed emphasis: {shadow}.")
        elif core:
            lines.append(f"  Reversed emphasis: the blocked, distorted, or overcorrected side of {core}.")
        lines.append(f"  In this spread, treat it as {position_focus} expressed through resistance, inversion, or avoidance.")
    else:
        if guidebook_upright:
            lines.append(f"  Upright core: {guidebook_upright}.")
        elif core:
            lines.append(f"  Upright core: {core}.")
        if position_hint:
            lines.append(f"  Position cue: {position_hint}.")
        lines.append(f"  In this spread, treat it as {position_focus}.")
    if traditional:
        lines.append(f"  Symbol cue: {traditional}.")
    return "\n".join(lines)


def build_tarot_draw_prompt_context(tarot_cards: List[Dict[str, Any]]) -> str:
    prompts = [build_tarot_card_prompt(card) for card in tarot_cards]
    prompts = [prompt for prompt in prompts if prompt.strip()]
    if not prompts:
        return ""
    return "TAROT DRAW REFERENCE (ground the story in these card notes):\n" + "\n".join(prompts)
