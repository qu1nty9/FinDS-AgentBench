from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from finds_agentbench.io import load_yaml


@dataclass(frozen=True)
class TaskCardBuildResult:
    task_specs: list[Path]
    task_card_paths: list[Path]
    evaluation_card_paths: list[Path]
    registry_json_path: Path
    registry_csv_path: Path
    index_path: Path


def discover_task_specs(tasks_root: str | Path) -> list[Path]:
    root = Path(tasks_root)
    return sorted(path for path in root.rglob("*.yaml") if path.is_file())


def format_scalar(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def format_markdown_value(value: Any) -> str:
    return format_scalar(value).replace("|", "\\|").replace("\n", "<br>")


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return "_None._\n"
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(format_markdown_value(value) for value in row) + " |")
    return "\n".join(lines) + "\n"


def markdown_bullets(items: list[Any] | tuple[Any, ...] | None) -> str:
    if not items:
        return "_None._\n"
    return "\n".join(f"- {format_scalar(item)}" for item in items) + "\n"


def render_sources_table(sources: list[dict[str, Any]]) -> str:
    rows = [
        [
            source.get("name"),
            source.get("license"),
            source.get("access"),
            source.get("url_or_reference"),
        ]
        for source in sources
    ]
    return markdown_table(["Name", "License", "Access", "Reference"], rows)


def render_data_dictionary_table(columns: list[dict[str, Any]]) -> str:
    rows = [
        [column.get("column"), column.get("meaning"), column.get("availability_lag")]
        for column in columns
    ]
    return markdown_table(["Column", "Meaning", "Availability Lag"], rows)


def render_availability_calendar_table(items: list[dict[str, Any]]) -> str:
    rows = [
        [item.get("item"), item.get("known_at"), item.get("usable_for_prediction_at")]
        for item in items
    ]
    return markdown_table(["Item", "Known At", "Usable For Prediction At"], rows)


def render_split_table(splits: dict[str, Any]) -> str:
    rows: list[list[Any]] = []
    for split_name in ("train", "public_validation", "private_temporal_holdout"):
        split = splits.get(split_name, {})
        rows.append([split_name, split.get("start"), split.get("end")])
    for stress_test in splits.get("stress_tests", []):
        rows.append(
            [
                f"stress_test:{stress_test.get('name', 'unnamed')}",
                stress_test.get("start"),
                stress_test.get("end"),
            ]
        )
    return markdown_table(["Split", "Start", "End"], rows)


def render_snapshot_table(spec: dict[str, Any], source_path: Path) -> str:
    metadata = spec.get("metadata", {})
    data = spec.get("data", {})
    evaluation = spec.get("evaluation", {})
    rows = [
        ["Task ID", metadata.get("task_id")],
        ["Title", metadata.get("title")],
        ["Track", metadata.get("track")],
        ["Version", metadata.get("version")],
        ["Status", metadata.get("status")],
        ["Owner", metadata.get("owner")],
        ["Tags", ", ".join(metadata.get("tags", [])) or "-"],
        ["Source Spec", str(source_path)],
        ["Data Access", data.get("access")],
        ["License Status", data.get("license_status")],
        ["Primary Metric", evaluation.get("primary_metric")],
    ]
    return markdown_table(["Field", "Value"], rows)


def render_task_card(spec: dict[str, Any], *, source_path: Path) -> str:
    metadata = spec.get("metadata", {})
    research_prompt = spec.get("research_prompt", {})
    data = spec.get("data", {})
    information_set = spec.get("information_set", {})
    target = spec.get("target", {})
    splits = spec.get("splits", {})
    deliverables = spec.get("deliverables", {})
    reproducibility = spec.get("reproducibility", {})
    audit = spec.get("audit", {})

    task_id = format_scalar(metadata.get("task_id"))
    sections = [
        f"# {task_id} Task Card\n",
        "Generated from the benchmark task specification.\n",
        "## Snapshot\n",
        render_snapshot_table(spec, source_path),
        "## Research Prompt\n",
        f"**Summary**: {format_scalar(research_prompt.get('summary'))}\n",
        f"**Research Question**: {format_scalar(research_prompt.get('expected_research_question'))}\n",
        f"**Instructions**: {format_scalar(research_prompt.get('instructions'))}\n",
        "\n**Prohibited Shortcuts**\n",
        markdown_bullets(research_prompt.get("prohibited_shortcuts")),
        "## Data\n",
        f"**Local Paths**: {', '.join(data.get('local_paths', [])) or '-'}\n",
        f"**Generator/Download Script**: {format_scalar(data.get('download_or_generation_script'))}\n",
        "\n**Sources**\n",
        render_sources_table(data.get("sources", [])),
        "\n**Data Dictionary**\n",
        render_data_dictionary_table(data.get("data_dictionary", [])),
        "## Information Set\n",
        f"**Prediction Timestamp**: {format_scalar(information_set.get('prediction_timestamp'))}\n",
        "\n**Allowed Information**\n",
        markdown_bullets(information_set.get("allowed_information")),
        "\n**Forbidden Information**\n",
        markdown_bullets(information_set.get("forbidden_information")),
        "\n**Availability Calendar**\n",
        render_availability_calendar_table(information_set.get("availability_calendar", [])),
        "\n**Timestamp Alignment Rules**\n",
        markdown_bullets(information_set.get("timestamp_alignment_rules")),
        "## Target\n",
        markdown_table(
            ["Field", "Value"],
            [
                ["Name", target.get("name")],
                ["Definition", target.get("definition")],
                ["Horizon", target.get("horizon")],
                ["Label Construction", target.get("label_construction")],
                ["Positive Class", target.get("positive_class")],
                ["Ranking Group", target.get("ranking_group")],
            ],
        ),
        "## Splits\n",
        f"**Split Method**: {format_scalar(splits.get('split_method'))}\n",
        f"**Embargo or Gap**: {format_scalar(splits.get('embargo_or_gap'))}\n",
        "\n",
        render_split_table(splits),
        "## Deliverables\n",
        "\n**Required Files**\n",
        markdown_bullets(deliverables.get("required_files")),
        markdown_table(
            ["Field", "Value"],
            [
                ["Notebook Path", deliverables.get("notebook", {}).get("path")],
                [
                    "Notebook Must Execute Cleanly",
                    deliverables.get("notebook", {}).get("must_execute_cleanly"),
                ],
                ["Predictions Path", deliverables.get("predictions", {}).get("path")],
                [
                    "Predictions Required Columns",
                    ", ".join(deliverables.get("predictions", {}).get("required_columns", [])) or "-",
                ],
                ["Writeup Path", deliverables.get("writeup", {}).get("path")],
                ["Writeup Max Words", deliverables.get("writeup", {}).get("max_words")],
                ["Retain Agent Trace", deliverables.get("logs", {}).get("retain_agent_trace")],
            ],
        ),
        "## Reproducibility and Audit\n",
        markdown_table(
            ["Field", "Value"],
            [
                ["Environment", reproducibility.get("environment")],
                ["Random Seed Policy", reproducibility.get("random_seed_policy")],
                ["Rerun Command", reproducibility.get("rerun_command")],
                ["Expected Runtime Limit", reproducibility.get("expected_runtime_limit")],
                ["CPU Limit", reproducibility.get("compute_limits", {}).get("cpu")],
                ["Memory Limit", reproducibility.get("compute_limits", {}).get("memory")],
            ],
        ),
        "\n**Artifact Retention**\n",
        markdown_bullets(audit.get("artifact_retention")),
        "\n**Trace Requirements**\n",
        markdown_bullets(audit.get("trace_requirements")),
    ]
    return "\n".join(sections).strip() + "\n"


def render_evaluation_card(spec: dict[str, Any], *, source_path: Path) -> str:
    metadata = spec.get("metadata", {})
    evaluation = spec.get("evaluation", {})
    leakage_checks = spec.get("leakage_checks", {})
    audit = spec.get("audit", {})

    task_id = format_scalar(metadata.get("task_id"))
    sections = [
        f"# {task_id} Evaluation Card\n",
        f"Source task specification: `{source_path}`.\n",
        "## Metrics\n",
        markdown_table(
            ["Field", "Value"],
            [
                ["Primary Metric", evaluation.get("primary_metric")],
                ["Aggregation", evaluation.get("aggregation")],
                [
                    "Secondary Metrics",
                    ", ".join(evaluation.get("secondary_metrics", [])) or "-",
                ],
                [
                    "Financial Metrics",
                    ", ".join(evaluation.get("financial_metrics", [])) or "-",
                ],
            ],
        ),
        "## Validity Gates\n",
        markdown_bullets(evaluation.get("validity_gates")),
        "## Minimum Success Conditions\n",
        markdown_bullets(evaluation.get("minimum_success_conditions")),
        "## Leakage and Validation Checks\n",
        "\n**Forbidden Columns**\n",
        markdown_bullets(leakage_checks.get("forbidden_columns")),
        "\n**Temporal Alignment Checks**\n",
        markdown_bullets(leakage_checks.get("temporal_alignment_checks")),
        "\n**Validation Protocol Checks**\n",
        markdown_bullets(leakage_checks.get("validation_protocol_checks")),
        "\n**Known Leakage Traps**\n",
        markdown_bullets(leakage_checks.get("known_leakage_traps")),
        "## Human Review Rubric\n",
        markdown_bullets(audit.get("human_review_rubric")),
        "## Failure Taxonomy References\n",
        markdown_bullets(audit.get("failure_taxonomy_refs")),
    ]
    return "\n".join(sections).strip() + "\n"


def build_registry_entry(spec: dict[str, Any], *, source_path: Path) -> dict[str, Any]:
    metadata = spec.get("metadata", {})
    data = spec.get("data", {})
    evaluation = spec.get("evaluation", {})
    splits = spec.get("splits", {})
    deliverables = spec.get("deliverables", {})
    return {
        "task_id": format_scalar(metadata.get("task_id")),
        "title": format_scalar(metadata.get("title")),
        "track": format_scalar(metadata.get("track")),
        "version": format_scalar(metadata.get("version")),
        "status": format_scalar(metadata.get("status")),
        "tags": metadata.get("tags", []),
        "source_spec": str(source_path),
        "data_access": format_scalar(data.get("access")),
        "license_status": format_scalar(data.get("license_status")),
        "split_method": format_scalar(splits.get("split_method")),
        "primary_metric": format_scalar(evaluation.get("primary_metric")),
        "required_files": deliverables.get("required_files", []),
    }


def build_task_cards(
    tasks_root: str | Path = "tasks/pilot",
    output_root: str | Path = "docs/cards",
) -> TaskCardBuildResult:
    task_specs = discover_task_specs(tasks_root)
    output_path = Path(output_root)
    task_cards_dir = output_path / "tasks"
    evaluation_cards_dir = output_path / "evaluations"
    task_cards_dir.mkdir(parents=True, exist_ok=True)
    evaluation_cards_dir.mkdir(parents=True, exist_ok=True)

    registry_entries: list[dict[str, Any]] = []
    task_card_paths: list[Path] = []
    evaluation_card_paths: list[Path] = []

    for spec_path in task_specs:
        spec = load_yaml(spec_path)
        metadata = spec.get("metadata", {})
        task_id = format_scalar(metadata.get("task_id"))
        task_card_path = task_cards_dir / f"{task_id}.md"
        evaluation_card_path = evaluation_cards_dir / f"{task_id}.md"
        task_card_path.write_text(
            render_task_card(spec, source_path=spec_path),
            encoding="utf-8",
        )
        evaluation_card_path.write_text(
            render_evaluation_card(spec, source_path=spec_path),
            encoding="utf-8",
        )
        task_card_paths.append(task_card_path)
        evaluation_card_paths.append(evaluation_card_path)
        registry_entries.append(build_registry_entry(spec, source_path=spec_path))

    registry_json_path = output_path / "task_registry.json"
    registry_json_path.write_text(
        json.dumps(registry_entries, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    registry_csv_path = output_path / "task_registry.csv"
    csv_fields = [
        "task_id",
        "title",
        "track",
        "version",
        "status",
        "source_spec",
        "data_access",
        "license_status",
        "split_method",
        "primary_metric",
        "tags",
        "required_files",
    ]
    with registry_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_fields)
        writer.writeheader()
        for entry in registry_entries:
            row = dict(entry)
            row["tags"] = ", ".join(entry.get("tags", []))
            row["required_files"] = ", ".join(entry.get("required_files", []))
            writer.writerow(row)

    index_path = output_path / "README.md"
    index_rows = [
        [
            entry["task_id"],
            entry["title"],
            entry["track"],
            entry["status"],
            f"[task](tasks/{entry['task_id']}.md)",
            f"[evaluation](evaluations/{entry['task_id']}.md)",
        ]
        for entry in registry_entries
    ]
    index_content = "\n".join(
        [
            "# Task Cards",
            "",
            "Generated from the benchmark YAML task specifications.",
            "",
            markdown_table(
                ["Task ID", "Title", "Track", "Status", "Task Card", "Evaluation Card"],
                index_rows,
            ).strip(),
            "",
            "- Registry JSON: `task_registry.json`",
            "- Registry CSV: `task_registry.csv`",
            "",
        ]
    )
    index_path.write_text(index_content, encoding="utf-8")

    return TaskCardBuildResult(
        task_specs=task_specs,
        task_card_paths=task_card_paths,
        evaluation_card_paths=evaluation_card_paths,
        registry_json_path=registry_json_path,
        registry_csv_path=registry_csv_path,
        index_path=index_path,
    )
