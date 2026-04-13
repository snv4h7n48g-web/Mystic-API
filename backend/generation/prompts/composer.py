from __future__ import annotations

import json
from typing import Any, Optional

from .base import BASE_SYSTEM_PROMPT
from .flow_prompts import FLOW_PROMPTS
from .output_schema import OUTPUT_SCHEMA_INSTRUCTION
from .persona_prompts import PERSONA_PROMPTS

PROMPT_VERSION = "mystic-v1"


def _compact_json(data: Any) -> str:
    return json.dumps(data, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def compose_generation_prompt(
    *,
    persona_id: str,
    flow_id: str,
    continuity_context: Optional[dict[str, Any]],
    domain_context: dict[str, Any],
    contract_instruction: Optional[str] = None,
    retry_instruction: Optional[str] = None,
) -> dict[str, Any]:
    persona_prompt = PERSONA_PROMPTS[persona_id]
    flow_prompt = FLOW_PROMPTS[flow_id]
    continuity_blob = _compact_json(continuity_context or {})
    domain_blob = _compact_json(domain_context)

    messages = [
        f"PERSONA:\n{persona_prompt}",
        f"FLOW:\n{flow_prompt}",
    ]
    if contract_instruction:
        messages.append(f"PRODUCT_CONTRACT:\n{contract_instruction}")
    if retry_instruction:
        messages.append(f"RETRY_CORRECTION:\n{retry_instruction}")
    messages.extend([
        f"CONTINUITY_CONTEXT:\n{continuity_blob}",
        f"DOMAIN_CONTEXT:\n{domain_blob}",
        OUTPUT_SCHEMA_INSTRUCTION,
    ])

    return {
        "system_prompt": BASE_SYSTEM_PROMPT,
        "messages": messages,
        "prompt_version": PROMPT_VERSION,
    }
