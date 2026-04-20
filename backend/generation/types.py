from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class GenerationContext:
    object_id: str
    object_type: str
    flow_type: str
    surface: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    question: Optional[str] = None
    locale: str = "en-AU"
    timezone: str = "Australia/Melbourne"
    style: Optional[str] = None
    unlocked: bool = False


@dataclass
class NormalizedMysticOutput:
    opening_hook: str
    current_pattern: str
    emotional_truth: str
    practical_guidance: str = ""
    what_this_is_asking_of_you: str = ""
    your_next_move: str = ""
    continuity_callback: Optional[str] = None
    next_return_invitation: str = ""
    premium_teaser: Optional[str] = None
    theme_tags: list[str] = field(default_factory=list)
    snapshot_core_theme: str = ""
    snapshot_main_tension: str = ""
    snapshot_best_next_move: str = ""
    reading_opening: str = ""
    astrological_foundation: str = ""
    palm_revelation: str = ""
    tarot_message: str = ""
    signals_agree: str = ""
    daily_sections: dict[str, dict[str, str]] = field(default_factory=dict)


@dataclass
class GenerationMetadata:
    persona_id: str
    llm_profile_id: str
    prompt_version: str
    model_id: str
    theme_tags: list[str] = field(default_factory=list)
    headline: Optional[str] = None
    continuity_source_session_id: Optional[str] = None


@dataclass
class GenerationTiming:
    total_duration_ms: float = 0.0
    provider_duration_ms: float | None = None
    queue_duration_ms: float | None = None
    model_duration_ms: float | None = None
    time_to_first_output_ms: float | None = None
    parse_duration_ms: float | None = None
    attempt_total_ms: float | None = None
    orchestration_overhead_ms: float | None = None
    retry_count: int = 0
    attempt_count: int = 1
    used_fallback_model: bool = False
    fallback_models_used: list[str] = field(default_factory=list)
    prompt_chars: int = 0
    context_chars: int = 0
    attempt_models: list[str] = field(default_factory=list)
    attempts: list[dict[str, Any]] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OrchestrationResult:
    payload: dict
    metadata: GenerationMetadata
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    generation_metrics: dict[str, Any] = field(default_factory=dict)
