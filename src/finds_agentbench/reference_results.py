from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from finds_agentbench.reports import results_to_markdown


REFERENCE_RESULTS_COLUMNS = [
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

REFERENCE_RESULTS_KEY_COLUMNS = ["task_id", "agent_id", "run_type"]

BASELINE_SUITE_DESCRIPTION = (
    "Baseline-only pilot evaluation across synthetic market direction, synthetic event "
    "response, Treasury 10Y direction, 10Y-2Y and 10Y-3M curve steepening, front-end "
    "spread widening, USD broad direction, and USD AFE-versus-EME relative direction tasks."
)

AGENT_SUITE_DESCRIPTION = (
    "External-agent pilot evaluation across the implemented synthetic, rates, curve, "
    "front-end, and FX env-agent wrappers."
)

PILOT_PROTOCOL_DESCRIPTION = (
    "End-to-end combined benchmark snapshot including both baseline and external-agent "
    "runs under the same repeated-run protocol across the full pilot task set."
)


def load_csv_rows(path: str | Path) -> list[dict[str, Any]]:
    csv_path = Path(path)
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        return [_coerce_row_types(row) for row in csv.DictReader(handle)]


def _coerce_scalar(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not stripped:
        return value
    if stripped.isdigit() or (stripped.startswith("-") and stripped[1:].isdigit()):
        return int(stripped)
    try:
        return float(stripped)
    except ValueError:
        return value


def _coerce_row_types(row: dict[str, Any]) -> dict[str, Any]:
    return {key: _coerce_scalar(value) for key, value in row.items()}


def _sort_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    run_type_order = {
        "baseline": 0,
        "agent": 1,
        "human": 2,
        "expert": 3,
    }
    return sorted(
        rows,
        key=lambda row: (
            str(row.get("task_id", "")),
            run_type_order.get(str(row.get("run_type", "")), 99),
            str(row.get("agent_id", "")),
        ),
    )


def _row_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(row.get(column, "") for column in REFERENCE_RESULTS_KEY_COLUMNS)


def _row_key_string(row: dict[str, Any]) -> str:
    return " / ".join(str(row.get(column, "")) for column in REFERENCE_RESULTS_KEY_COLUMNS)


def _project_reference_row(row: dict[str, Any]) -> dict[str, Any]:
    return {column: row.get(column) for column in REFERENCE_RESULTS_COLUMNS}


def _rows_by_key(
    rows: list[dict[str, Any]],
    *,
    section_name: str,
) -> dict[tuple[Any, ...], dict[str, Any]]:
    keyed_rows: dict[tuple[Any, ...], dict[str, Any]] = {}
    duplicates: list[str] = []
    for row in rows:
        key = _row_key(row)
        if key in keyed_rows:
            duplicates.append(_row_key_string(row))
            continue
        keyed_rows[key] = row
    if duplicates:
        duplicate_list = ", ".join(sorted(duplicates))
        raise ValueError(f"{section_name} contains duplicate summary rows: {duplicate_list}")
    return keyed_rows


def _validate_section_rows(
    rows: list[dict[str, Any]],
    *,
    section_name: str,
    expected_run_type: str | None,
    expected_run_count: int | None,
) -> dict[tuple[Any, ...], dict[str, Any]]:
    keyed_rows = _rows_by_key(rows, section_name=section_name)
    for row in keyed_rows.values():
        row_key = _row_key_string(row)
        run_type = str(row.get("run_type", ""))
        if expected_run_type is not None and run_type != expected_run_type:
            raise ValueError(
                f"{section_name} row {row_key} has run_type={run_type!r}; "
                f"expected {expected_run_type!r}"
            )

        run_count = row.get("run_count")
        if not isinstance(run_count, int):
            raise ValueError(f"{section_name} row {row_key} is missing integer run_count")
        if expected_run_count is not None and run_count != expected_run_count:
            raise ValueError(
                f"{section_name} row {row_key} has run_count={run_count}; "
                f"expected {expected_run_count}"
            )

        completed_count = row.get("completed_count")
        if completed_count is not None:
            if not isinstance(completed_count, int):
                raise ValueError(
                    f"{section_name} row {row_key} is missing integer completed_count"
                )
            if completed_count > run_count:
                raise ValueError(
                    f"{section_name} row {row_key} has completed_count={completed_count} "
                    f"greater than run_count={run_count}"
                )

    return keyed_rows


def validate_reference_results_rows(
    *,
    baseline_rows: list[dict[str, Any]],
    agent_rows: list[dict[str, Any]],
    protocol_rows: list[dict[str, Any]],
    expected_run_count: int | None = None,
) -> None:
    baseline_by_key = _validate_section_rows(
        baseline_rows,
        section_name="baseline_rows",
        expected_run_type="baseline",
        expected_run_count=expected_run_count,
    )
    agent_by_key = _validate_section_rows(
        agent_rows,
        section_name="agent_rows",
        expected_run_type="agent",
        expected_run_count=expected_run_count,
    )
    protocol_by_key = _validate_section_rows(
        protocol_rows,
        section_name="protocol_rows",
        expected_run_type=None,
        expected_run_count=expected_run_count,
    )

    expected_protocol_by_key = {**baseline_by_key, **agent_by_key}
    expected_keys = set(expected_protocol_by_key)
    protocol_keys = set(protocol_by_key)
    missing_keys = expected_keys - protocol_keys
    extra_keys = protocol_keys - expected_keys

    if missing_keys:
        missing = ", ".join(
            " / ".join(str(part) for part in key) for key in sorted(missing_keys, key=str)
        )
        raise ValueError(f"protocol_rows is missing expected summary rows: {missing}")
    if extra_keys:
        extra = ", ".join(
            " / ".join(str(part) for part in key) for key in sorted(extra_keys, key=str)
        )
        raise ValueError(f"protocol_rows contains unexpected summary rows: {extra}")

    mismatched_keys: list[str] = []
    for key in sorted(expected_keys, key=str):
        expected_row = _project_reference_row(expected_protocol_by_key[key])
        protocol_row = _project_reference_row(protocol_by_key[key])
        if protocol_row != expected_row:
            mismatched_keys.append(" / ".join(str(part) for part in key))
    if mismatched_keys:
        mismatch_list = ", ".join(mismatched_keys)
        raise ValueError(
            "protocol_rows does not match baseline_rows + agent_rows for rows: "
            f"{mismatch_list}"
        )


def _reference_section_markdown(
    *,
    title: str,
    description: str,
    command: str,
    rows: list[dict[str, Any]],
) -> str:
    ordered_rows = _sort_rows(rows)
    return "\n".join(
        [
            f"## {title}",
            "",
            description,
            "",
            f"Official command: `{command}`",
            "",
            results_to_markdown(ordered_rows, columns=REFERENCE_RESULTS_COLUMNS).strip(),
            "",
        ]
    )


def render_reference_results_markdown(
    *,
    benchmark_id: str,
    benchmark_version: str,
    release_stage: str,
    treasury_snapshot_date: str,
    baseline_rows: list[dict[str, Any]],
    agent_rows: list[dict[str, Any]],
    protocol_rows: list[dict[str, Any]],
    baseline_command: str,
    agent_command: str,
    protocol_command: str,
) -> str:
    lines = [
        "# Pilot Reference Results",
        "",
        f"Reference repeated-run result snapshot for `{benchmark_id}`.",
        "",
        "## Snapshot",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Benchmark ID | {benchmark_id} |",
        f"| Benchmark Version | {benchmark_version} |",
        f"| Release Stage | {release_stage} |",
        f"| Treasury Snapshot Date | {treasury_snapshot_date} |",
        f"| Baseline Summary Rows | {len(baseline_rows)} |",
        f"| Agent Summary Rows | {len(agent_rows)} |",
        f"| Protocol Summary Rows | {len(protocol_rows)} |",
        "",
        "All summary statistics report repeated-run mean and sample standard deviation across the configured seeds.",
        "",
        _reference_section_markdown(
            title="Pilot Baseline Suite",
            description=BASELINE_SUITE_DESCRIPTION,
            command=baseline_command,
            rows=baseline_rows,
        ),
        _reference_section_markdown(
            title="Pilot Agent Suite",
            description=AGENT_SUITE_DESCRIPTION,
            command=agent_command,
            rows=agent_rows,
        ),
        _reference_section_markdown(
            title="Combined Pilot Protocol",
            description=PILOT_PROTOCOL_DESCRIPTION,
            command=protocol_command,
            rows=protocol_rows,
        ),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_reference_results_payload(
    *,
    benchmark_id: str,
    benchmark_version: str,
    release_stage: str,
    treasury_snapshot_date: str,
    baseline_rows: list[dict[str, Any]],
    agent_rows: list[dict[str, Any]],
    protocol_rows: list[dict[str, Any]],
    baseline_command: str,
    agent_command: str,
    protocol_command: str,
) -> dict[str, Any]:
    return {
        "benchmark_id": benchmark_id,
        "benchmark_version": benchmark_version,
        "release_stage": release_stage,
        "treasury_snapshot_date": treasury_snapshot_date,
        "sections": [
            {
                "section_id": "pilot_baseline_suite",
                "title": "Pilot Baseline Suite",
                "command": baseline_command,
                "rows": _sort_rows(baseline_rows),
            },
            {
                "section_id": "pilot_agent_suite",
                "title": "Pilot Agent Suite",
                "command": agent_command,
                "rows": _sort_rows(agent_rows),
            },
            {
                "section_id": "pilot_protocol",
                "title": "Combined Pilot Protocol",
                "command": protocol_command,
                "rows": _sort_rows(protocol_rows),
            },
        ],
    }


def write_reference_results_snapshot(
    *,
    output_markdown_path: str | Path,
    output_json_path: str | Path,
    benchmark_id: str,
    benchmark_version: str,
    release_stage: str,
    treasury_snapshot_date: str,
    baseline_rows: list[dict[str, Any]],
    agent_rows: list[dict[str, Any]],
    protocol_rows: list[dict[str, Any]],
    baseline_command: str,
    agent_command: str,
    protocol_command: str,
    expected_run_count: int | None = None,
) -> tuple[Path, Path]:
    markdown_path = Path(output_markdown_path)
    json_path = Path(output_json_path)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    validate_reference_results_rows(
        baseline_rows=baseline_rows,
        agent_rows=agent_rows,
        protocol_rows=protocol_rows,
        expected_run_count=expected_run_count,
    )

    payload = build_reference_results_payload(
        benchmark_id=benchmark_id,
        benchmark_version=benchmark_version,
        release_stage=release_stage,
        treasury_snapshot_date=treasury_snapshot_date,
        baseline_rows=baseline_rows,
        agent_rows=agent_rows,
        protocol_rows=protocol_rows,
        baseline_command=baseline_command,
        agent_command=agent_command,
        protocol_command=protocol_command,
    )
    markdown = render_reference_results_markdown(
        benchmark_id=benchmark_id,
        benchmark_version=benchmark_version,
        release_stage=release_stage,
        treasury_snapshot_date=treasury_snapshot_date,
        baseline_rows=baseline_rows,
        agent_rows=agent_rows,
        protocol_rows=protocol_rows,
        baseline_command=baseline_command,
        agent_command=agent_command,
        protocol_command=protocol_command,
    )

    markdown_path.write_text(markdown, encoding="utf-8")
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return markdown_path, json_path
