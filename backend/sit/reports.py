from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_report_files(*, report: dict[str, Any], output_dir: str | Path) -> tuple[Path, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = output_path / f"mystic-sit-report-{timestamp}.json"
    md_path = output_path / f"mystic-sit-report-{timestamp}.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(_render_markdown(report, json_path.name), encoding="utf-8")
    return json_path, md_path



def _render_markdown(report: dict[str, Any], json_name: str) -> str:
    lines = [
        "# Mystic SIT v2 Report",
        "",
        f"- Generated at: `{report.get('generated_at')}`",
        f"- Overall status: **{report.get('status')}**",
        f"- Cases run: `{report.get('summary', {}).get('cases_run', 0)}`",
        f"- Passed: `{report.get('summary', {}).get('passed', 0)}`",
        f"- Passed with warnings: `{report.get('summary', {}).get('passed_with_warnings', 0)}`",
        f"- Failed: `{report.get('summary', {}).get('failed', 0)}`",
        f"- JSON report: `{json_name}`",
        "",
    ]
    for case in report.get("cases", []):
        lines.extend([
            f"## {case.get('case_id')}",
            "",
            f"- Status: **{case.get('status')}**",
            f"- Product: `{case.get('product_key')}`",
            f"- Surface: `{case.get('surface')}`",
            f"- Duration: `{case.get('duration_ms')} ms`",
        ])
        generation = case.get("generation") or {}
        if generation:
            lines.extend([
                f"- Model: `{generation.get('model_id')}`",
                f"- Persona: `{generation.get('persona_id')}`",
                f"- Input tokens: `{generation.get('input_tokens')}`",
                f"- Output tokens: `{generation.get('output_tokens')}`",
                f"- Cost USD: `{generation.get('cost_usd')}`",
            ])
        validation = case.get("validation") or {}
        if validation.get("checks"):
            lines.append("- Checks:")
            lines.extend(f"  - {item}" for item in validation["checks"])
        if validation.get("warnings"):
            lines.append("- Warnings:")
            lines.extend(f"  - {item}" for item in validation["warnings"])
        if validation.get("hard_failures"):
            lines.append("- Hard failures:")
            lines.extend(f"  - {item}" for item in validation["hard_failures"])
        if case.get("error"):
            lines.append(f"- Error: `{case['error']}`")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
