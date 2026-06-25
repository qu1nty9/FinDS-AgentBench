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
DEFAULT_SUBMISSION_EVIDENCE_LEDGER_JSON_PATH = Path(
    "docs/releases/pilot_v0/submission_evidence_ledger.json"
)
DEFAULT_SUBMISSION_EVIDENCE_LEDGER_MARKDOWN_PATH = Path(
    "docs/releases/pilot_v0/submission_evidence_ledger.md"
)


GATE_CLAIM_POLICIES: dict[str, dict[str, str]] = {
    "pilot_release_scope": {
        "allowed_when_ready": "The pilot release is within the planned 8-12 runnable-task workshop scope.",
        "allowed_while_blocked": "The pilot release scope gate has a machine-readable status report.",
        "disallowed_when_blocked": "The public pilot task suite is complete and runnable for workshop release.",
    },
    "statistical_artifacts": {
        "allowed_when_ready": "Pilot uncertainty and paired-comparison statistical artifacts are generated.",
        "allowed_while_blocked": "The statistical-artifact gate has a machine-readable status report.",
        "disallowed_when_blocked": "Pilot result claims are backed by generated uncertainty artifacts.",
    },
    "manual_audit_independent_review": {
        "allowed_when_ready": "The manual-audit subset has completed independent-review evidence and official agreement reporting.",
        "allowed_while_blocked": "Manual-audit rubric, seed review, reviewer handoff, blank reviewer packet, and dry-run plumbing are available.",
        "disallowed_when_blocked": "Independent manual-audit agreement or submission-strength second-reviewer evidence.",
    },
    "external_agent_evidence": {
        "allowed_when_ready": "At least one non-author external-agent configuration has completed the registered pilot evidence protocol.",
        "allowed_while_blocked": "External-agent registration, handoff, and readiness gates are available.",
        "disallowed_when_blocked": "Independent external-agent performance evidence.",
    },
    "methodology_calibration_review": {
        "allowed_when_ready": "Methodology-calibration findings have a completed author review packet.",
        "allowed_while_blocked": "Methodology-calibration fixtures and review-packet workflow are available.",
        "disallowed_when_blocked": "Methodology-calibration findings have completed review adjudication.",
    },
    "release_tag_and_archive": {
        "allowed_when_ready": "The release archive is ready to tag under the expected release tag.",
        "allowed_while_blocked": "A deterministic candidate archive and archive manifest can be built before final tagging.",
        "disallowed_when_blocked": "A frozen tagged release archive exists.",
    },
}


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
        review_type = str(row.get("review_type", "")).strip()
        status = str(row.get("review_status", "")).strip()
        decision = str(row.get("review_decision", "")).strip()
        if review_type == "finding_review":
            valid_decisions = {"true_positive", "false_positive"}
        elif review_type == "clean_control_review":
            valid_decisions = {"true_negative", "false_negative"}
        else:
            valid_decisions = set()
        if status != "complete" or decision not in valid_decisions:
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


def artifact_entry(role: str, path: Any, *, note: str = "") -> dict[str, str]:
    entry = {
        "role": role,
        "path": Path(str(path)).as_posix(),
    }
    if note:
        entry["note"] = note
    return entry


def dedupe_artifact_entries(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for entry in entries:
        path = str(entry.get("path", "")).strip()
        role = str(entry.get("role", "")).strip()
        if not path or not role:
            continue
        key = (role, path)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(entry)
    return deduped


def evidence_artifacts_for_gate(gate_id: str, manifest: dict[str, Any]) -> list[dict[str, str]]:
    manual_audit = manifest.get("manual_audit", {})
    external_agents = manifest.get("external_agents", {})
    artifacts: dict[str, list[dict[str, str]]] = {
        "pilot_release_scope": [
            artifact_entry("release_manifest", "docs/releases/pilot_v0/manifest.json"),
            artifact_entry("release_readme", "docs/releases/pilot_v0/README.md"),
            artifact_entry("task_registry_json", "docs/cards/task_registry.json"),
            artifact_entry("task_registry_csv", "docs/cards/task_registry.csv"),
            artifact_entry("task_cards_index", manifest.get("cards_root", "docs/cards")),
            artifact_entry(
                "data_manifests_index",
                manifest.get("data_manifests_root", "docs/data_manifests/pilot_v0"),
            ),
        ],
        "statistical_artifacts": [
            artifact_entry(
                "statistical_artifacts_index",
                manifest.get("statistical_artifacts_path", "docs/releases/pilot_v0/statistical_artifacts/README.md"),
            ),
            artifact_entry(
                "summary_uncertainty",
                "docs/releases/pilot_v0/statistical_artifacts/summary_uncertainty.md",
            ),
            artifact_entry(
                "agent_vs_best_baseline",
                "docs/releases/pilot_v0/statistical_artifacts/agent_vs_best_baseline.md",
            ),
            artifact_entry(
                "statistical_methods",
                "docs/releases/pilot_v0/statistical_artifacts/methods/statistical_methods.md",
            ),
        ],
        "manual_audit_independent_review": [
            artifact_entry("manual_audit_readme", manual_audit.get("readme_path", "audits/pilot_v0/README.md")),
            artifact_entry("rubric", manual_audit.get("rubric_path", "audits/pilot_v0/manual_audit_rubric.yaml")),
            artifact_entry("seed_subset", manual_audit.get("subset_path", "audits/pilot_v0/adjudicated_subset.json")),
            artifact_entry("reviews_workflow", manual_audit.get("reviews_readme_path", "")),
            artifact_entry("reviewer_readiness", manual_audit.get("reviewer_readiness_markdown_path", "")),
            artifact_entry("agreement_report", manual_audit.get("agreement_report_markdown_path", "")),
            artifact_entry("adjudication_queue", manual_audit.get("adjudication_report_markdown_path", "")),
            artifact_entry("independent_handoff", manual_audit.get("independent_reviewer_handoff_path", "")),
            artifact_entry(
                "independent_packet_manifest",
                manual_audit.get("independent_reviewer_packet_manifest_markdown_path", ""),
            ),
            artifact_entry(
                "independent_packet_validation",
                manual_audit.get("independent_reviewer_packet_validation_markdown_path", ""),
            ),
        ],
        "external_agent_evidence": [
            artifact_entry("external_agent_registry", external_agents.get("registry_path", "")),
            artifact_entry("external_agent_handoff", external_agents.get("handoff_markdown_path", "")),
            artifact_entry("external_agent_intake_manifest", external_agents.get("intake_manifest_markdown_path", "")),
            artifact_entry("external_agent_protocol", external_agents.get("protocol_markdown_path", "")),
            artifact_entry("external_agent_readiness", external_agents.get("readiness_markdown_path", "")),
            artifact_entry(
                "external_agent_registration_validation",
                external_agents.get("registration_validation_markdown_path", ""),
            ),
        ],
        "methodology_calibration_review": [
            artifact_entry("methodology_calibration_readme", "audits/methodology_calibration/README.md"),
            artifact_entry("methodology_calibration_corpus", "audits/methodology_calibration/corpus.yaml"),
            artifact_entry("methodology_calibration_summary", str(DEFAULT_METHODOLOGY_CALIBRATION_SUMMARY_PATH)),
            artifact_entry(
                "methodology_calibration_review_packet",
                str(DEFAULT_METHODOLOGY_CALIBRATION_REVIEW_PACKET_PATH),
            ),
        ],
        "release_tag_and_archive": [
            artifact_entry("release_archive", manifest.get("release_archive_path", "")),
            artifact_entry("release_archive_manifest_json", manifest.get("release_archive_manifest_json_path", "")),
            artifact_entry(
                "release_archive_manifest_markdown",
                manifest.get("release_archive_manifest_markdown_path", ""),
            ),
        ],
    }
    return dedupe_artifact_entries(artifacts.get(gate_id, []))


def verification_commands_for_gate(gate_id: str) -> list[str]:
    commands = {
        "pilot_release_scope": [
            "PYTHONPATH=src python scripts/build_task_cards.py",
            "PYTHONPATH=src python scripts/build_data_manifests.py",
            "PYTHONPATH=src python scripts/build_benchmark_manifest.py",
        ],
        "statistical_artifacts": [
            "PYTHONPATH=src python scripts/build_pilot_statistical_artifacts.py",
        ],
        "manual_audit_independent_review": [
            "PYTHONPATH=src python scripts/build_manual_audit_workflow.py",
            "PYTHONPATH=src python scripts/validate_manual_audit_review_packet.py --packet audits/pilot_v0/reviews/reviewer_2_completed.csv",
        ],
        "external_agent_evidence": [
            "PYTHONPATH=src python scripts/validate_external_agent_registry.py",
            "PYTHONPATH=src python scripts/build_external_agent_readiness.py",
        ],
        "methodology_calibration_review": [
            "PYTHONPATH=src python scripts/build_methodology_calibration_workflow.py",
        ],
        "release_tag_and_archive": [
            "PYTHONPATH=src python scripts/build_release_archive.py",
            "PYTHONPATH=src python scripts/check_pilot_release_reproducibility.py --repeat 1 --treasury-snapshot-date 2026-06-21 --curve-snapshot-date 2026-06-21 --curve3mo-snapshot-date 2026-06-21 --front-end-snapshot-date 2026-06-21 --usd-snapshot-date 2026-06-21",
        ],
    }
    return commands.get(gate_id, [])


def build_submission_evidence_ledger(
    *,
    report: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    gate_entries: list[dict[str, Any]] = []
    for gate in report["gates"]:
        gate_id = gate["gate_id"]
        policy = GATE_CLAIM_POLICIES.get(
            gate_id,
            {
                "allowed_when_ready": f"{gate_id} is ready.",
                "allowed_while_blocked": f"{gate_id} has a machine-readable status report.",
                "disallowed_when_blocked": f"{gate_id} is ready.",
            },
        )
        ready = bool(gate["ready"])
        gate_entries.append(
            {
                "gate_id": gate_id,
                "title": gate["title"],
                "ready": ready,
                "status": gate["status"],
                "claim_status": "claim_allowed" if ready else "claim_blocked",
                "current_allowed_claim": (
                    policy["allowed_when_ready"] if ready else policy["allowed_while_blocked"]
                ),
                "current_disallowed_claim": None if ready else policy["disallowed_when_blocked"],
                "evidence": gate["evidence"],
                "evidence_artifacts": evidence_artifacts_for_gate(gate_id, manifest),
                "verification_commands": verification_commands_for_gate(gate_id),
                "blockers": gate["blockers"],
            }
        )

    return {
        "benchmark_id": report["benchmark_id"],
        "benchmark_version": report["benchmark_version"],
        "release_stage": report["release_stage"],
        "status": (
            "submission_evidence_ready"
            if report["ready_for_workshop_submission"]
            else "submission_evidence_incomplete"
        ),
        "submission_readiness_status": report["status"],
        "ready_for_workshop_submission": report["ready_for_workshop_submission"],
        "gate_count": report["gate_count"],
        "ready_gate_count": report["ready_gate_count"],
        "blocking_gate_count": report["blocking_gate_count"],
        "current_allowed_claims": [entry["current_allowed_claim"] for entry in gate_entries],
        "current_disallowed_claims": [
            entry["current_disallowed_claim"]
            for entry in gate_entries
            if entry["current_disallowed_claim"]
        ],
        "gates": gate_entries,
    }


def render_submission_evidence_ledger_markdown(ledger: dict[str, Any]) -> str:
    gate_rows = [
        [
            gate["gate_id"],
            "yes" if gate["ready"] else "no",
            f"`{gate['status']}`",
            f"`{gate['claim_status']}`",
            len(gate["evidence_artifacts"]),
            len(gate["verification_commands"]),
        ]
        for gate in ledger["gates"]
    ]
    lines = [
        "# Submission Evidence Ledger",
        "",
        "Machine-readable claim boundary and evidence index for the workshop submission gates.",
        "",
        "## Status",
        "",
        render_markdown_table(
            ["Field", "Value"],
            [
                ["Ledger status", f"`{ledger['status']}`"],
                ["Submission readiness", f"`{ledger['submission_readiness_status']}`"],
                ["Ready for workshop submission", "yes" if ledger["ready_for_workshop_submission"] else "no"],
                ["Ready gates", f"{ledger['ready_gate_count']} / {ledger['gate_count']}"],
                ["Blocking gates", ledger["blocking_gate_count"]],
            ],
        ),
        "",
        "## Allowed Current Claims",
        "",
    ]
    lines.extend(f"- {claim}" for claim in ledger["current_allowed_claims"])
    lines.extend(["", "## Disallowed Current Claims", ""])
    if ledger["current_disallowed_claims"]:
        lines.extend(f"- {claim}" for claim in ledger["current_disallowed_claims"])
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Gate Summary",
            "",
            render_markdown_table(
                ["Gate", "Ready", "Status", "Claim Status", "Evidence Artifacts", "Verification Commands"],
                gate_rows,
            ),
            "",
            "## Gate Evidence",
            "",
        ]
    )
    for gate in ledger["gates"]:
        lines.extend(
            [
                f"### {gate['gate_id']}",
                "",
                f"- Current allowed claim: {gate['current_allowed_claim']}",
            ]
        )
        if gate["current_disallowed_claim"]:
            lines.append(f"- Current disallowed claim: {gate['current_disallowed_claim']}")
        if gate["blockers"]:
            lines.append("- Blockers:")
            lines.extend(f"  - {blocker}" for blocker in gate["blockers"])
        else:
            lines.append("- Blockers: none")
        lines.append("- Evidence artifacts:")
        lines.extend(
            f"  - `{entry['path']}` ({entry['role']})"
            for entry in gate["evidence_artifacts"]
        )
        lines.append("- Verification commands:")
        lines.extend(f"  - `{command}`" for command in gate["verification_commands"])
        lines.append("")
    return "\n".join(lines) + "\n"


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
    evidence_ledger_json_path: str | Path = DEFAULT_SUBMISSION_EVIDENCE_LEDGER_JSON_PATH,
    evidence_ledger_markdown_path: str | Path = DEFAULT_SUBMISSION_EVIDENCE_LEDGER_MARKDOWN_PATH,
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

    evidence_ledger = build_submission_evidence_ledger(
        report=report,
        manifest=manifest_payload,
    )
    ledger_json_path = Path(evidence_ledger_json_path)
    ledger_json_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_json_path.write_text(
        json.dumps(evidence_ledger, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    ledger_markdown_path = Path(evidence_ledger_markdown_path)
    ledger_markdown_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_markdown_path.write_text(
        render_submission_evidence_ledger_markdown(evidence_ledger),
        encoding="utf-8",
    )

    return {
        "json_path": json_path,
        "markdown_path": markdown_path,
        "report": report,
        "evidence_ledger_json_path": ledger_json_path,
        "evidence_ledger_markdown_path": ledger_markdown_path,
        "evidence_ledger": evidence_ledger,
    }
