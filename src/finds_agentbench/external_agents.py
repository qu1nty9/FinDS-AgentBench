from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from finds_agentbench.io import load_yaml
from finds_agentbench.runs import load_run_manifest, validate_run_manifest


DEFAULT_EXTERNAL_AGENT_REGISTRY_PATH = Path("agents/external_agent_registry.yaml")
DEFAULT_EXTERNAL_AGENT_PROTOCOL_MARKDOWN_PATH = Path(
    "docs/releases/pilot_v0/external_agent_protocol.md"
)
DEFAULT_EXTERNAL_AGENT_HANDOFF_MARKDOWN_PATH = Path("agents/external_agent_handoff.md")
DEFAULT_EXTERNAL_AGENT_READINESS_JSON_PATH = Path(
    "docs/releases/pilot_v0/external_agent_readiness.json"
)
DEFAULT_EXTERNAL_AGENT_READINESS_MARKDOWN_PATH = Path(
    "docs/releases/pilot_v0/external_agent_readiness.md"
)
DEFAULT_EXTERNAL_AGENT_REGISTRATION_VALIDATION_JSON_PATH = Path(
    "docs/releases/pilot_v0/external_agent_registration_validation.json"
)
DEFAULT_EXTERNAL_AGENT_REGISTRATION_VALIDATION_MARKDOWN_PATH = Path(
    "docs/releases/pilot_v0/external_agent_registration_validation.md"
)

REQUIRED_AGENT_ENV_VARS = [
    "FINDS_TASK_ID",
    "FINDS_RUN_SEED",
    "FINDS_TASK_SPEC_PATH",
    "FINDS_PUBLIC_DATA_DIR",
    "FINDS_TRAIN_PUBLIC_PATH",
    "FINDS_HOLDOUT_FEATURES_PATH",
    "FINDS_PRIVATE_HOLDOUT_FEATURES_PATH",
    "FINDS_SAMPLE_SUBMISSION_PATH",
    "FINDS_METADATA_PATH",
    "FINDS_SUBMISSION_DIR",
]

REQUIRED_AGENT_ARTIFACTS = [
    "notebook.ipynb",
    "predictions.csv",
    "writeup.md",
]

EXTERNAL_AGENT_TEMPLATE_PATH = Path("agents/external_agent_registration_template.yaml")


def load_external_agent_registry(path: str | Path = DEFAULT_EXTERNAL_AGENT_REGISTRY_PATH) -> dict[str, Any]:
    return load_yaml(path)


def render_markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    body_lines = ["| " + " | ".join(str(value) for value in row) + " |" for row in rows]
    return "\n".join([header_line, separator_line, *body_lines])


def registry_agent_configurations(registry: dict[str, Any]) -> list[dict[str, Any]]:
    configurations: list[dict[str, Any]] = []
    for key in ("agent_configurations", "external_agent_configurations"):
        values = registry.get(key, [])
        if isinstance(values, list):
            configurations.extend(item for item in values if isinstance(item, dict))
    return configurations


def validate_external_agent_registry(registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if int(registry.get("schema_version", 0)) < 1:
        errors.append("schema_version must be >= 1")
    if not str(registry.get("registry_id", "")).strip():
        errors.append("registry_id must be non-empty")

    requirement = registry.get("required_for_workshop_submission", {})
    if not isinstance(requirement, dict):
        errors.append("required_for_workshop_submission must be an object")
        requirement = {}
    minimum_external = int(requirement.get("minimum_external_agent_configurations", 0) or 0)
    minimum_completed_runs = int(requirement.get("minimum_completed_runs_per_task", 0) or 0)
    if minimum_external < 1:
        errors.append("minimum_external_agent_configurations must be >= 1")
    if minimum_completed_runs < 1:
        errors.append("minimum_completed_runs_per_task must be >= 1")
    expected_tasks = requirement.get("expected_task_ids", [])
    if not isinstance(expected_tasks, list) or not expected_tasks:
        errors.append("expected_task_ids must be a non-empty list")

    for idx, config in enumerate(registry_agent_configurations(registry)):
        context = f"agent_configurations[{idx}]"
        for key in (
            "agent_id",
            "version",
            "provenance",
            "maintainer_type",
            "agent_type",
            "status",
            "command_family",
        ):
            if not str(config.get(key, "")).strip():
                errors.append(f"{context}.{key} must be non-empty")
        task_ids = config.get("task_ids", [])
        if not isinstance(task_ids, list) or not task_ids:
            errors.append(f"{context}.task_ids must be a non-empty list")
        if not isinstance(config.get("included_in_reference_results", False), bool):
            errors.append(f"{context}.included_in_reference_results must be boolean")
        if not isinstance(config.get("stronger_external_evidence", False), bool):
            errors.append(f"{context}.stronger_external_evidence must be boolean")
        if is_external_agent_configuration(config) and str(config.get("status", "")).strip() in {
            "completed",
            "completed_reference",
        }:
            errors.extend(
                f"{context}.{error}"
                for error in external_agent_completed_evidence_errors(
                    config,
                    minimum_completed_runs_per_task=minimum_completed_runs,
                )
            )
    return errors


def is_external_agent_configuration(config: dict[str, Any]) -> bool:
    provenance = str(config.get("provenance", "")).strip()
    maintainer_type = str(config.get("maintainer_type", "")).strip()
    return provenance.startswith("external") or maintainer_type == "external"


def is_completed_external_agent_configuration(config: dict[str, Any]) -> bool:
    return (
        is_external_agent_configuration(config)
        and bool(config.get("included_in_reference_results", False))
        and bool(config.get("stronger_external_evidence", False))
        and str(config.get("status", "")).strip() in {"completed", "completed_reference"}
    )


def external_agent_completed_evidence_errors(
    config: dict[str, Any],
    *,
    minimum_completed_runs_per_task: int,
) -> list[str]:
    errors: list[str] = []
    task_ids = [str(task_id) for task_id in config.get("task_ids", [])]
    completed_runs = config.get("completed_runs_per_task", {})
    if not isinstance(completed_runs, dict) or not completed_runs:
        errors.append("completed_runs_per_task must be a non-empty object for completed external configs")
        completed_runs = {}
    for task_id in task_ids:
        try:
            completed_count = int(completed_runs.get(task_id, 0))
        except (TypeError, ValueError):
            completed_count = 0
        if completed_count < minimum_completed_runs_per_task:
            errors.append(
                f"completed_runs_per_task.{task_id} must be >= {minimum_completed_runs_per_task}"
            )

    run_manifest_paths = config.get("run_manifest_paths", [])
    if not isinstance(run_manifest_paths, list) or not run_manifest_paths:
        errors.append("run_manifest_paths must be a non-empty list for completed external configs")
        run_manifest_paths = []
    elif any(not str(path).strip() for path in run_manifest_paths):
        errors.append("run_manifest_paths entries must be non-empty strings")

    required_run_manifest_count = sum(
        int(completed_runs.get(task_id, 0) or 0)
        for task_id in task_ids
        if str(task_id) in completed_runs
    )
    if run_manifest_paths and len(run_manifest_paths) < required_run_manifest_count:
        errors.append(
            "run_manifest_paths must include at least one manifest per completed run "
            f"({len(run_manifest_paths)} < {required_run_manifest_count})"
        )

    return errors


def resolve_external_agent_evidence_path(path_value: str | Path, *, workspace_root: Path) -> Path:
    path = Path(str(path_value))
    return path if path.is_absolute() else workspace_root / path


def external_agent_run_manifest_evidence_errors(
    config: dict[str, Any],
    manifest_path: str | Path,
    *,
    workspace_root: str | Path = ".",
) -> tuple[list[str], dict[str, Any] | None]:
    workspace = Path(workspace_root)
    path = resolve_external_agent_evidence_path(manifest_path, workspace_root=workspace)
    if not path.exists():
        return [f"run_manifest_path does not exist: {manifest_path}"], None

    try:
        manifest = load_run_manifest(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [f"run_manifest_path is not a readable run manifest: {manifest_path}: {exc}"], None

    validation = validate_run_manifest(manifest)
    errors = [f"run_manifest schema error: {error}" for error in validation.errors]

    agent = manifest.get("agent", {})
    expected_agent_id = str(config.get("agent_id", ""))
    expected_version = str(config.get("version", ""))
    if isinstance(agent, dict):
        if str(agent.get("agent_id", "")) != expected_agent_id:
            errors.append(
                f"run_manifest agent.agent_id must be {expected_agent_id!r}, "
                f"got {agent.get('agent_id')!r}"
            )
        if str(agent.get("agent_version", "")) != expected_version:
            errors.append(
                f"run_manifest agent.agent_version must be {expected_version!r}, "
                f"got {agent.get('agent_version')!r}"
            )

    task_ids = {str(task_id) for task_id in config.get("task_ids", [])}
    manifest_task_id = str(manifest.get("task_id", ""))
    if manifest_task_id not in task_ids:
        errors.append(
            f"run_manifest task_id must be one of {sorted(task_ids)}, got {manifest_task_id!r}"
        )

    if manifest.get("run_type") != "agent":
        errors.append(f"run_manifest run_type must be 'agent', got {manifest.get('run_type')!r}")
    if manifest.get("status") != "completed":
        errors.append(f"run_manifest status must be 'completed', got {manifest.get('status')!r}")

    validations = manifest.get("validations", {})
    artifact_validation = validations.get("artifact_validation", {}) if isinstance(validations, dict) else {}
    if not isinstance(artifact_validation, dict) or artifact_validation.get("ok") is not True:
        errors.append("run_manifest validations.artifact_validation.ok must be true")

    scores = manifest.get("scores", {})
    if not isinstance(scores, dict) or not scores:
        errors.append("run_manifest scores must be a non-empty object")
    elif "execution_success" in scores and not bool(scores["execution_success"]):
        errors.append("run_manifest scores.execution_success must be truthy when present")

    artifacts = manifest.get("artifacts", {})
    files = artifacts.get("files", []) if isinstance(artifacts, dict) else []
    file_names = {
        str(item.get("path", ""))
        for item in files
        if isinstance(item, dict) and str(item.get("path", ""))
    }
    missing_artifacts = sorted(set(REQUIRED_AGENT_ARTIFACTS) - file_names)
    if missing_artifacts:
        errors.append(
            "run_manifest artifact inventory missing required files: "
            + ", ".join(missing_artifacts)
        )

    return errors, manifest


def unique_preserving_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output


def apply_registration_validation_to_readiness(
    readiness: dict[str, Any],
    registration_validation: dict[str, Any],
) -> dict[str, Any]:
    if (
        not readiness.get("ready_for_external_agent_claims", False)
        or registration_validation.get("ready_for_external_agent_claims", False)
    ):
        return readiness

    combined = dict(readiness)
    combined["status"] = "not_ready_invalid_external_agent_evidence"
    combined["ready_for_external_agent_claims"] = False
    combined["blocking_items"] = unique_preserving_order(
        [
            *list(readiness.get("blocking_items", [])),
            *list(registration_validation.get("blocking_items", [])),
        ]
    )
    combined["claim_boundary"] = {
        "allowed_current_claim": (
            "The registry declares a candidate external-agent configuration, but run-manifest "
            "evidence has not passed validation."
        ),
        "disallowed_current_claim": "Ready external-agent evidence or stronger external-agent claims.",
    }
    return combined


def build_external_agent_readiness_report(registry: dict[str, Any]) -> dict[str, Any]:
    validation_errors = validate_external_agent_registry(registry)
    if validation_errors:
        raise ValueError("Invalid external-agent registry: " + "; ".join(validation_errors))

    requirement = registry["required_for_workshop_submission"]
    minimum_external = int(requirement["minimum_external_agent_configurations"])
    minimum_completed_runs = int(requirement.get("minimum_completed_runs_per_task", 1))
    expected_task_ids = [str(task_id) for task_id in requirement["expected_task_ids"]]
    configurations = registry_agent_configurations(registry)
    bundled_configs = [
        config for config in configurations if str(config.get("provenance")) == "bundled_reference"
    ]
    external_configs = [config for config in configurations if is_external_agent_configuration(config)]
    completed_external_configs = [
        config
        for config in configurations
        if is_completed_external_agent_configuration(config)
        and not external_agent_completed_evidence_errors(
            config,
            minimum_completed_runs_per_task=minimum_completed_runs,
        )
    ]

    covered_external_tasks = sorted(
        {
            str(task_id)
            for config in completed_external_configs
            for task_id in config.get("task_ids", [])
        }
    )
    missing_external_task_ids = sorted(set(expected_task_ids) - set(covered_external_tasks))
    ready = len(completed_external_configs) >= minimum_external and not missing_external_task_ids

    blocking_items: list[str] = []
    if len(completed_external_configs) < minimum_external:
        blocking_items.append(
            "Register and run at least one non-author external agent configuration through the pilot harness."
        )
    if missing_external_task_ids:
        blocking_items.append(
            "Cover all expected pilot agent tasks with completed external-agent runs or declare a scoped external-agent subset."
        )
    if minimum_completed_runs < 3:
        blocking_items.append("Set minimum_completed_runs_per_task to at least 3 for workshop claims.")

    status = "ready_for_external_agent_claims" if ready else "not_ready_no_external_agents"
    return {
        "status": status,
        "ready_for_external_agent_claims": ready,
        "registry_id": registry["registry_id"],
        "minimum_external_agent_configurations": minimum_external,
        "minimum_completed_runs_per_task": minimum_completed_runs,
        "expected_task_ids": expected_task_ids,
        "expected_task_count": len(expected_task_ids),
        "bundled_reference_agent_count": len(bundled_configs),
        "bundled_reference_agent_ids": sorted(str(config["agent_id"]) for config in bundled_configs),
        "external_agent_configuration_count": len(external_configs),
        "completed_external_agent_configuration_count": len(completed_external_configs),
        "completed_external_agent_ids": sorted(
            str(config["agent_id"]) for config in completed_external_configs
        ),
        "external_task_coverage_count": len(covered_external_tasks),
        "covered_external_task_ids": covered_external_tasks,
        "missing_external_task_ids": missing_external_task_ids,
        "blocking_items": blocking_items,
        "claim_boundary": {
            "allowed_current_claim": (
                "The benchmark includes a command-based external-agent harness and bundled reference agents."
                if not ready
                else "At least one completed external-agent configuration is available for benchmark claims."
            ),
            "disallowed_current_claim": (
                "Broad external-agent leaderboard or stronger external-agent evidence."
                if not ready
                else ""
            ),
        },
        "non_blocking_cautions": [
            "Bundled reference agents are maintained by the benchmark authors and should not be framed as independent external systems."
        ],
        "next_actions": [
            "Add an external_agent_configurations entry for a non-author agent.",
            "Run the agent with the same command harness, repeated seeds, task specs, and hidden-label protections.",
            "Regenerate reference results, readiness reports, and the manuscript checklist.",
        ]
        if not ready
        else [
            "Inspect external-agent run manifests and artifact validation before final submission claims."
        ],
    }


def render_external_agent_protocol_markdown(
    registry: dict[str, Any],
    readiness: dict[str, Any],
) -> str:
    requirement = registry["required_for_workshop_submission"]
    expected_tasks = ", ".join(str(task_id) for task_id in requirement["expected_task_ids"])
    env_rows = [[name, "provided by the harness"] for name in REQUIRED_AGENT_ENV_VARS]
    artifact_rows = [[name, "required in FINDS_SUBMISSION_DIR"] for name in REQUIRED_AGENT_ARTIFACTS]
    return "\n".join(
        [
            "# External Agent Protocol",
            "",
            "This protocol defines how non-author agents should be evaluated in FinDS-AgentBench.",
            "",
            "## Submission Contract",
            "",
            "- Agents are launched through the existing `scripts/run_*_agent_suite.py` wrappers.",
            "- Commands are parsed with `shlex`; private answer-key paths are not exposed in the agent environment.",
            "- Each completed run must write the required submission artifacts before scoring.",
            "- Run manifests, stdout, stderr, validation, score, and methodology reports are retained under the run directory.",
            "",
            "## Required Environment",
            "",
            render_markdown_table(["Variable", "Meaning"], env_rows),
            "",
            "## Required Artifacts",
            "",
            render_markdown_table(["Artifact", "Requirement"], artifact_rows),
            "",
            "## Workshop Readiness Requirement",
            "",
            f"- Minimum external agent configurations: `{readiness['minimum_external_agent_configurations']}`",
            f"- Minimum completed runs per task: `{readiness['minimum_completed_runs_per_task']}`",
            f"- Expected task coverage: `{expected_tasks}`",
            "",
            "## Current Claim Boundary",
            "",
            f"- Current readiness status: `{readiness['status']}`",
            f"- Allowed current claim: {readiness['claim_boundary']['allowed_current_claim']}",
            f"- Disallowed current claim: {readiness['claim_boundary']['disallowed_current_claim'] or 'n/a'}",
            "",
        ]
    )


def build_external_agent_registration_validation_report(
    registry: dict[str, Any],
    *,
    workspace_root: str | Path = ".",
) -> dict[str, Any]:
    workspace = Path(workspace_root)
    validation_errors = validate_external_agent_registry(registry)
    readiness: dict[str, Any] | None = None
    if not validation_errors:
        readiness = build_external_agent_readiness_report(registry)

    external_configs = [
        config for config in registry_agent_configurations(registry) if is_external_agent_configuration(config)
    ]
    path_errors: list[str] = []
    evidence_errors: list[str] = []
    valid_run_manifest_count_by_agent: dict[str, int] = {}
    valid_run_manifest_count_by_agent_task: dict[tuple[str, str], int] = {}
    seen_run_ids: dict[str, str] = {}
    for config in external_configs:
        agent_id = str(config.get("agent_id", "unknown"))
        for path_value in config.get("run_manifest_paths", []) or []:
            evidence_path = resolve_external_agent_evidence_path(path_value, workspace_root=workspace)
            errors, manifest = external_agent_run_manifest_evidence_errors(
                config,
                path_value,
                workspace_root=workspace,
            )
            if errors:
                if any(error.startswith("run_manifest_path does not exist") for error in errors):
                    path_errors.extend(f"{agent_id}: {error}" for error in errors)
                else:
                    evidence_errors.extend(f"{agent_id}: {path_value}: {error}" for error in errors)
                continue

            assert manifest is not None
            run_id = str(manifest.get("run_id", ""))
            if run_id in seen_run_ids:
                evidence_errors.append(
                    f"{agent_id}: {path_value}: duplicate run_id {run_id!r}; "
                    f"already seen in {seen_run_ids[run_id]}"
                )
                continue
            seen_run_ids[run_id] = str(evidence_path)
            task_id = str(manifest.get("task_id", ""))
            valid_run_manifest_count_by_agent[agent_id] = (
                valid_run_manifest_count_by_agent.get(agent_id, 0) + 1
            )
            key = (agent_id, task_id)
            valid_run_manifest_count_by_agent_task[key] = (
                valid_run_manifest_count_by_agent_task.get(key, 0) + 1
            )

        completed_runs = config.get("completed_runs_per_task", {})
        if isinstance(completed_runs, dict):
            for task_id, declared_count in completed_runs.items():
                try:
                    expected_count = int(declared_count)
                except (TypeError, ValueError):
                    expected_count = 0
                actual_count = valid_run_manifest_count_by_agent_task.get((agent_id, str(task_id)), 0)
                if actual_count < expected_count:
                    evidence_errors.append(
                        f"{agent_id}: valid run manifests for {task_id} are below declared "
                        f"completed_runs_per_task ({actual_count} < {expected_count})"
                    )

    blocking_items: list[str] = []
    if not external_configs:
        blocking_items.append("No external_agent_configurations entries are registered.")
    if validation_errors:
        blocking_items.extend(validation_errors)
    if path_errors:
        blocking_items.extend(path_errors)
    if evidence_errors:
        blocking_items.extend(evidence_errors)
    if readiness and readiness["blocking_items"]:
        blocking_items.extend(readiness["blocking_items"])

    registration_ready = bool(
        readiness
        and readiness["ready_for_external_agent_claims"]
        and not validation_errors
        and not path_errors
        and not evidence_errors
    )

    if validation_errors or path_errors or evidence_errors:
        status = "invalid_external_agent_registration"
    elif registration_ready:
        status = "ready_for_external_agent_claims"
    elif external_configs:
        status = "registered_but_not_ready_for_claims"
    else:
        status = "no_external_agent_registered"

    config_rows = []
    for config in external_configs:
        completed_runs = config.get("completed_runs_per_task", {})
        if isinstance(completed_runs, dict):
            completed_runs_text = ", ".join(
                f"{task_id}:{count}" for task_id, count in sorted(completed_runs.items())
            )
        else:
            completed_runs_text = "invalid"
        config_rows.append(
            {
                "agent_id": str(config.get("agent_id", "")),
                "status": str(config.get("status", "")),
                "maintainer_type": str(config.get("maintainer_type", "")),
                "included_in_reference_results": bool(config.get("included_in_reference_results", False)),
                "stronger_external_evidence": bool(config.get("stronger_external_evidence", False)),
                "task_ids": [str(task_id) for task_id in config.get("task_ids", [])],
                "completed_runs_per_task": completed_runs_text,
                "run_manifest_path_count": len(config.get("run_manifest_paths", []) or []),
                "valid_run_manifest_count": valid_run_manifest_count_by_agent.get(
                    str(config.get("agent_id", "")),
                    0,
                ),
            }
        )

    return {
        "status": status,
        "ready_for_external_agent_claims": registration_ready,
        "registry_id": registry.get("registry_id", ""),
        "external_agent_configuration_count": len(external_configs),
        "completed_external_agent_configuration_count": (
            readiness["completed_external_agent_configuration_count"] if readiness else 0
        ),
        "external_task_coverage_count": readiness["external_task_coverage_count"] if readiness else 0,
        "expected_task_count": readiness["expected_task_count"] if readiness else 0,
        "validation_error_count": len(validation_errors),
        "path_error_count": len(path_errors),
        "evidence_error_count": len(evidence_errors),
        "valid_run_manifest_count": sum(valid_run_manifest_count_by_agent.values()),
        "blocking_items": blocking_items,
        "external_configurations": config_rows,
        "template_path": str(EXTERNAL_AGENT_TEMPLATE_PATH),
        "next_actions": [
            "Copy agents/external_agent_registration_template.yaml into an external_agent_configurations entry.",
            "Run the external agent through the pilot command harness for the required repeated runs.",
            "Record completed_runs_per_task and run_manifest_paths for every completed run.",
            "Ensure every run_manifest.json validates, matches the registered agent/task, and reports completed artifact validation.",
            "Re-run scripts/validate_external_agent_registry.py and rebuild release artifacts.",
        ]
        if not (readiness and readiness["ready_for_external_agent_claims"])
        else [
            "Inspect external-agent run manifests, artifact validation, and reference-result inclusion before submission."
        ],
    }


def render_external_agent_registration_validation_markdown(report: dict[str, Any]) -> str:
    summary_rows = [
        ["Status", f"`{report['status']}`"],
        [
            "Ready for external-agent claims",
            "yes" if report["ready_for_external_agent_claims"] else "no",
        ],
        ["External configurations", report["external_agent_configuration_count"]],
        [
            "Completed external configurations",
            report["completed_external_agent_configuration_count"],
        ],
        [
            "External task coverage",
            f"{report['external_task_coverage_count']} / {report['expected_task_count']}",
        ],
        ["Validation errors", report["validation_error_count"]],
        ["Path errors", report["path_error_count"]],
        ["Evidence errors", report["evidence_error_count"]],
        ["Valid run manifests", report["valid_run_manifest_count"]],
        ["Template", report["template_path"]],
    ]
    config_rows = [
        [
            config["agent_id"],
            config["status"],
            config["maintainer_type"],
            "yes" if config["included_in_reference_results"] else "no",
            "yes" if config["stronger_external_evidence"] else "no",
            ", ".join(config["task_ids"]),
            config["completed_runs_per_task"],
            config["run_manifest_path_count"],
            config["valid_run_manifest_count"],
        ]
        for config in report["external_configurations"]
    ]
    lines = [
        "# External Agent Registration Validation",
        "",
        "Validation report for non-author external-agent registration and run evidence.",
        "",
        "## Status",
        "",
        render_markdown_table(["Field", "Value"], summary_rows),
        "",
        "## External Configurations",
        "",
        render_markdown_table(
            [
                "Agent",
                "Status",
                "Maintainer",
                "In Reference Results",
                "Stronger Evidence",
                "Tasks",
                "Completed Runs",
                "Run Manifests",
                "Valid Run Manifests",
            ],
            config_rows
            or [["(none)", "n/a", "n/a", "no", "no", "n/a", "n/a", 0, 0]],
        ),
        "",
        "## Blocking Items",
        "",
    ]
    if report["blocking_items"]:
        lines.extend(f"- {item}" for item in report["blocking_items"])
    else:
        lines.append("- None.")
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {item}" for item in report["next_actions"])
    return "\n".join(lines) + "\n"


def render_external_agent_handoff_markdown(
    registry: dict[str, Any],
    readiness: dict[str, Any],
) -> str:
    expected_tasks = readiness["expected_task_ids"]
    command_rows = [
        [config["agent_id"], config["command_family"], ", ".join(config["task_ids"])]
        for config in registry_agent_configurations(registry)
        if str(config.get("provenance", "")) == "bundled_reference"
    ]
    return "\n".join(
        [
            "# External Agent Handoff",
            "",
            "Use this protocol to register and run a non-author external agent for FinDS-AgentBench.",
            "",
            "## Claim Boundary",
            "",
            "- Bundled reference agents are benchmark-maintained examples.",
            "- A submission-strength external-agent claim requires a non-author configuration with completed run evidence.",
            "- Do not mark `stronger_external_evidence: true` until the run manifests are included in reference results.",
            "",
            "## Registration",
            "",
            "- Start from `agents/external_agent_registration_template.yaml`.",
            "- Add the completed entry under `external_agent_configurations` in `agents/external_agent_registry.yaml`.",
            "- Set `maintainer_type: external` and `provenance: external_submission`.",
            "- Record `completed_runs_per_task` and every `run_manifest_path` after the harness finishes.",
            "",
            "## Required Coverage",
            "",
            f"- Minimum external configurations: `{readiness['minimum_external_agent_configurations']}`",
            f"- Minimum completed runs per task: `{readiness['minimum_completed_runs_per_task']}`",
            f"- Expected task IDs: `{', '.join(expected_tasks)}`",
            "",
            "## Validation",
            "",
            "```bash",
            "PYTHONPATH=src python scripts/validate_external_agent_registry.py",
            "```",
            "",
            "The registry is eligible for external-agent claims only when the validation report and readiness report both say ready.",
            "",
            "## Existing Harness Families",
            "",
            render_markdown_table(["Bundled Agent", "Command Family", "Tasks"], command_rows),
            "",
        ]
    )


def render_external_agent_readiness_markdown(readiness: dict[str, Any]) -> str:
    summary_rows = [
        ["Status", f"`{readiness['status']}`"],
        ["Ready for external-agent claims", "yes" if readiness["ready_for_external_agent_claims"] else "no"],
        ["Bundled reference agents", readiness["bundled_reference_agent_count"]],
        ["External agent configurations", readiness["external_agent_configuration_count"]],
        ["Completed external agent configurations", readiness["completed_external_agent_configuration_count"]],
        ["External task coverage", f"{readiness['external_task_coverage_count']} / {readiness['expected_task_count']}"],
        ["Minimum completed runs per task", readiness["minimum_completed_runs_per_task"]],
    ]
    lines = [
        "# External Agent Readiness",
        "",
        "This report gates claims about independent or stronger external-agent evidence.",
        "",
        "## Status",
        "",
        render_markdown_table(["Field", "Value"], summary_rows),
        "",
        "## Claim Boundary",
        "",
        f"- Allowed current claim: {readiness['claim_boundary']['allowed_current_claim']}",
        f"- Disallowed current claim: {readiness['claim_boundary']['disallowed_current_claim'] or 'n/a'}",
        "",
        "## Blocking Items",
        "",
    ]
    if readiness["blocking_items"]:
        lines.extend(f"- {item}" for item in readiness["blocking_items"])
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Bundled Reference Agents",
            "",
            render_markdown_table(
                ["Agent ID"],
                [[agent_id] for agent_id in readiness["bundled_reference_agent_ids"]],
            ),
            "",
            "## Missing External Task Coverage",
            "",
        ]
    )
    if readiness["missing_external_task_ids"]:
        lines.extend(f"- `{task_id}`" for task_id in readiness["missing_external_task_ids"])
    else:
        lines.append("- None.")
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {item}" for item in readiness["next_actions"])
    return "\n".join(lines)


def build_external_agent_readiness_artifacts(
    *,
    registry_path: str | Path = DEFAULT_EXTERNAL_AGENT_REGISTRY_PATH,
    protocol_markdown_path: str | Path = DEFAULT_EXTERNAL_AGENT_PROTOCOL_MARKDOWN_PATH,
    handoff_markdown_path: str | Path = DEFAULT_EXTERNAL_AGENT_HANDOFF_MARKDOWN_PATH,
    readiness_json_path: str | Path = DEFAULT_EXTERNAL_AGENT_READINESS_JSON_PATH,
    readiness_markdown_path: str | Path = DEFAULT_EXTERNAL_AGENT_READINESS_MARKDOWN_PATH,
    registration_validation_json_path: str | Path = (
        DEFAULT_EXTERNAL_AGENT_REGISTRATION_VALIDATION_JSON_PATH
    ),
    registration_validation_markdown_path: str | Path = (
        DEFAULT_EXTERNAL_AGENT_REGISTRATION_VALIDATION_MARKDOWN_PATH
    ),
    workspace_root: str | Path = ".",
) -> dict[str, Any]:
    registry = load_external_agent_registry(registry_path)
    readiness = build_external_agent_readiness_report(registry)
    registration_validation = build_external_agent_registration_validation_report(
        registry,
        workspace_root=workspace_root,
    )
    readiness = apply_registration_validation_to_readiness(readiness, registration_validation)

    protocol_path = Path(protocol_markdown_path)
    protocol_path.parent.mkdir(parents=True, exist_ok=True)
    protocol_path.write_text(
        render_external_agent_protocol_markdown(registry, readiness),
        encoding="utf-8",
    )

    handoff_path = Path(handoff_markdown_path)
    handoff_path.parent.mkdir(parents=True, exist_ok=True)
    handoff_path.write_text(
        render_external_agent_handoff_markdown(registry, readiness),
        encoding="utf-8",
    )

    readiness_json = Path(readiness_json_path)
    readiness_json.parent.mkdir(parents=True, exist_ok=True)
    readiness_json.write_text(
        json.dumps(readiness, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    readiness_markdown = Path(readiness_markdown_path)
    readiness_markdown.parent.mkdir(parents=True, exist_ok=True)
    readiness_markdown.write_text(
        render_external_agent_readiness_markdown(readiness) + "\n",
        encoding="utf-8",
    )

    registration_validation_json = Path(registration_validation_json_path)
    registration_validation_json.parent.mkdir(parents=True, exist_ok=True)
    registration_validation_json.write_text(
        json.dumps(registration_validation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    registration_validation_markdown = Path(registration_validation_markdown_path)
    registration_validation_markdown.parent.mkdir(parents=True, exist_ok=True)
    registration_validation_markdown.write_text(
        render_external_agent_registration_validation_markdown(registration_validation),
        encoding="utf-8",
    )

    return {
        "registry_path": Path(registry_path),
        "protocol_markdown_path": protocol_path,
        "handoff_markdown_path": handoff_path,
        "readiness_json_path": readiness_json,
        "readiness_markdown_path": readiness_markdown,
        "registration_validation_json_path": registration_validation_json,
        "registration_validation_markdown_path": registration_validation_markdown,
        "registration_validation": registration_validation,
        "readiness": readiness,
    }
