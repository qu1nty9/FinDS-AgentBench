from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_RELEASE_MANIFEST_PATH = Path("docs/releases/pilot_v0/manifest.json")
DEFAULT_SUBMISSION_READINESS_PATH = Path("docs/releases/pilot_v0/submission_readiness.json")
DEFAULT_FORMATTING_CHECK_PATH = Path("papers/workshop_pilot/formatting_check.json")
DEFAULT_PUBLICATION_GATE_JSON_PATH = Path("docs/releases/pilot_v0/publication_gate_manifest.json")
DEFAULT_PUBLICATION_GATE_MARKDOWN_PATH = Path("docs/releases/pilot_v0/publication_gate_manifest.md")

SNAPSHOT_DATE = "2026-06-21"

RELEASE_GATE_TEST_PATHS = (
    "tests/test_curve_10y3mo_and_scoring.py",
    "tests/test_pipelines.py",
    "tests/test_benchmark_manifest.py",
    "tests/test_task_cards.py",
    "tests/test_manual_audit.py",
    "tests/test_external_agents.py",
    "tests/test_pilot_release.py",
    "tests/test_release_archive.py",
    "tests/test_reference_results.py",
    "tests/test_paper_artifacts.py",
    "tests/test_release_reproducibility.py",
    "tests/test_submission_readiness.py",
    "tests/test_manuscript_formatting.py",
    "tests/test_submission_package.py",
    "tests/test_publication_gate.py",
)

REPRODUCIBILITY_SMOKE_COMMAND = (
    "PYTHONPATH=src python scripts/check_pilot_release_reproducibility.py "
    "--work-root tmp/pilot_release_repro_check "
    "--repeat 1 "
    "--market-seed 11 "
    "--event-seed 23 "
    "--treasury-seed 29 "
    "--curve-seed 31 "
    "--curve3mo-seed 33 "
    "--front-end-seed 31 "
    "--usd-seed 37 "
    f"--treasury-snapshot-date {SNAPSHOT_DATE} "
    f"--curve-snapshot-date {SNAPSHOT_DATE} "
    f"--curve3mo-snapshot-date {SNAPSHOT_DATE} "
    f"--front-end-snapshot-date {SNAPSHOT_DATE} "
    f"--usd-snapshot-date {SNAPSHOT_DATE}"
)


@dataclass(frozen=True)
class PublicationGateBuildResult:
    json_path: Path
    markdown_path: Path
    manifest: dict[str, Any]


def load_json_object(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}, got {type(payload).__name__}.")
    return payload


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    body_lines = ["| " + " | ".join(str(value) for value in row) + " |" for row in rows]
    return "\n".join([header_line, separator_line, *body_lines])


def release_gate_pytest_command() -> str:
    return "PYTHONPATH=src python -m pytest " + " ".join(RELEASE_GATE_TEST_PATHS) + " -q"


def build_automated_gates() -> list[dict[str, Any]]:
    temp_archive_build_command = (
        "PYTHONPATH=src python scripts/build_release_archive.py "
        "--output-dir tmp/ci_release_archives "
        "--manifest-json tmp/ci_release_archive_manifest.json "
        "--manifest-markdown tmp/ci_release_archive_manifest.md"
    )
    temp_archive_verify_command = (
        "PYTHONPATH=src python scripts/verify_release_archive.py "
        "--archive-manifest tmp/ci_release_archive_manifest.json"
    )
    return [
        {
            "gate_id": "full_repository_lint",
            "title": "Full Repository Lint",
            "status": "defined_in_ci",
            "ci_job": "release-gate-tests",
            "ci_enforced": True,
            "blocks_publication_if_failing": True,
            "local_command": "python -m ruff check .",
            "ci_command": "python -m ruff check .",
            "artifacts": [],
        },
        {
            "gate_id": "release_gate_regression_suite",
            "title": "Release-Gate Regression Suite",
            "status": "defined_in_ci",
            "ci_job": "release-gate-tests",
            "ci_enforced": True,
            "blocks_publication_if_failing": True,
            "local_command": release_gate_pytest_command(),
            "ci_command": release_gate_pytest_command(),
            "artifacts": [],
        },
        {
            "gate_id": "manuscript_static_formatting",
            "title": "Manuscript Static Formatting",
            "status": "defined_in_ci",
            "ci_job": "release-gate-tests",
            "ci_enforced": True,
            "blocks_publication_if_failing": True,
            "local_command": "PYTHONPATH=src python scripts/check_pilot_manuscript_formatting.py",
            "ci_command": "PYTHONPATH=src python scripts/check_pilot_manuscript_formatting.py",
            "artifacts": [
                "papers/workshop_pilot/formatting_check.json",
                "papers/workshop_pilot/formatting_check.md",
            ],
        },
        {
            "gate_id": "publication_gate_manifest_staleness",
            "title": "Publication Gate Manifest Staleness",
            "status": "defined_in_ci",
            "ci_job": "release-gate-tests",
            "ci_enforced": True,
            "blocks_publication_if_failing": True,
            "local_command": "PYTHONPATH=src python scripts/build_publication_gate_manifest.py --check",
            "ci_command": "PYTHONPATH=src python scripts/build_publication_gate_manifest.py --check",
            "artifacts": [
                "docs/releases/pilot_v0/publication_gate_manifest.json",
                "docs/releases/pilot_v0/publication_gate_manifest.md",
            ],
        },
        {
            "gate_id": "submission_package_manifest_staleness",
            "title": "Submission Package Manifest Staleness",
            "status": "defined_in_ci",
            "ci_job": "release-gate-tests",
            "ci_enforced": True,
            "blocks_publication_if_failing": True,
            "local_command": "PYTHONPATH=src python scripts/build_submission_package_manifest.py --check",
            "ci_command": "PYTHONPATH=src python scripts/build_submission_package_manifest.py --check",
            "artifacts": [
                "papers/workshop_pilot/submission_package_manifest.json",
                "papers/workshop_pilot/submission_package_manifest.md",
            ],
        },
        {
            "gate_id": "release_archive_build_and_verify",
            "title": "Release Archive Build and Verify",
            "status": "defined_in_ci",
            "ci_job": "release-gate-tests",
            "ci_enforced": True,
            "blocks_publication_if_failing": True,
            "local_command": f"{temp_archive_build_command} && {temp_archive_verify_command}",
            "ci_command": f"{temp_archive_build_command} && {temp_archive_verify_command}",
            "artifacts": [
                "tmp/ci_release_archives/finds_agentbench_pilot_v0-0.1.0-pilot.tar.gz",
                "tmp/ci_release_archive_manifest.json",
                "tmp/ci_release_archive_manifest.md",
            ],
        },
        {
            "gate_id": "pilot_release_reproducibility_smoke",
            "title": "Pilot Release Reproducibility Smoke",
            "status": "defined_in_ci",
            "ci_job": "pilot-release-repro-smoke",
            "ci_enforced": True,
            "blocks_publication_if_failing": True,
            "local_command": REPRODUCIBILITY_SMOKE_COMMAND,
            "ci_command": REPRODUCIBILITY_SMOKE_COMMAND.replace(
                "--work-root tmp/pilot_release_repro_check",
                "--work-root tmp/github_actions_release_repro "
                "--forensics-output-dir tmp/github_actions_release_repro/forensics",
            ),
            "artifacts": ["tmp/pilot_release_repro_check"],
        },
    ]


def build_latex_pdf_gate(formatting_check: dict[str, Any]) -> dict[str, Any]:
    ready = bool(formatting_check.get("ready_for_pdf_formatting_claims", False))
    blockers = [] if ready else list(formatting_check.get("next_actions", []))
    if not blockers and not ready:
        blockers = ["Compile the manuscript PDF with a local LaTeX engine and inspect the output."]
    latex_engine = formatting_check.get("latex_engine", {})
    return {
        "gate_id": "latex_pdf_compile_visual_inspection",
        "title": "LaTeX PDF Compile and Visual Inspection",
        "ready": ready,
        "status": "ready" if ready else str(formatting_check.get("status", "pdf_compile_pending")),
        "evidence": {
            "main_tex_path": formatting_check.get("main_tex_path", "papers/workshop_pilot/main.tex"),
            "pdf_compile_status": formatting_check.get("pdf_compile_status", "unknown"),
            "latex_engine_available": bool(latex_engine.get("available", False)),
            "latex_engine": latex_engine.get("engine"),
            "hard_error_count": formatting_check.get("hard_error_count", 0),
            "warning_count": formatting_check.get("warning_count", 0),
            "table_count": formatting_check.get("table_count", 0),
            "mitigated_table_count": formatting_check.get("mitigated_table_count", 0),
        },
        "blockers": blockers,
    }


def build_evidence_gates(
    *,
    submission_readiness: dict[str, Any],
    formatting_check: dict[str, Any],
) -> list[dict[str, Any]]:
    gates = [
        {
            "gate_id": gate["gate_id"],
            "title": gate["title"],
            "ready": bool(gate["ready"]),
            "status": str(gate["status"]),
            "evidence": gate.get("evidence", {}),
            "blockers": list(gate.get("blockers", [])),
        }
        for gate in submission_readiness.get("gates", [])
    ]
    gates.append(build_latex_pdf_gate(formatting_check))
    return gates


def publication_gate_status(*, submission_ready: bool, pdf_ready: bool) -> str:
    if submission_ready and pdf_ready:
        return "ready_for_final_submission_package"
    if not submission_ready and not pdf_ready:
        return "blocked_on_submission_evidence_and_pdf_compile"
    if not submission_ready:
        return "blocked_on_submission_evidence"
    return "blocked_on_pdf_compile"


def build_publication_gate_manifest(
    *,
    release_manifest: dict[str, Any],
    submission_readiness: dict[str, Any],
    formatting_check: dict[str, Any],
) -> dict[str, Any]:
    automated_gates = build_automated_gates()
    evidence_gates = build_evidence_gates(
        submission_readiness=submission_readiness,
        formatting_check=formatting_check,
    )
    blocking_items = [
        blocker
        for gate in evidence_gates
        if not gate["ready"]
        for blocker in gate["blockers"]
    ]
    submission_ready = bool(submission_readiness.get("ready_for_workshop_submission", False))
    pdf_ready = bool(formatting_check.get("ready_for_pdf_formatting_claims", False))
    return {
        "schema_version": 1,
        "benchmark_id": release_manifest["benchmark_id"],
        "benchmark_version": release_manifest["benchmark_version"],
        "release_stage": release_manifest["release_stage"],
        "status": publication_gate_status(submission_ready=submission_ready, pdf_ready=pdf_ready),
        "ready_for_final_submission_package": submission_ready and pdf_ready,
        "source_artifacts": {
            "release_manifest": str(DEFAULT_RELEASE_MANIFEST_PATH),
            "submission_readiness": str(DEFAULT_SUBMISSION_READINESS_PATH),
            "formatting_check": str(DEFAULT_FORMATTING_CHECK_PATH),
            "github_actions_workflow": ".github/workflows/ci.yml",
        },
        "automated_gate_count": len(automated_gates),
        "ci_enforced_automated_gate_count": sum(1 for gate in automated_gates if gate["ci_enforced"]),
        "evidence_gate_count": len(evidence_gates),
        "blocking_evidence_gate_count": sum(1 for gate in evidence_gates if not gate["ready"]),
        "blocking_item_count": len(blocking_items),
        "blocking_items": blocking_items,
        "automated_gates": automated_gates,
        "evidence_gates": evidence_gates,
        "recommended_completion_order": [
            "Run CI-backed automated gates on every publication-facing change.",
            "Complete one independent manual-audit reviewer packet and rebuild agreement reporting.",
            "Register and run at least one non-author external agent configuration.",
            "Compile and inspect the manuscript PDF with a real LaTeX engine.",
            "Rebuild and verify the deterministic release archive.",
            "Freeze the final release tag after all evidence gates pass.",
        ],
    }


def render_publication_gate_markdown(manifest: dict[str, Any]) -> str:
    automated_rows = [
        [
            gate["gate_id"],
            gate["ci_job"],
            "yes" if gate["ci_enforced"] else "no",
            "yes" if gate["blocks_publication_if_failing"] else "no",
        ]
        for gate in manifest["automated_gates"]
    ]
    evidence_rows = [
        [
            gate["gate_id"],
            "yes" if gate["ready"] else "no",
            f"`{gate['status']}`",
            len(gate["blockers"]),
        ]
        for gate in manifest["evidence_gates"]
    ]
    lines = [
        "# Publication Gate Manifest",
        "",
        "Machine-readable gate map for the FinDS-AgentBench pilot submission package.",
        "",
        "## Status",
        "",
        markdown_table(
            ["Field", "Value"],
            [
                ["Benchmark ID", manifest["benchmark_id"]],
                ["Benchmark Version", manifest["benchmark_version"]],
                ["Release Stage", manifest["release_stage"]],
                ["Status", f"`{manifest['status']}`"],
                [
                    "Ready for Final Submission Package",
                    "yes" if manifest["ready_for_final_submission_package"] else "no",
                ],
                ["Automated Gates", manifest["automated_gate_count"]],
                ["CI-Enforced Automated Gates", manifest["ci_enforced_automated_gate_count"]],
                ["Evidence Gates", manifest["evidence_gate_count"]],
                ["Blocking Evidence Gates", manifest["blocking_evidence_gate_count"]],
                ["Blocking Items", manifest["blocking_item_count"]],
            ],
        ),
        "",
        "## Automated Gates",
        "",
        markdown_table(["Gate", "CI Job", "CI Enforced", "Blocks Publication"], automated_rows),
        "",
        "## Evidence Gates",
        "",
        markdown_table(["Gate", "Ready", "Status", "Blockers"], evidence_rows),
        "",
        "## Blocking Items",
        "",
    ]
    if manifest["blocking_items"]:
        lines.extend(f"- {item}" for item in manifest["blocking_items"])
    else:
        lines.append("- None.")
    lines.extend(["", "## Command Catalog", ""])
    for gate in manifest["automated_gates"]:
        lines.extend(
            [
                f"### {gate['gate_id']}",
                "",
                f"- CI job: `{gate['ci_job']}`",
                f"- Status: `{gate['status']}`",
                "",
                "```bash",
                gate["local_command"],
                "```",
                "",
            ]
        )
    lines.extend(["## Recommended Completion Order", ""])
    lines.extend(f"{index}. {item}" for index, item in enumerate(manifest["recommended_completion_order"], start=1))
    return "\n".join(lines) + "\n"


def build_publication_gate_artifacts(
    *,
    release_manifest_path: str | Path = DEFAULT_RELEASE_MANIFEST_PATH,
    submission_readiness_path: str | Path = DEFAULT_SUBMISSION_READINESS_PATH,
    formatting_check_path: str | Path = DEFAULT_FORMATTING_CHECK_PATH,
    output_json_path: str | Path = DEFAULT_PUBLICATION_GATE_JSON_PATH,
    output_markdown_path: str | Path = DEFAULT_PUBLICATION_GATE_MARKDOWN_PATH,
) -> PublicationGateBuildResult:
    release_manifest = load_json_object(release_manifest_path)
    submission_readiness = load_json_object(submission_readiness_path)
    formatting_check = load_json_object(formatting_check_path)
    manifest = build_publication_gate_manifest(
        release_manifest=release_manifest,
        submission_readiness=submission_readiness,
        formatting_check=formatting_check,
    )
    json_path = Path(output_json_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path = Path(output_markdown_path)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_publication_gate_markdown(manifest), encoding="utf-8")
    return PublicationGateBuildResult(
        json_path=json_path,
        markdown_path=markdown_path,
        manifest=manifest,
    )


def expected_publication_gate_artifact_texts(
    *,
    release_manifest_path: str | Path = DEFAULT_RELEASE_MANIFEST_PATH,
    submission_readiness_path: str | Path = DEFAULT_SUBMISSION_READINESS_PATH,
    formatting_check_path: str | Path = DEFAULT_FORMATTING_CHECK_PATH,
) -> tuple[str, str]:
    release_manifest = load_json_object(release_manifest_path)
    submission_readiness = load_json_object(submission_readiness_path)
    formatting_check = load_json_object(formatting_check_path)
    manifest = build_publication_gate_manifest(
        release_manifest=release_manifest,
        submission_readiness=submission_readiness,
        formatting_check=formatting_check,
    )
    return (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        render_publication_gate_markdown(manifest),
    )


def stale_publication_gate_artifacts(
    *,
    release_manifest_path: str | Path = DEFAULT_RELEASE_MANIFEST_PATH,
    submission_readiness_path: str | Path = DEFAULT_SUBMISSION_READINESS_PATH,
    formatting_check_path: str | Path = DEFAULT_FORMATTING_CHECK_PATH,
    output_json_path: str | Path = DEFAULT_PUBLICATION_GATE_JSON_PATH,
    output_markdown_path: str | Path = DEFAULT_PUBLICATION_GATE_MARKDOWN_PATH,
) -> list[Path]:
    expected_json, expected_markdown = expected_publication_gate_artifact_texts(
        release_manifest_path=release_manifest_path,
        submission_readiness_path=submission_readiness_path,
        formatting_check_path=formatting_check_path,
    )
    checks = [
        (Path(output_json_path), expected_json),
        (Path(output_markdown_path), expected_markdown),
    ]
    stale_paths: list[Path] = []
    for path, expected_text in checks:
        if not path.exists() or path.read_text(encoding="utf-8") != expected_text:
            stale_paths.append(path)
    return stale_paths
