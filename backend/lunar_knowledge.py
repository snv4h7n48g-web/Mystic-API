from __future__ import annotations

from datetime import date
from typing import Any

from astrology_engine import get_astrology_engine

# Research grounding used for this first-pass knowledge layer:
# - The Met notes the Chinese zodiac as a 12-year animal cycle and states that
#   February 17, 2026 begins the Year of the Horse, symbolizing power, strength,
#   and vitality.
# - The symbolic interpretations below are product-facing synthesis built on top
#   of those public cultural references and are intended as narrative guidance,
#   not definitive cultural scholarship.

ANIMAL_GROUPS = {
    "Rat": {"trine": ("Rat", "Dragon", "Monkey"), "opposite": "Horse"},
    "Ox": {"trine": ("Ox", "Snake", "Rooster"), "opposite": "Goat"},
    "Tiger": {"trine": ("Tiger", "Horse", "Dog"), "opposite": "Monkey"},
    "Rabbit": {"trine": ("Rabbit", "Goat", "Pig"), "opposite": "Rooster"},
    "Dragon": {"trine": ("Rat", "Dragon", "Monkey"), "opposite": "Dog"},
    "Snake": {"trine": ("Ox", "Snake", "Rooster"), "opposite": "Pig"},
    "Horse": {"trine": ("Tiger", "Horse", "Dog"), "opposite": "Rat"},
    "Goat": {"trine": ("Rabbit", "Goat", "Pig"), "opposite": "Ox"},
    "Monkey": {"trine": ("Rat", "Dragon", "Monkey"), "opposite": "Tiger"},
    "Rooster": {"trine": ("Ox", "Snake", "Rooster"), "opposite": "Rabbit"},
    "Dog": {"trine": ("Tiger", "Horse", "Dog"), "opposite": "Dragon"},
    "Pig": {"trine": ("Rabbit", "Goat", "Pig"), "opposite": "Snake"},
}

ANIMAL_KNOWLEDGE: dict[str, dict[str, Any]] = {
    "Rat": {
        "archetype": "strategic survivor",
        "themes": ["resourcefulness", "timing", "quiet ambition"],
        "gifts": "finding openings others miss and moving quickly once the path is clear",
        "cautions": "scattering energy across too many schemes or protecting yourself so tightly that trust cannot grow",
        "move_well": "keep your plans lean, protect the strongest lead, and let consistency matter more than cleverness alone",
    },
    "Ox": {
        "archetype": "steady builder",
        "themes": ["discipline", "reliability", "earned momentum"],
        "gifts": "turning slow effort into durable results and calming chaos through structure",
        "cautions": "mistaking endurance for the whole answer or staying rigid after the situation has changed",
        "move_well": "back the long game, trim unnecessary obligations, and let patience become visible progress",
    },
    "Tiger": {
        "archetype": "courageous catalyst",
        "themes": ["boldness", "will", "decisive action"],
        "gifts": "breaking deadlock and restoring movement when fear has made everyone passive",
        "cautions": "confusing urgency with truth or burning energy on drama instead of direction",
        "move_well": "choose a worthy fight, act cleanly, and leave room for strategy to temper instinct",
    },
    "Rabbit": {
        "archetype": "sensitive harmonizer",
        "themes": ["discernment", "diplomacy", "protective grace"],
        "gifts": "reading subtle emotional weather and creating safer, more sustainable conditions",
        "cautions": "avoiding necessary friction or staying small to preserve peace",
        "move_well": "honor your sensitivity, but let it sharpen discernment rather than keep you hidden",
    },
    "Dragon": {
        "archetype": "visionary force",
        "themes": ["charisma", "expansion", "high stakes creation"],
        "gifts": "making the path feel larger, more possible, and more alive",
        "cautions": "overshooting reality or expecting intensity to replace craftsmanship",
        "move_well": "build around the biggest honest vision, then give it structure strong enough to hold",
    },
    "Snake": {
        "archetype": "intuitive strategist",
        "themes": ["discernment", "depth", "measured transformation"],
        "gifts": "seeing beneath surfaces and moving with precision instead of noise",
        "cautions": "withholding too much, overcontrolling the timing, or becoming trapped in suspicion",
        "move_well": "trust your pattern-recognition, but let clarity lead rather than fear of exposure",
    },
    "Horse": {
        "archetype": "vital mover",
        "themes": ["freedom", "momentum", "animated will"],
        "gifts": "bringing motion, courage, and a fresh appetite for life",
        "cautions": "running too hot, resisting containment on principle, or mistaking movement for alignment",
        "move_well": "follow what restores aliveness, but give your momentum a direction and a discipline",
    },
    "Goat": {
        "archetype": "creative nurturer",
        "themes": ["care", "beauty", "emotionally intelligent pacing"],
        "gifts": "making life more humane and sustaining what needs tenderness to grow",
        "cautions": "collapsing under emotional noise or waiting for perfect conditions before moving",
        "move_well": "protect softness without becoming passive, and make room for both beauty and backbone",
    },
    "Monkey": {
        "archetype": "inventive trickster",
        "themes": ["adaptability", "wit", "experimentation"],
        "gifts": "reframing stale problems and finding workable solutions through agility",
        "cautions": "treating everything like a puzzle and not enough like a commitment",
        "move_well": "use your intelligence to simplify the path, not to dodge emotional stakes",
    },
    "Rooster": {
        "archetype": "refining truth-teller",
        "themes": ["precision", "standards", "visible order"],
        "gifts": "spotting what needs correction and sharpening blurred situations into something usable",
        "cautions": "overcorrecting, becoming hypercritical, or using certainty to defend against vulnerability",
        "move_well": "keep standards high, but make sure they are serving life instead of punishing it",
    },
    "Dog": {
        "archetype": "loyal guardian",
        "themes": ["devotion", "justice", "protective honesty"],
        "gifts": "holding the line for what is fair, safe, and worth defending",
        "cautions": "living in vigilance, rehearsing disappointment, or expecting betrayal before connection has a chance",
        "move_well": "let loyalty stay active, but choose where to guard and where to soften",
    },
    "Pig": {
        "archetype": "generous restorer",
        "themes": ["abundance", "pleasure", "sincere warmth"],
        "gifts": "bringing ease, trust, and replenishment back into dry situations",
        "cautions": "indulgence without boundaries or assuming goodwill removes the need for discernment",
        "move_well": "receive what nourishes you, but stay awake to where excess blurs your judgment",
    },
}

ELEMENT_KNOWLEDGE: dict[str, dict[str, str]] = {
    "Wood": {
        "tone": "growth, flexibility, and forward movement",
        "gift": "renewal, creative expansion, and the courage to begin again",
        "caution": "growing outward faster than the roots can support",
        "move_well": "choose living growth over frantic expansion and keep tending the foundations",
    },
    "Fire": {
        "tone": "visibility, passion, and animated momentum",
        "gift": "confidence, magnetism, and the power to energize a stagnant situation",
        "caution": "burnout, impulsiveness, or drama that outruns substance",
        "move_well": "let passion light the path, but keep enough discipline to sustain what begins",
    },
    "Earth": {
        "tone": "stability, responsibility, and integration",
        "gift": "grounding, stewardship, and the ability to turn plans into something dependable",
        "caution": "heaviness, over-obligation, or fear of necessary change",
        "move_well": "build slowly, prune what is no longer viable, and protect the essentials",
    },
    "Metal": {
        "tone": "clarity, standards, and refinement",
        "gift": "discernment, precision, and the ability to cut away what weakens the whole",
        "caution": "rigidity, overcontrol, or coldness disguised as clarity",
        "move_well": "choose clean priorities and let sharpness serve wisdom rather than defensiveness",
    },
    "Water": {
        "tone": "intuition, adaptability, and depth",
        "gift": "wisdom, emotional intelligence, and strategic movement through changing conditions",
        "caution": "drift, avoidance, or dissolving boundaries",
        "move_well": "flow where the situation asks for flexibility, but do not surrender your center",
    },
}

YEAR_ANIMAL_OVERRIDES: dict[str, dict[str, str]] = {
    "Horse": {
        "headline": "a year that rewards motion, courage, and visible aliveness",
        "symbolism": "The Horse year asks whether your momentum is truly liberating you or merely keeping you busy.",
        "opportunity": "Fresh starts, bold pivots, travel, visibility, and reclaiming vitality are often amplified.",
        "caution": "Restlessness, scattered effort, ego-driven leaps, and impatience with slower growth can cost more than expected.",
    },
}


def _animal_entry(animal: str) -> dict[str, Any]:
    return ANIMAL_KNOWLEDGE.get(animal, {})


def _element_entry(element: str) -> dict[str, str]:
    return ELEMENT_KNOWLEDGE.get(element, {})


def classify_zodiac_relationship(birth_animal: str, current_year_animal: str) -> dict[str, str]:
    if not birth_animal or not current_year_animal:
        return {"type": "unknown", "reading": ""}
    if birth_animal == current_year_animal:
        return {
            "type": "return",
            "reading": "This is a return-cycle year, which tends to amplify identity, repetition, and the need to choose consciously rather than run on old instinct.",
        }
    group = ANIMAL_GROUPS.get(birth_animal, {})
    if current_year_animal == group.get("opposite"):
        return {
            "type": "opposition",
            "reading": "This year animal presses against your defaults, so growth is more likely to arrive through friction, contrast, and the need to adapt.",
        }
    if current_year_animal in group.get("trine", ()):
        return {
            "type": "allied",
            "reading": "This year animal tends to work with your nature, so support, momentum, and more natural timing may be easier to access if you still act with discipline.",
        }
    return {
        "type": "mixed",
        "reading": "This pairing is mixed rather than obviously easy or difficult, which often makes the year more about calibration than fate.",
    }


def build_lunar_prompt_context(*, birth_zodiac: dict[str, str] | None, current_year: int, current_year_zodiac: dict[str, str] | None = None) -> dict[str, Any]:
    engine = get_astrology_engine()
    year_zodiac = current_year_zodiac or engine.calculate_chinese_zodiac(current_year)
    birth_animal = (birth_zodiac or {}).get("animal", "")
    birth_element = (birth_zodiac or {}).get("element", "")
    year_animal = year_zodiac.get("animal", "")
    year_element = year_zodiac.get("element", "")
    birth_relationship = classify_zodiac_relationship(birth_animal, year_animal) if birth_animal else {"type": "year_only", "reading": ""}

    year_override = YEAR_ANIMAL_OVERRIDES.get(year_animal, {})
    year_animal_entry = _animal_entry(year_animal)
    year_element_entry = _element_entry(year_element)

    current_year_summary = {
        "gregorian_year": current_year,
        "year_label": f"{current_year}: Year of the {year_zodiac.get('combined', year_animal)}",
        "cycle_marker": "February 17, 2026 begins the Year of the Horse." if current_year == 2026 else "",
        "year_animal": {
            "animal": year_animal,
            "element": year_element,
            "combined": year_zodiac.get("combined", ""),
            "headline": year_override.get("headline") or f"A {year_animal} year foregrounds {', '.join(year_animal_entry.get('themes', [])[:3])}.",
            "symbolism": year_override.get("symbolism") or f"The {year_animal} brings a tone of {year_animal_entry.get('archetype', 'movement and symbolic change')}.",
            "opportunity": year_override.get("opportunity") or year_animal_entry.get("gifts", ""),
            "caution": year_override.get("caution") or year_animal_entry.get("cautions", ""),
        },
        "year_element": {
            "element": year_element,
            "tone": year_element_entry.get("tone", ""),
            "gift": year_element_entry.get("gift", ""),
            "caution": year_element_entry.get("caution", ""),
            "move_well": year_element_entry.get("move_well", ""),
        },
    }

    if not birth_zodiac:
        return {
            "current_year": current_year_summary,
            "reading_focus": [
                current_year_summary["year_animal"]["headline"],
                current_year_summary["year_animal"]["opportunity"],
                current_year_summary["year_animal"]["caution"],
                current_year_summary["year_element"]["move_well"],
            ],
        }

    birth_animal_entry = _animal_entry(birth_animal)
    birth_element_entry = _element_entry(birth_element)
    interaction_hook = (
        f"A {birth_zodiac.get('combined', birth_animal)} person moving through a {year_zodiac.get('combined', year_animal)} year is working with a "
        f"{birth_relationship['type']} dynamic."
    )

    return {
        "birth_zodiac": {
            "animal": birth_animal,
            "element": birth_element,
            "combined": birth_zodiac.get("combined", ""),
            "archetype": birth_animal_entry.get("archetype", ""),
            "themes": birth_animal_entry.get("themes", []),
            "gifts": birth_animal_entry.get("gifts", ""),
            "cautions": birth_animal_entry.get("cautions", ""),
            "move_well": birth_animal_entry.get("move_well", ""),
            "element_tone": birth_element_entry.get("tone", ""),
        },
        "current_year": current_year_summary,
        "interaction": {
            "type": birth_relationship["type"],
            "reading": birth_relationship["reading"],
            "hook": interaction_hook,
        },
        "reading_focus": [
            interaction_hook,
            birth_relationship["reading"],
            current_year_summary["year_animal"]["opportunity"],
            current_year_summary["year_animal"]["caution"],
            current_year_summary["year_element"]["move_well"],
        ],
    }


def lunar_knowledge_sources() -> list[dict[str, str]]:
    return [
        {
            "title": "The Met - Celebrating the Year of the Horse",
            "url": "https://www.metmuseum.org/exhibitions/celebrating-the-year-of-the-horse",
            "note": "Used for the 12-year animal cycle framing and the February 17, 2026 Year of the Horse marker.",
        },
        {
            "title": "Internal interpretation layer",
            "url": "",
            "note": "Animal, element, and interaction meanings are product-facing synthesis built on top of public cultural references for narrative guidance.",
        },
    ]


def current_lunar_year_for_date(today: date | None = None) -> int:
    return (today or date.today()).year
