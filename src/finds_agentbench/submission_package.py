from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from finds_agentbench.runs import file_sha256


DEFAULT_RELEASE_MANIFEST_PATH = Path("docs/releases/pilot_v0/manifest.json")
DEFAULT_ARCHIVE_MANIFEST_PATH = Path("docs/releases/pilot_v0/archive_manifest.json")
DEFAULT_SUBMISSION_READINESS_PATH = Path("docs/releases/pilot_v0/submission_readiness.json")
DEFAULT_EVIDENCE_LEDGER_PATH = Path("docs/releases/pilot_v0/submission_evidence_ledger.json")
DEFAULT_PUBLICATION_GATE_PATH = Path("docs/releases/pilot_v0/publication_gate_manifest.json")
DEFAULT_FORMATTING_CHECK_PATH = Path("papers/workshop_pilot/formatting_check.json")
DEFAULT_SUBMISSION_PACKAGE_JSON_PATH = Path("papers/workshop_pilot/submission_package_manifest.json")
DEFAULT_SUBMISSION_PACKAGE_MARKDOWN_PATH = Path("papers/workshop_pilot/submission_package_manifest.md")
DEFAULT_COMPILED_MANUSCRIPT_PDF_PATH = Path("papers/workshop_pilot/main.pdf")


@dataclass(frozen=True)
class SubmissionPackageBuildResult:
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


def artifact_entry(
    *,
    group: str,
    role: str,
    path: str | Path,
    required_for_workshop_submission: bool = True,
    note: str = "",
) -> dict[str, Any]:
    artifact_path = Path(path)
    entry: dict[str, Any] = {
        "group": group,
        "role": role,
        "path": artifact_path.as_posix(),
        "required_for_workshop_submission": required_for_workshop_submission,
        "materialization": "workspace_path",
        "exists": artifact_path.exists(),
    }
    if note:
        entry["note"] = note
    if artifact_path.is_file():
        entry.update(
            {
                "kind": "file",
                "size_bytes": artifact_path.stat().st_size,
                "sha256": file_sha256(artifact_path),
            }
        )
    elif artifact_path.is_dir():
        entry.update({"kind": "directory", "size_bytes": None, "sha256": None})
    else:
        entry.update({"kind": "missing", "size_bytes": None, "sha256": None})
    return entry


def archive_artifact_entry(*, archive_manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "group": "release_candidate",
        "role": "release_archive",
        "path": archive_manifest["archive_path"],
        "required_for_workshop_submission": True,
        "materialization": "declared_by_archive_manifest",
        "kind": "file",
        "exists": None,
        "size_bytes": archive_manifest.get("archive_size_bytes"),
        "sha256": archive_manifest.get("archive_sha256"),
        "note": "Archive file metadata is declared by docs/releases/pilot_v0/archive_manifest.json.",
    }


def dedupe_artifacts(artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for artifact in artifacts:
        key = (
            str(artifact.get("group", "")),
            str(artifact.get("role", "")),
            str(artifact.get("path", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(artifact)
    return deduped


def evidence_artifacts_from_ledger(evidence_ledger: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for gate in evidence_ledger.get("gates", []):
        gate_id = str(gate.get("gate_id", "unknown_gate"))
        for evidence in gate.get("evidence_artifacts", []):
            path = str(evidence.get("path", "")).strip()
            role = str(evidence.get("role", "")).strip()
            if not path or path.startswith("dist/release_archives/"):
                continue
            artifacts.append(
                artifact_entry(
                    group=f"evidence:{gate_id}",
                    role=role or "evidence_artifact",
                    path=path,
                    required_for_workshop_submission=not bool(gate.get("ready", False)),
                )
            )
    return artifacts


def build_core_artifacts(
    *,
    archive_manifest: dict[str, Any],
    release_manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    release_archive_entry = archive_artifact_entry(archive_manifest=archive_manifest)
    paths = [
        ("manuscript", "main_tex", "papers/workshop_pilot/main.tex"),
        ("manuscript", "related_work_tex", "papers/workshop_pilot/related_work.tex"),
        ("manuscript", "references_bib", "papers/workshop_pilot/references.bib"),
        ("manuscript", "metadata", "papers/workshop_pilot/metadata.json"),
        ("manuscript", "audit_failure_examples_tex", "papers/workshop_pilot/audit_failure_examples.tex"),
        ("manuscript", "audit_failure_examples_md", "papers/workshop_pilot/audit_failure_examples.md"),
        ("manuscript", "formatting_check_json", "papers/workshop_pilot/formatting_check.json"),
        ("manuscript", "formatting_check_md", "papers/workshop_pilot/formatting_check.md"),
        (
            "manuscript",
            "submission_readiness_checklist",
            "papers/workshop_pilot/submission_readiness_checklist.md",
        ),
        (
            "manuscript",
            "compiled_pdf",
            DEFAULT_COMPILED_MANUSCRIPT_PDF_PATH,
        ),
        ("paper_inputs", "reference_results", "docs/releases/pilot_v0/reference_results.md"),
        ("paper_inputs", "paper_artifacts_index", "docs/releases/pilot_v0/paper_artifacts/README.md"),
        (
            "paper_inputs",
            "statistical_artifacts_index",
            "docs/releases/pilot_v0/statistical_artifacts/README.md",
        ),
        (
            "paper_inputs",
            "agent_vs_baseline_table",
            "docs/releases/pilot_v0/statistical_artifacts/tables/agent_vs_best_baseline_overall_score.tex",
        ),
        (
            "paper_inputs",
            "uncertainty_table",
            "docs/releases/pilot_v0/statistical_artifacts/tables/summary_uncertainty_overall_score.tex",
        ),
        ("release_candidate", "release_manifest", DEFAULT_RELEASE_MANIFEST_PATH),
        ("release_candidate", "release_readme", "docs/releases/pilot_v0/README.md"),
        ("release_candidate", "archive_manifest_json", DEFAULT_ARCHIVE_MANIFEST_PATH),
        ("release_candidate", "archive_manifest_md", "docs/releases/pilot_v0/archive_manifest.md"),
        ("release_candidate", "publication_gate_json", DEFAULT_PUBLICATION_GATE_PATH),
        (
            "release_candidate",
            "publication_gate_md",
            "docs/releases/pilot_v0/publication_gate_manifest.md",
        ),
        ("release_candidate", "submission_readiness_json", DEFAULT_SUBMISSION_READINESS_PATH),
        ("release_candidate", "submission_readiness_md", "docs/releases/pilot_v0/submission_readiness.md"),
        ("release_candidate", "evidence_ledger_json", DEFAULT_EVIDENCE_LEDGER_PATH),
        ("release_candidate", "evidence_ledger_md", "docs/releases/pilot_v0/submission_evidence_ledger.md"),
        ("ci", "github_actions_workflow", ".github/workflows/ci.yml"),
        ("package_control", "submission_package_script", "scripts/build_submission_package_manifest.py"),
        ("package_control", "submission_package_module", "src/finds_agentbench/submission_package.py"),
        ("package_control", "publication_gate_script", "scripts/build_publication_gate_manifest.py"),
        ("package_control", "publication_gate_module", "src/finds_agentbench/publication_gate.py"),
    ]
    artifacts = [
        artifact_entry(
            group=group,
            role=role,
            path=path,
            required_for_workshop_submission=role != "compiled_pdf",
        )
        for group, role, path in paths
    ]
    compiled_pdf = next(artifact for artifact in artifacts if artifact["role"] == "compiled_pdf")
    compiled_pdf["required_for_workshop_submission"] = True
    compiled_pdf["note"] = "Required only for the final venue upload, not for source-only review."
    artifacts.append(release_archive_entry)

    package_json = release_manifest.get("workshop_submission_package_json_path")
    package_markdown = release_manifest.get("workshop_submission_package_markdown_path")
    if package_json:
        artifacts.append(
            {
                "group": "submission_package",
                "role": "submission_package_json",
                "path": package_json,
                "required_for_workshop_submission": True,
                "materialization": "generated_by_this_command",
                "kind": "file",
                "exists": None,
                "size_bytes": None,
                "sha256": None,
            }
        )
    if package_markdown:
        artifacts.append(
            {
                "group": "submission_package",
                "role": "submission_package_markdown",
                "path": package_markdown,
                "required_for_workshop_submission": True,
                "materialization": "generated_by_this_command",
                "kind": "file",
                "exists": None,
                "size_bytes": None,
                "sha256": None,
            }
        )
    return artifacts


def package_status(*, publication_gate: dict[str, Any], missing_required_artifact_count: int) -> str:
    if publication_gate.get("ready_for_final_submission_package") and missing_required_artifact_count == 0:
        return "ready_for_workshop_submission_package"
    if missing_required_artifact_count:
        return "candidate_blocked_on_missing_artifacts_and_evidence"
    return "candidate_blocked_on_evidence_gates"


def build_stage_targets(
    *,
    package_ready: bool,
    publication_gate: dict[str, Any],
) -> list[dict[str, Any]]:
    blockers = list(publication_gate.get("blocking_items", []))
    return [
        {
            "target_id": "arxiv_workshop",
            "status": "ready" if package_ready else "not_ready_blocked_by_current_gates",
            "required_before_submission": blockers,
            "scope": "Pilot manuscript plus deterministic public benchmark release candidate.",
        },
        {
            "target_id": "top_benchmark_dataset_venue",
            "status": "not_ready_requires_scale_and_external_validation",
            "required_before_submission": [
                "Expand from pilot scale to a larger audited task suite.",
                "Add hidden or private temporal holdout governance.",
                "Collect independent external-agent results across representative agent families.",
                "Add broader reproducibility evidence from non-author machines.",
            ],
            "scope": "Dataset/benchmark paper with public harness, stronger agent coverage, and governance.",
        },
        {
            "target_id": "journal_extension",
            "status": "not_ready_requires_longitudinal_reliability_study",
            "required_before_submission": [
                "Run larger repeated-run experiments across agents, tasks, seeds, and regimes.",
                "Study leakage, validation, reproducibility, and decision-quality failure modes jointly.",
                "Add model-risk and governance analysis beyond pilot benchmark reporting.",
                "Complete independent review and external reproducibility evidence.",
            ],
            "scope": "Methodological extension focused on reliability and model-risk implications.",
        },
    ]


def build_submission_package_manifest(
    *,
    release_manifest: dict[str, Any],
    archive_manifest: dict[str, Any],
    submission_readiness: dict[str, Any],
    evidence_ledger: dict[str, Any],
    publication_gate: dict[str, Any],
    formatting_check: dict[str, Any],
) -> dict[str, Any]:
    artifacts = dedupe_artifacts(
        [
            *build_core_artifacts(
                archive_manifest=archive_manifest,
                release_manifest=release_manifest,
            ),
            *evidence_artifacts_from_ledger(evidence_ledger),
        ]
    )
    missing_required_artifacts = [
        artifact
        for artifact in artifacts
        if artifact.get("required_for_workshop_submission") and artifact.get("exists") is False
    ]
    package_ready = (
        bool(publication_gate.get("ready_for_final_submission_package", False))
        and not missing_required_artifacts
    )
    verification_commands = list(
        dict.fromkeys(
            [
                gate["local_command"]
                for gate in publication_gate.get("automated_gates", [])
                if gate.get("blocks_publication_if_failing")
            ]
            + ["PYTHONPATH=src python scripts/build_submission_package_manifest.py --check"]
        )
    )
    return {
        "schema_version": 1,
        "benchmark_id": release_manifest["benchmark_id"],
        "benchmark_version": release_manifest["benchmark_version"],
        "release_stage": release_manifest["release_stage"],
        "status": package_status(
            publication_gate=publication_gate,
            missing_required_artifact_count=len(missing_required_artifacts),
        ),
        "ready_for_workshop_submission_package": package_ready,
        "source_artifacts": {
            "release_manifest": str(DEFAULT_RELEASE_MANIFEST_PATH),
            "archive_manifest": str(DEFAULT_ARCHIVE_MANIFEST_PATH),
            "submission_readiness": str(DEFAULT_SUBMISSION_READINESS_PATH),
            "evidence_ledger": str(DEFAULT_EVIDENCE_LEDGER_PATH),
            "publication_gate": str(DEFAULT_PUBLICATION_GATE_PATH),
            "formatting_check": str(DEFAULT_FORMATTING_CHECK_PATH),
        },
        "publication_gate_status": publication_gate.get("status", "unknown"),
        "submission_readiness_status": submission_readiness.get("status", "unknown"),
        "formatting_status": formatting_check.get("status", "unknown"),
        "archive_status": archive_manifest.get("archive_status", "unknown"),
        "archive_sha256": archive_manifest.get("archive_sha256", ""),
        "allowed_current_claims": list(evidence_ledger.get("current_allowed_claims", [])),
        "disallowed_current_claims": list(evidence_ledger.get("current_disallowed_claims", [])),
        "blocking_items": list(publication_gate.get("blocking_items", [])),
        "artifact_count": len(artifacts),
        "missing_required_artifact_count": len(missing_required_artifacts),
        "missing_required_artifacts": [
            {"group": artifact["group"], "role": artifact["role"], "path": artifact["path"]}
            for artifact in missing_required_artifacts
        ],
        "artifacts": artifacts,
        "stage_targets": build_stage_targets(
            package_ready=package_ready,
            publication_gate=publication_gate,
        ),
        "pre_submission_verification_commands": verification_commands,
    }


def render_submission_package_markdown(manifest: dict[str, Any]) -> str:
    artifact_rows = [
        [
            artifact["group"],
            artifact["role"],
            artifact["path"],
            artifact["kind"],
            "yes"
            if artifact["exists"] is True
            else "no"
            if artifact["exists"] is False
            else "declared",
        ]
        for artifact in manifest["artifacts"]
    ]
    stage_rows = [
        [target["target_id"], f"`{target['status']}`", target["scope"]]
        for target in manifest["stage_targets"]
    ]
    lines = [
        "# Workshop Submission Package Manifest",
        "",
        "Submission-level wrapper around the manuscript source, release candidate, evidence ledger, "
        "publication gate, and archive checksum manifest.",
        "",
        "## Status",
        "",
        markdown_table(
            ["Field", "Value"],
            [
                ["Benchmark ID", manifest["benchmark_id"]],
                ["Benchmark Version", manifest["benchmark_version"]],
                ["Release Stage", manifest["release_stage"]],
                ["Package Status", f"`{manifest['status']}`"],
                [
                    "Ready for Workshop Submission Package",
                    "yes" if manifest["ready_for_workshop_submission_package"] else "no",
                ],
                ["Publication Gate", f"`{manifest['publication_gate_status']}`"],
                ["Submission Readiness", f"`{manifest['submission_readiness_status']}`"],
                ["Formatting Status", f"`{manifest['formatting_status']}`"],
                ["Archive Status", f"`{manifest['archive_status']}`"],
                ["Archive SHA256", f"`{manifest['archive_sha256']}`"],
                ["Artifacts", manifest["artifact_count"]],
                ["Missing Required Artifacts", manifest["missing_required_artifact_count"]],
            ],
        ),
        "",
        "## Stage Targets",
        "",
        markdown_table(["Target", "Status", "Scope"], stage_rows),
        "",
        "## Blocking Items",
        "",
    ]
    if manifest["blocking_items"]:
        lines.extend(f"- {item}" for item in manifest["blocking_items"])
    else:
        lines.append("- None.")
    lines.extend(["", "## Missing Required Artifacts", ""])
    if manifest["missing_required_artifacts"]:
        lines.extend(
            f"- `{artifact['path']}` ({artifact['group']} / {artifact['role']})"
            for artifact in manifest["missing_required_artifacts"]
        )
    else:
        lines.append("- None.")
    lines.extend(["", "## Allowed Current Claims", ""])
    lines.extend(f"- {claim}" for claim in manifest["allowed_current_claims"])
    lines.extend(["", "## Disallowed Current Claims", ""])
    if manifest["disallowed_current_claims"]:
        lines.extend(f"- {claim}" for claim in manifest["disallowed_current_claims"])
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Artifact Inventory",
            "",
            markdown_table(["Group", "Role", "Path", "Kind", "Exists"], artifact_rows),
            "",
            "## Pre-Submission Verification Commands",
            "",
        ]
    )
    for command in manifest["pre_submission_verification_commands"]:
        lines.extend(["```bash", command, "```", ""])
    return "\n".join(lines).rstrip() + "\n"


def build_submission_package_artifacts(
    *,
    release_manifest_path: str | Path = DEFAULT_RELEASE_MANIFEST_PATH,
    archive_manifest_path: str | Path = DEFAULT_ARCHIVE_MANIFEST_PATH,
    submission_readiness_path: str | Path = DEFAULT_SUBMISSION_READINESS_PATH,
    evidence_ledger_path: str | Path = DEFAULT_EVIDENCE_LEDGER_PATH,
    publication_gate_path: str | Path = DEFAULT_PUBLICATION_GATE_PATH,
    formatting_check_path: str | Path = DEFAULT_FORMATTING_CHECK_PATH,
    output_json_path: str | Path = DEFAULT_SUBMISSION_PACKAGE_JSON_PATH,
    output_markdown_path: str | Path = DEFAULT_SUBMISSION_PACKAGE_MARKDOWN_PATH,
) -> SubmissionPackageBuildResult:
    manifest = build_submission_package_manifest(
        release_manifest=load_json_object(release_manifest_path),
        archive_manifest=load_json_object(archive_manifest_path),
        submission_readiness=load_json_object(submission_readiness_path),
        evidence_ledger=load_json_object(evidence_ledger_path),
        publication_gate=load_json_object(publication_gate_path),
        formatting_check=load_json_object(formatting_check_path),
    )
    json_path = Path(output_json_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path = Path(output_markdown_path)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_submission_package_markdown(manifest), encoding="utf-8")
    return SubmissionPackageBuildResult(
        json_path=json_path,
        markdown_path=markdown_path,
        manifest=manifest,
    )


def expected_submission_package_artifact_texts(
    *,
    release_manifest_path: str | Path = DEFAULT_RELEASE_MANIFEST_PATH,
    archive_manifest_path: str | Path = DEFAULT_ARCHIVE_MANIFEST_PATH,
    submission_readiness_path: str | Path = DEFAULT_SUBMISSION_READINESS_PATH,
    evidence_ledger_path: str | Path = DEFAULT_EVIDENCE_LEDGER_PATH,
    publication_gate_path: str | Path = DEFAULT_PUBLICATION_GATE_PATH,
    formatting_check_path: str | Path = DEFAULT_FORMATTING_CHECK_PATH,
) -> tuple[str, str]:
    manifest = build_submission_package_manifest(
        release_manifest=load_json_object(release_manifest_path),
        archive_manifest=load_json_object(archive_manifest_path),
        submission_readiness=load_json_object(submission_readiness_path),
        evidence_ledger=load_json_object(evidence_ledger_path),
        publication_gate=load_json_object(publication_gate_path),
        formatting_check=load_json_object(formatting_check_path),
    )
    return (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        render_submission_package_markdown(manifest),
    )


def stale_submission_package_artifacts(
    *,
    release_manifest_path: str | Path = DEFAULT_RELEASE_MANIFEST_PATH,
    archive_manifest_path: str | Path = DEFAULT_ARCHIVE_MANIFEST_PATH,
    submission_readiness_path: str | Path = DEFAULT_SUBMISSION_READINESS_PATH,
    evidence_ledger_path: str | Path = DEFAULT_EVIDENCE_LEDGER_PATH,
    publication_gate_path: str | Path = DEFAULT_PUBLICATION_GATE_PATH,
    formatting_check_path: str | Path = DEFAULT_FORMATTING_CHECK_PATH,
    output_json_path: str | Path = DEFAULT_SUBMISSION_PACKAGE_JSON_PATH,
    output_markdown_path: str | Path = DEFAULT_SUBMISSION_PACKAGE_MARKDOWN_PATH,
) -> list[Path]:
    expected_json, expected_markdown = expected_submission_package_artifact_texts(
        release_manifest_path=release_manifest_path,
        archive_manifest_path=archive_manifest_path,
        submission_readiness_path=submission_readiness_path,
        evidence_ledger_path=evidence_ledger_path,
        publication_gate_path=publication_gate_path,
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
