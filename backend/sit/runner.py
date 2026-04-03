from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from generation.orchestration import MysticGenerationOrchestrator

from sit.fixtures import get_fixture
from sit.reports import write_report_files
from sit.validators import validate_preview_payload, validate_reading_payload


@dataclass(frozen=True)
class SitCaseDefinition:
    case_id: str
    product_key: str
    description: str
    surface: str
    execute: Callable[[MysticGenerationOrchestrator, dict[str, Any]], Any]


_CASES: dict[str, SitCaseDefinition] = {
    "combined_preview": SitCaseDefinition(
        case_id="combined_preview",
        product_key="full_reading",
        description="Real combined session preview through orchestration.",
        surface="preview",
        execute=lambda orchestrator, fx: orchestrator.build_session_preview_result(
            session=fx["session"],
            user=fx["user"],
            astrology_facts=fx["astrology_facts"],
            tarot_payload=fx["tarot_payload"],
            unlock_price=fx["unlock_price"],
            product_id=fx["product_id"],
            entitlements=fx["entitlements"],
        ),
    ),
    "combined_full_reading": SitCaseDefinition(
        case_id="combined_full_reading",
        product_key="full_reading",
        description="Real combined full reading through orchestration.",
        surface="full",
        execute=lambda orchestrator, fx: orchestrator.build_session_reading_result(
            session=fx["session"],
            user=fx["user"],
            astrology_facts=fx["astrology_facts"],
            tarot_payload=fx["tarot_payload"],
            palm_features=fx["palm_features"],
            include_palm=fx["include_palm"],
            deep_access=fx["deep_access"],
            content_contract=fx["content_contract"],
        ),
    ),
    "daily_preview": SitCaseDefinition(
        case_id="daily_preview",
        product_key="daily",
        description="Real daily preview through orchestration.",
        surface="preview",
        execute=lambda orchestrator, fx: orchestrator.build_session_preview_result(
            session=fx["session"],
            user=fx["user"],
            astrology_facts=fx["astrology_facts"],
            tarot_payload=fx["tarot_payload"],
            unlock_price=fx["unlock_price"],
            product_id=fx["product_id"],
            entitlements=fx["entitlements"],
        ),
    ),
    "daily_full_reading": SitCaseDefinition(
        case_id="daily_full_reading",
        product_key="daily",
        description="Real daily full reading through orchestration.",
        surface="full",
        execute=lambda orchestrator, fx: orchestrator.build_session_reading_result(
            session=fx["session"],
            user=fx["user"],
            astrology_facts=fx["astrology_facts"],
            tarot_payload=fx["tarot_payload"],
            palm_features=[],
            include_palm=False,
            deep_access=fx["deep_access"],
            content_contract=fx["content_contract"],
        ),
    ),
    "tarot_solo_preview": SitCaseDefinition(
        case_id="tarot_solo_preview",
        product_key="tarot",
        description="Real tarot solo preview through orchestration.",
        surface="preview",
        execute=lambda orchestrator, fx: orchestrator.build_session_preview_result(
            session=fx["session"],
            user=fx["user"],
            astrology_facts=fx["astrology_facts"],
            tarot_payload=fx["tarot_payload"],
            unlock_price=fx["unlock_price"],
            product_id=fx["product_id"],
            entitlements=fx["entitlements"],
        ),
    ),
    "compatibility_preview": SitCaseDefinition(
        case_id="compatibility_preview",
        product_key="compatibility",
        description="Real compatibility preview through orchestration.",
        surface="preview",
        execute=lambda orchestrator, fx: orchestrator.build_compatibility_preview_result(
            compat=fx["compat"],
            user=fx["user"],
            person1=fx["person1"],
            person2=fx["person2"],
            chart1=fx["chart1"],
            chart2=fx["chart2"],
            zodiac1=fx["zodiac1"],
            zodiac2=fx["zodiac2"],
            synastry=fx["synastry"],
            zodiac_harmony=fx["zodiac_harmony"],
            entitlements=fx["entitlements"],
        ),
    ),
    "compatibility_full_reading": SitCaseDefinition(
        case_id="compatibility_full_reading",
        product_key="compatibility",
        description="Real compatibility full reading through orchestration.",
        surface="full",
        execute=lambda orchestrator, fx: orchestrator.build_compatibility_reading_result(
            compat=fx["compat"],
            user=fx["user"],
            person1=fx["person1"],
            person2=fx["person2"],
            chart1=fx["chart1"],
            chart2=fx["chart2"],
            synastry=fx["synastry"],
            zodiac_harmony=fx["zodiac_harmony"],
        ),
    ),
    "feng_shui_preview": SitCaseDefinition(
        case_id="feng_shui_preview",
        product_key="feng_shui",
        description="Real feng shui preview through orchestration.",
        surface="preview",
        execute=lambda orchestrator, fx: orchestrator.build_feng_shui_preview_result(
            analysis=fx["analysis"],
            user=fx["user"],
            entitlements=fx["entitlements"],
            product_id=fx["product_id"],
            price_amount=fx["price_amount"],
        ),
    ),
}


def run_cases(case_ids: list[str]) -> dict[str, Any]:
    orchestrator = MysticGenerationOrchestrator()
    results: list[dict[str, Any]] = []

    for case_id in case_ids:
        definition = _CASES[case_id]
        fixture = get_fixture(case_id)
        started = time.perf_counter()
        try:
            orchestration_result = definition.execute(orchestrator, fixture)
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            validation = (
                validate_preview_payload(case_id=case_id, product_key=definition.product_key, payload=orchestration_result.payload)
                if definition.surface == "preview"
                else validate_reading_payload(case_id=case_id, product_key=definition.product_key, payload=orchestration_result.payload)
            )
            results.append(
                {
                    "case_id": case_id,
                    "description": definition.description,
                    "product_key": definition.product_key,
                    "surface": definition.surface,
                    "status": validation.status,
                    "duration_ms": duration_ms,
                    "generation": {
                        "persona_id": orchestration_result.metadata.persona_id,
                        "llm_profile_id": orchestration_result.metadata.llm_profile_id,
                        "prompt_version": orchestration_result.metadata.prompt_version,
                        "model_id": orchestration_result.metadata.model_id,
                        "input_tokens": orchestration_result.input_tokens,
                        "output_tokens": orchestration_result.output_tokens,
                        "cost_usd": orchestration_result.cost_usd,
                    },
                    "validation": validation.as_dict(),
                    "payload_excerpt": _payload_excerpt(orchestration_result.payload),
                }
            )
        except Exception as exc:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            results.append(
                {
                    "case_id": case_id,
                    "description": definition.description,
                    "product_key": definition.product_key,
                    "surface": definition.surface,
                    "status": "failed",
                    "duration_ms": duration_ms,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    summary = {
        "cases_run": len(results),
        "passed": sum(1 for item in results if item["status"] == "passed"),
        "passed_with_warnings": sum(1 for item in results if item["status"] == "passed_with_warnings"),
        "failed": sum(1 for item in results if item["status"] == "failed"),
    }
    status = "failed" if summary["failed"] else "passed_with_warnings" if summary["passed_with_warnings"] else "passed"
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "summary": summary,
        "cases": results,
    }


def _payload_excerpt(payload: dict[str, Any]) -> dict[str, Any]:
    excerpt = {key: payload.get(key) for key in ("flow_type", "product_id", "teaser_text", "analysis_type") if key in payload}
    if isinstance(payload.get("sections"), list):
        excerpt["section_ids"] = [section.get("id") for section in payload["sections"] if isinstance(section, dict)]
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    if metadata.get("flow_type"):
        excerpt["metadata_flow_type"] = metadata.get("flow_type")
    return excerpt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Mystic SIT checks.")
    parser.add_argument("--case", action="append", dest="cases", choices=sorted(_CASES.keys()), help="Case id to run. Repeat for multiple cases.")
    parser.add_argument("--output-dir", default=str(Path(__file__).resolve().parent / "reports"), help="Directory for JSON and markdown reports.")
    parser.add_argument("--api-v3", action="store_true", help="Run the API-level SIT v3 pytest suite under sit/api/.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.api_v3:
        return subprocess.call([sys.executable, "-m", "pytest", "sit/api/test_api_sit_v3.py", "-q"])

    case_ids = args.cases or list(_CASES.keys())
    report = run_cases(case_ids)
    json_path, md_path = write_report_files(report=report, output_dir=args.output_dir)
    print(json.dumps({"status": report["status"], "json_report": str(json_path), "markdown_report": str(md_path)}, indent=2))
    return 1 if report["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
