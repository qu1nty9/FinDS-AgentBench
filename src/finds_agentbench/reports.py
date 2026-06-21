from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev
from typing import Any

from finds_agentbench.runs import load_run_manifest, validate_run_manifest


DEFAULT_MARKDOWN_COLUMNS = [
    "task_id",
    "agent_id",
    "run_type",
    "status",
    "score.overall_score",
    "score.balanced_accuracy",
    "score.roc_auc",
    "score.execution_success",
    "failure_count",
]

DEFAULT_SUMMARY_GROUP_BY = ["task_id", "agent_id", "run_type"]

DEFAULT_SUMMARY_METRICS = [
    "score.overall_score",
    "score.balanced_accuracy",
    "score.roc_auc",
    "score.log_loss",
    "score.long_flat_mean_return",
    "score.max_drawdown",
    "score.turnover",
    "score.execution_success",
]

DEFAULT_SUMMARY_MARKDOWN_COLUMNS = [
    "task_id",
    "agent_id",
    "run_type",
    "run_count",
    "completed_count",
    "score.overall_score.mean",
    "score.overall_score.std",
    "score.balanced_accuracy.mean",
    "score.balanced_accuracy.std",
    "score.roc_auc.mean",
    "score.roc_auc.std",
]


def find_run_manifests(root: str | Path) -> list[Path]:
    root_path = Path(root)
    if root_path.is_file():
        return [root_path]
    return sorted(root_path.rglob("run_manifest.json"))


def flatten_dict(value: dict[str, Any], *, prefix: str = "") -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for key, item in value.items():
        flat_key = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(item, dict):
            rows.update(flatten_dict(item, prefix=flat_key))
        elif isinstance(item, list):
            rows[flat_key] = len(item)
        else:
            rows[flat_key] = item
    return rows


def manifest_to_result_row(
    manifest: dict[str, Any],
    *,
    source_path: str | Path | None = None,
) -> dict[str, Any]:
    agent = manifest.get("agent", {})
    timing = manifest.get("timing", {})
    artifacts = manifest.get("artifacts", {})
    validations = manifest.get("validations", {})
    scores = manifest.get("scores", {})
    trace = manifest.get("trace", {})
    files = artifacts.get("files", []) if isinstance(artifacts, dict) else []
    failures = manifest.get("failures", [])

    row: dict[str, Any] = {
        "manifest_path": str(source_path) if source_path is not None else "",
        "run_id": manifest.get("run_id", ""),
        "task_id": manifest.get("task_id", ""),
        "run_type": manifest.get("run_type", ""),
        "agent_id": agent.get("agent_id", "") if isinstance(agent, dict) else "",
        "agent_version": agent.get("agent_version", "") if isinstance(agent, dict) else "",
        "status": manifest.get("status", ""),
        "started_at": timing.get("started_at", "") if isinstance(timing, dict) else "",
        "completed_at": timing.get("completed_at", "") if isinstance(timing, dict) else "",
        "submission_dir": artifacts.get("submission_dir", "")
        if isinstance(artifacts, dict)
        else "",
        "artifact_file_count": len(files) if isinstance(files, list) else 0,
        "failure_count": len(failures) if isinstance(failures, list) else 0,
        "command_count": len(manifest.get("commands", []))
        if isinstance(manifest.get("commands", []), list)
        else 0,
        "tool_permission_count": len(manifest.get("tool_permissions", []))
        if isinstance(manifest.get("tool_permissions", []), list)
        else 0,
    }
    if isinstance(scores, dict):
        row.update({f"score.{key}": value for key, value in flatten_dict(scores).items()})
    if isinstance(validations, dict):
        row.update({f"validation.{key}": value for key, value in flatten_dict(validations).items()})
    if isinstance(trace, dict):
        row.update({f"trace.{key}": value for key, value in flatten_dict(trace).items()})
    return row


def load_result_rows(root: str | Path, *, strict: bool = False) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for manifest_path in find_run_manifests(root):
        manifest = load_run_manifest(manifest_path)
        validation = validate_run_manifest(manifest)
        if strict and not validation.ok:
            raise ValueError(f"Invalid run manifest {manifest_path}: {validation.errors}")
        row = manifest_to_result_row(manifest, source_path=manifest_path)
        row["manifest_valid"] = validation.ok
        row["manifest_error_count"] = len(validation.errors)
        row["manifest_warning_count"] = len(validation.warnings)
        rows.append(row)
    return rows


def write_results_csv(rows: list[dict[str, Any]], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def to_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return float(stripped)
        except ValueError:
            return None
    return None


def aggregate_result_rows(
    rows: list[dict[str, Any]],
    *,
    group_by: list[str] | None = None,
    metrics: list[str] | None = None,
) -> list[dict[str, Any]]:
    selected_group_by = group_by or DEFAULT_SUMMARY_GROUP_BY
    selected_metrics = metrics or DEFAULT_SUMMARY_METRICS
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = tuple(row.get(column, "") for column in selected_group_by)
        grouped[key].append(row)

    summary_rows: list[dict[str, Any]] = []
    sorted_groups = sorted(
        grouped.items(),
        key=lambda item: tuple(str(part) for part in item[0]),
    )
    for key, group_rows in sorted_groups:
        summary: dict[str, Any] = {
            column: value for column, value in zip(selected_group_by, key, strict=True)
        }
        summary["run_count"] = len(group_rows)
        summary["completed_count"] = sum(
            1 for row in group_rows if row.get("status") == "completed"
        )
        summary["manifest_valid_count"] = sum(
            1 for row in group_rows if row.get("manifest_valid") is True
        )
        summary["total_failure_count"] = int(
            sum(to_float(row.get("failure_count")) or 0.0 for row in group_rows)
        )

        for metric in selected_metrics:
            values = [
                numeric
                for numeric in (to_float(row.get(metric)) for row in group_rows)
                if numeric is not None
            ]
            if not values:
                continue
            summary[f"{metric}.count"] = len(values)
            summary[f"{metric}.mean"] = mean(values)
            summary[f"{metric}.std"] = stdev(values) if len(values) > 1 else 0.0
            summary[f"{metric}.min"] = min(values)
            summary[f"{metric}.max"] = max(values)
        summary_rows.append(summary)

    return summary_rows


def format_markdown_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def results_to_markdown(
    rows: list[dict[str, Any]],
    *,
    columns: list[str] | None = None,
) -> str:
    selected = columns or DEFAULT_MARKDOWN_COLUMNS
    lines = [
        "| " + " | ".join(selected) + " |",
        "| " + " | ".join(["---"] * len(selected)) + " |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(format_markdown_value(row.get(column, "")) for column in selected)
            + " |"
        )
    return "\n".join(lines) + "\n"


def write_results_markdown(
    rows: list[dict[str, Any]],
    output_path: str | Path,
    *,
    columns: list[str] | None = None,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(results_to_markdown(rows, columns=columns), encoding="utf-8")
    return path


def write_summary_csv(rows: list[dict[str, Any]], output_path: str | Path) -> Path:
    return write_results_csv(rows, output_path)


def write_summary_markdown(
    rows: list[dict[str, Any]],
    output_path: str | Path,
    *,
    columns: list[str] | None = None,
) -> Path:
    selected_columns = columns or DEFAULT_SUMMARY_MARKDOWN_COLUMNS
    return write_results_markdown(rows, output_path, columns=selected_columns)
