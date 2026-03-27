from __future__ import annotations

import re

ANNUAL_DRIFT_PATTERNS = [
    r"\bthis year\b",
    r"\byear ahead\b",
    r"\bcoming year\b",
    r"\bmonths ahead\b",
    r"\blunar new year\b",
    r"\bseason ahead\b",
    r"\byour cycle this year\b",
]


def validate_daily_payload(payload: dict) -> list[str]:
    text = "\n".join(section.get("text", "") for section in payload.get("sections", []))
    lowered = text.casefold()
    issues: list[str] = []
    for pattern in ANNUAL_DRIFT_PATTERNS:
        if re.search(pattern, lowered):
            issues.append(f"daily_drift_detected:{pattern}")
    return issues
