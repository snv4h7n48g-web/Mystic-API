from __future__ import annotations

from dataclasses import dataclass, field
import re

from .products.compatibility.validator import validate_compatibility_payload
from .products.daily_horoscope.validator import validate_daily_payload
from .products.feng_shui.validator import validate_feng_shui_payload
from .products.full_reading.validator import validate_full_reading_payload
from .products.lunar.validator import validate_lunar_payload
from .products.palm.validator import validate_palm_payload
from .products.tarot.validator import validate_tarot_payload


@dataclass(frozen=True)
class ValidationResult:
    product_key: str
    passed: bool
    issues: list[str] = field(default_factory=list)
    retry_hint: str | None = None
    hard_fail: bool = False

    @property
    def valid(self) -> bool:
        return self.passed


@dataclass(frozen=True)
class SectionSafetyResult:
    section_id: str
    passed: bool
    issues: list[str] = field(default_factory=list)


_PLACEHOLDER_RE = re.compile(r"^(?:todo|tbd|coming soon|placeholder|n/?a|none|null|\.{3,}|—+|-+)$", re.IGNORECASE)
_STUB_RE = re.compile(r'^\s*(?:\d+[.):-]?|[-*])\s*$')
_DANGLING_RE = re.compile(r'(?:steps?|guidance|next steps?|next move)\s*:\s*1\.?\s*$', re.IGNORECASE)
_TRUNCATED_RE = re.compile(r'(?:[:;,-]|\b(?:and|or|to|with|consider|including|like|such as|for example)\s*)$', re.IGNORECASE)


def _section_primary_text(section: dict) -> str:
    return str(section.get("detail") or section.get("text") or "").strip()


def assess_section_safety(section: dict) -> SectionSafetyResult:
    section_id = str(section.get("id") or "unknown")
    text = _section_primary_text(section)
    issues: list[str] = []

    if not text:
        issues.append("missing_text")
    elif _PLACEHOLDER_RE.match(text):
        issues.append("placeholder_text")
    elif _STUB_RE.match(text) or _DANGLING_RE.search(text) or _TRUNCATED_RE.search(text):
        issues.append("malformed_text")

    return SectionSafetyResult(section_id=section_id, passed=not issues, issues=issues)


VALIDATORS = {
    "daily": validate_daily_payload,
    "lunar": validate_lunar_payload,
    "tarot": validate_tarot_payload,
    "compatibility": validate_compatibility_payload,
    "palm": validate_palm_payload,
    "feng_shui": validate_feng_shui_payload,
    "full_reading": validate_full_reading_payload,
}

RETRY_HINTS = {
    "daily": "Correct the output into a true daily horoscope about today only. Use a recognisable daily structure with all eight sections: today's theme, today's energy, best move, watch out for, people energy, work/focus, timing, and closing guidance. Fill the daily_sections object with distinct headline/detail pairs. Each detail should be 2-4 concrete sentences, roughly 35-70 words, and include at least one usable cue, action, timing note, or relationship/work implication. Keep timing immediate and concrete, remove year-ahead or Lunar framing, stop repeating the same sentence or stem across sections, and remove any teaser/upsell language about deeper dives or personalised readings from the actual horoscope copy.",
    "lunar": "Correct the output into a Lunar New Year year-ahead reading. Remove today-style wording, avoid duplicate sections, and keep the year-cycle frame explicit. Make the current lunar year animal and element matter. If lunar_context is present, make the user's birth zodiac and its relationship to the current year visibly shape the reading. Ensure cycle theme, year symbolism, welcome/release, and movement guidance are all distinct and materially developed.",
    "tarot": "Correct the output into a card-led tarot reading. Return tarot_spread_overview, tarot_card_chapters, and tarot_spread_story. Name the actual cards, positions, and reversal/upright orientation; each card chapter must explain card meaning, position logic, question relevance, and personal implication; the spread story must synthesize the cards without recapping chapter sentences; and guidance must be concrete, specific, and actionable rather than abstract filler.",
    "compatibility": "Correct the output into a two-person compatibility reading. Make the relationship dynamics, strengths, tensions, and grounded guidance explicit.",
    "palm": "Correct the output into a palm-feature-led reading. Refer to palm lines, mounts, hand shape, or observed features; interpret what each visible signal suggests; and avoid generic divination prose or raw OCR-style description.",
    "feng_shui": "Correct the output into a Feng Shui space analysis. Refer to rooms, layout, placement, flow, clutter, direction, and practical recommendations. Build distinct sections for overview, what_helps, what_blocks, practical_fixes, and action_plan. Practical fixes must include multiple concrete actions that say what to move, clear, place, adjust, add, remove, open, anchor, or soften, and the action plan must prioritise first/next/observe steps. Do not repeat the same sentence across sections.",
    "full_reading": "Correct the output into a layered full premium reading. Provide a non-duplicative three-line snapshot, then distinct body sections for reading_opening, astrological_foundation, palm_revelation when palm is present, tarot_message with actual cards/spread interpretation, signals_agree, what_this_is_asking_of_you, and your_next_move. Astrology must be explicit and interpretive rather than invisible setup. Palm must interpret visible hand signals into meaning, not just describe them. Tarot must explain each card's contribution and spread-level interaction. Do not let summary repeat body, do not let astrology disappear, do not let palm disappear, do not make tarot decorative, and do not duplicate the payoff sections.",
}


def validate_product_payload(product_key: str, payload: dict) -> ValidationResult:
    validator = VALIDATORS.get(product_key)
    if validator is None:
        return ValidationResult(product_key=product_key, passed=True, issues=[])
    issues = validator(payload)
    hard_fail_products = {"daily", "lunar", "tarot", "palm", "feng_shui", "full_reading"}
    return ValidationResult(
        product_key=product_key,
        passed=not issues,
        issues=issues,
        retry_hint=None if not issues else RETRY_HINTS.get(product_key),
        hard_fail=bool(issues) and product_key in hard_fail_products,
    )
