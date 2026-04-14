from __future__ import annotations

import json
from typing import Any, Optional

from .base import BASE_SYSTEM_PROMPT
from .flow_prompts import FLOW_PROMPTS
from .output_schema import OUTPUT_SCHEMA_INSTRUCTION
from .persona_prompts import PERSONA_PROMPTS

PROMPT_VERSION = "mystic-v2"


def _prune_prompt_payload(data: Any) -> Any:
    if isinstance(data, dict):
        cleaned = {
            key: _prune_prompt_payload(value)
            for key, value in data.items()
            if value is not None and value != ""
        }
        return {key: value for key, value in cleaned.items() if value not in ({}, [])}
    if isinstance(data, list):
        cleaned = [_prune_prompt_payload(item) for item in data]
        return [item for item in cleaned if item not in (None, "", {}, [])]
    return data


def _compact_json(data: Any) -> str:
    return json.dumps(_prune_prompt_payload(data), separators=(",", ":"), sort_keys=True, ensure_ascii=False)


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

    prompt_chars = len(BASE_SYSTEM_PROMPT) + sum(len(message) for message in messages)
    return {
        "system_prompt": BASE_SYSTEM_PROMPT,
        "messages": messages,
        "prompt_version": PROMPT_VERSION,
        "prompt_chars": prompt_chars,
        "context_chars": len(continuity_blob) + len(domain_blob),
    }
