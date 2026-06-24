from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST_PATH = Path("docs/releases/pilot_v0/manifest.json")
DEFAULT_METHODOLOGY_CALIBRATION_SUMMARY_PATH = Path(
    "audits/methodology_calibration/reports/summary.json"
)
DEFAULT_METHODOLOGY_CALIBRATION_REVIEW_PACKET_PATH = Path(
    "audits/methodology_calibration/reviews/calibration_review_packet.csv"
)
DEFAULT_SUBMISSION_READINESS_JSON_PATH = Path("docs/releases/pilot_v0/submission_readiness.json")
DEFAULT_SUBMISSION_READINESS_MARKDOWN_PATH = Path("docs/releases/pilot_v0/submission_readiness.md")


def load_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object in {path}, got {type(payload).__name__}.")
    return payload


def load_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return [{key: str(value or "") for key, value in row.items()} for row in csv.DictReader(handle)]


def render_markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    body_lines = ["| " + " | ".join(str(value) for value in row) + " |" for row in rows]
    return "\n".join([header_line, separator_line, *body_lines])


def methodology_review_ready(review_rows: list[dict[str, str]]) -> bool:
    if not review_rows:
        return False
    for row in review_rows:
        status = str(row.get("review_status", "")).strip()
        decision = str(row.get("review_decision", "")).strip()
        if status != "complete" or not decision:
            return False
    return True


def build_gate(
    *,
    gate_id: str,
    title: str,
    ready: bool,
    status: str,
    evidence: dict[str, Any],
    blockers: list[str],
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "title": title,
        "ready": ready,
        "status": status,
        "evidence": evidence,
        "blockers": blockers,
    }


def build_submission_readiness_report(
    *,
    manifest: dict[str, Any],
    methodology_calibration_summary: dict[str, Any],
    methodology_review_rows: list[dict[str, str]],
) -> dict[str, Any]:
    task_count = int(manifest.get("task_count", 0))
    runnable_task_count = int(manifest.get("runnable_task_count", 0))
    release_scope_ready = 8 <= task_count <= 12 and runnable_task_count == task_count
    manual_audit = manifest.get("manual_audit", {})
    external_agents = manifest.get("external_agents", {})
    methodology_counts = methodology_calibration_summary.get("counts", {})
    review_complete = methodology_review_ready(methodology_review_rows)

    gates = [
        build_gate(
            gate_id="pilot_release_scope",
            title="Pilot Release Scope",
            ready=release_scope_ready,
            status="ready" if release_scope_ready else "not_ready",
            evidence={
                "task_count": task_count,
                "runnable_task_count": runnable_task_count,
                "target_range": "8-12 runnable pilot tasks",
            },
            blockers=[]
            if release_scope_ready
            else ["Keep the workshop pilot in the 8-12 task range and make every pilot task runnable."],
        ),
        build_gate(
            gate_id="statistical_artifacts",
            title="Statistical Artifacts",
            ready=bool(manifest.get("statistical_artifacts_path")),
            status="ready" if manifest.get("statistical_artifacts_path") else "not_ready",
            evidence={"path": manifest.get("statistical_artifacts_path", "")},
            blockers=[] if manifest.get("statistical_artifacts_path") else ["Build statistical artifacts."],
        ),
        build_gate(
            gate_id="manual_audit_independent_review",
            title="Manual Audit Independent Review",
            ready=bool(manual_audit.get("ready_for_submission_claims", False)),
            status=str(manual_audit.get("reviewer_readiness_status", "unknown")),
            evidence={
                "case_count": manual_audit.get("case_count", 0),
                "independent_completed_reviewer_packet_count": manual_audit.get(
                    "independent_completed_reviewer_packet_count",
                    0,
                ),
                "agreement_status": manual_audit.get("agreement_status", "unknown"),
            },
            blockers=list(manual_audit.get("reviewer_readiness_blocking_items", [])),
        ),
        build_gate(
            gate_id="external_agent_evidence",
            title="External Agent Evidence",
            ready=bool(external_agents.get("ready_for_external_agent_claims", False)),
            status=str(external_agents.get("readiness_status", "unknown")),
            evidence={
                "completed_external_agent_configuration_count": external_agents.get(
                    "completed_external_agent_configuration_count",
                    0,
                ),
                "external_task_coverage_count": external_agents.get("external_task_coverage_count", 0),
                "expected_task_count": external_agents.get("expected_task_count", 0),
            },
            blockers=list(external_agents.get("blocking_items", [])),
        ),
        build_gate(
            gate_id="methodology_calibration_review",
            title="Methodology Calibration Review",
            ready=review_complete,
            status="ready" if review_complete else "not_ready_template_review_packet",
            evidence={
                "review_packet_row_count": len(methodology_review_rows),
                "finding_row_count": methodology_calibration_summary.get("review_packet", {}).get(
                    "finding_row_count",
                    0,
                ),
                "clean_control_row_count": methodology_calibration_summary.get("review_packet", {}).get(
                    "clean_control_row_count",
                    0,
                ),
                "fixture_true_positives": methodology_calibration_summary.get(
                    "fixture_evaluation",
                    {},
                ).get("true_positive_count", 0),
                "scanned_file_count": methodology_counts.get("scanned_file_count", 0),
            },
            blockers=[]
            if review_complete
            else [
                "Complete audits/methodology_calibration/reviews/calibration_review_packet.csv and rebuild the methodology calibration workflow."
            ],
        ),
        build_gate(
            gate_id="release_tag_and_archive",
            title="Release Tag and Archive",
            ready=False,
            status="not_ready_unfrozen",
            evidence={
                "expected_tag": f"v{manifest.get('benchmark_version', '0.1.0')}-pilot",
                "archive_required": True,
            },
            blockers=["Create a release tag and archive the release artifact bundle after the remaining gates pass."],
        ),
    ]
    blocking_items = [
        blocker
        for gate in gates
        if not gate["ready"]
        for blocker in gate["blockers"]
    ]
    ready = all(gate["ready"] for gate in gates)
    return {
        "benchmark_id": manifest["benchmark_id"],
        "benchmark_version": manifest["benchmark_version"],
        "release_stage": manifest["release_stage"],
        "status": "ready_for_workshop_submission" if ready else "not_ready_for_workshop_submission",
        "ready_for_workshop_submission": ready,
        "gate_count": len(gates),
        "ready_gate_count": sum(1 for gate in gates if gate["ready"]),
        "blocking_gate_count": sum(1 for gate in gates if not gate["ready"]),
        "blocking_items": blocking_items,
        "gates": gates,
    }


def render_submission_readiness_markdown(report: dict[str, Any]) -> str:
    gate_rows = [
        [
            gate["gate_id"],
            "yes" if gate["ready"] else "no",
            f"`{gate['status']}`",
            "; ".join(gate["blockers"]) if gate["blockers"] else "-",
        ]
        for gate in report["gates"]
    ]
    lines = [
        "# Submission Readiness",
        "",
        "Release-facing gate for treating the pilot manuscript as workshop-submission ready.",
        "",
        "## Status",
        "",
        render_markdown_table(
            ["Field", "Value"],
            [
                ["Status", f"`{report['status']}`"],
                ["Ready for workshop submission", "yes" if report["ready_for_workshop_submission"] else "no"],
                ["Ready gates", f"{report['ready_gate_count']} / {report['gate_count']}"],
                ["Blocking gates", report["blocking_gate_count"]],
            ],
        ),
        "",
        "## Gates",
        "",
        render_markdown_table(["Gate", "Ready", "Status", "Blockers"], gate_rows),
        "",
        "## Blocking Items",
        "",
    ]
    if report["blocking_items"]:
        lines.extend(f"- {item}" for item in report["blocking_items"])
    else:
        lines.append("- None.")
    return "\n".join(lines) + "\n"


def build_submission_readiness_artifacts(
    *,
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    methodology_calibration_summary_path: str | Path = DEFAULT_METHODOLOGY_CALIBRATION_SUMMARY_PATH,
    methodology_calibration_review_packet_path: str | Path = DEFAULT_METHODOLOGY_CALIBRATION_REVIEW_PACKET_PATH,
    output_json_path: str | Path = DEFAULT_SUBMISSION_READINESS_JSON_PATH,
    output_markdown_path: str | Path = DEFAULT_SUBMISSION_READINESS_MARKDOWN_PATH,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest_payload = manifest or load_json(manifest_path)
    methodology_summary = load_json(methodology_calibration_summary_path)
    review_rows = load_csv_rows(methodology_calibration_review_packet_path)
    report = build_submission_readiness_report(
        manifest=manifest_payload,
        methodology_calibration_summary=methodology_summary,
        methodology_review_rows=review_rows,
    )

    json_path = Path(output_json_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    markdown_path = Path(output_markdown_path)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_submission_readiness_markdown(report), encoding="utf-8")

    return {
        "json_path": json_path,
        "markdown_path": markdown_path,
        "report": report,
    }
