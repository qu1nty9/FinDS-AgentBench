from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from finds_agentbench.io import load_yaml
from finds_agentbench.methodology import methodology_rules_for_task, scan_submission_methodology
from finds_agentbench.runs import load_run_manifest


DEFAULT_METHODOLOGY_CALIBRATION_ROOT = Path("audits/methodology_calibration")
DEFAULT_METHODOLOGY_CALIBRATION_CONFIG_PATH = DEFAULT_METHODOLOGY_CALIBRATION_ROOT / "corpus.yaml"
DEFAULT_METHODOLOGY_CALIBRATION_REVIEWS_DIR = DEFAULT_METHODOLOGY_CALIBRATION_ROOT / "reviews"
DEFAULT_METHODOLOGY_CALIBRATION_REPORTS_DIR = DEFAULT_METHODOLOGY_CALIBRATION_ROOT / "reports"
DEFAULT_METHODOLOGY_CALIBRATION_REVIEW_PACKET_PATH = (
    DEFAULT_METHODOLOGY_CALIBRATION_REVIEWS_DIR / "calibration_review_packet.csv"
)
DEFAULT_METHODOLOGY_CALIBRATION_SUMMARY_JSON_PATH = (
    DEFAULT_METHODOLOGY_CALIBRATION_REPORTS_DIR / "summary.json"
)
DEFAULT_METHODOLOGY_CALIBRATION_SUMMARY_MARKDOWN_PATH = (
    DEFAULT_METHODOLOGY_CALIBRATION_REPORTS_DIR / "summary.md"
)


@dataclass(frozen=True)
class MethodologyCalibrationEntry:
    entry_id: str
    corpus_label: str
    source_kind: str
    task_id: str
    submission_dir: Path
    run_type: str
    agent_id: str
    run_label: str
    manifest_path: Path | None = None
    fixture_id: str | None = None
    expected_flagged: bool | None = None
    expected_rule_ids: tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class MethodologyCalibrationScan:
    entry: MethodologyCalibrationEntry
    findings: list[dict[str, str]]
    scanned_files: int
    skipped_files: int

    @property
    def finding_count(self) -> int:
        return len(self.findings)

    @property
    def flagged(self) -> bool:
        return bool(self.findings)

    @property
    def rule_ids(self) -> tuple[str, ...]:
        return tuple(sorted({finding["rule_id"] for finding in self.findings}))


def resolve_path(path_value: str | Path, *, base_dir: Path, workspace_root: Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    workspace_candidate = workspace_root / path
    if workspace_candidate.exists():
        return workspace_candidate
    return base_dir / path


def relative_to_workspace(path: Path, workspace_root: Path) -> str:
    try:
        return str(path.relative_to(workspace_root))
    except ValueError:
        return str(path)


def task_spec_path(task_id: str, *, tasks_root: Path) -> Path:
    return tasks_root / f"{task_id}.yaml"


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return ""
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def load_methodology_calibration_config(
    config_path: str | Path = DEFAULT_METHODOLOGY_CALIBRATION_CONFIG_PATH,
) -> dict[str, Any]:
    return load_yaml(config_path)


def discover_run_corpus_entries(
    config: dict[str, Any],
    *,
    config_dir: Path,
    workspace_root: Path,
) -> list[MethodologyCalibrationEntry]:
    entries: list[MethodologyCalibrationEntry] = []
    for corpus in config.get("run_corpora", []):
        if not isinstance(corpus, dict):
            continue
        label = str(corpus.get("label", "")).strip()
        root_value = corpus.get("root")
        if not label or not root_value:
            continue
        root = resolve_path(root_value, base_dir=config_dir, workspace_root=workspace_root)
        for manifest_path in sorted(root.rglob("run_manifest.json")):
            manifest = load_run_manifest(manifest_path)
            task_id = str(manifest.get("task_id", "")).strip()
            run_type = str(manifest.get("run_type", "")).strip()
            agent = manifest.get("agent", {})
            trace = manifest.get("trace", {})
            artifacts = manifest.get("artifacts", {})
            if not task_id:
                continue
            submission_value = (
                artifacts.get("submission_dir") if isinstance(artifacts, dict) else None
            )
            submission_dir = (
                resolve_path(submission_value, base_dir=manifest_path.parent, workspace_root=workspace_root)
                if submission_value
                else manifest_path.parent
            )
            agent_id = str(agent.get("agent_id", "")).strip() if isinstance(agent, dict) else ""
            run_label = (
                str(trace.get("run_label", "")).strip() if isinstance(trace, dict) else ""
            ) or manifest_path.parent.name
            entry_id = "::".join(
                [
                    label,
                    task_id,
                    run_type or "unknown_run_type",
                    agent_id or "unknown_agent",
                    run_label,
                ]
            )
            entries.append(
                MethodologyCalibrationEntry(
                    entry_id=entry_id,
                    corpus_label=label,
                    source_kind="run_submission",
                    task_id=task_id,
                    submission_dir=submission_dir,
                    run_type=run_type,
                    agent_id=agent_id,
                    run_label=run_label,
                    manifest_path=manifest_path,
                )
            )
    return entries


def discover_fixture_corpus_entries(
    config: dict[str, Any],
    *,
    config_dir: Path,
    workspace_root: Path,
) -> list[MethodologyCalibrationEntry]:
    entries: list[MethodologyCalibrationEntry] = []
    for fixture in config.get("fixtures", []):
        if not isinstance(fixture, dict):
            continue
        fixture_id = str(fixture.get("fixture_id", "")).strip()
        task_id = str(fixture.get("task_id", "")).strip()
        submission_value = fixture.get("submission_dir")
        if not fixture_id or not task_id or not submission_value:
            continue
        expected_rule_ids = tuple(
            str(value).strip()
            for value in fixture.get("expected_rule_ids", [])
            if str(value).strip()
        )
        entries.append(
            MethodologyCalibrationEntry(
                entry_id=f"fixture::{fixture_id}",
                corpus_label=str(fixture.get("corpus_label", "curated_fixtures")).strip()
                or "curated_fixtures",
                source_kind="curated_fixture",
                task_id=task_id,
                submission_dir=resolve_path(
                    submission_value,
                    base_dir=config_dir,
                    workspace_root=workspace_root,
                ),
                run_type=str(fixture.get("run_type", "fixture")).strip() or "fixture",
                agent_id=str(fixture.get("agent_id", fixture_id)).strip() or fixture_id,
                run_label=str(fixture.get("run_label", fixture_id)).strip() or fixture_id,
                fixture_id=fixture_id,
                expected_flagged=(
                    bool(fixture.get("expected_flagged"))
                    if fixture.get("expected_flagged") is not None
                    else None
                ),
                expected_rule_ids=expected_rule_ids,
                notes=str(fixture.get("notes", "")).strip(),
            )
        )
    return entries


def scan_methodology_calibration_entries(
    entries: list[MethodologyCalibrationEntry],
    *,
    tasks_root: str | Path = Path("tasks/pilot"),
) -> list[MethodologyCalibrationScan]:
    tasks_root_path = Path(tasks_root)
    cache: dict[str, dict[str, Any]] = {}
    scans: list[MethodologyCalibrationScan] = []
    for entry in entries:
        spec = cache.get(entry.task_id)
        if spec is None:
            spec = load_yaml(task_spec_path(entry.task_id, tasks_root=tasks_root_path))
            cache[entry.task_id] = spec
        result = scan_submission_methodology(
            entry.submission_dir,
            rules=methodology_rules_for_task(spec),
        )
        scans.append(
            MethodologyCalibrationScan(
                entry=entry,
                findings=[finding.as_dict() for finding in result.findings],
                scanned_files=result.scanned_files,
                skipped_files=result.skipped_files,
            )
        )
    return scans


def summarize_counts(
    scans: list[MethodologyCalibrationScan],
    *,
    workspace_root: Path,
) -> dict[str, Any]:
    corpus_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"entries": 0, "flagged_entries": 0, "clean_entries": 0, "findings": 0}
    )
    task_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"entries": 0, "flagged_entries": 0, "clean_entries": 0, "findings": 0}
    )
    run_type_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"entries": 0, "flagged_entries": 0, "clean_entries": 0, "findings": 0}
    )
    rule_counts: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"finding_count": 0, "flagged_entry_count": 0, "severity": ""}
    )
    severity_counts: dict[str, int] = defaultdict(int)
    entry_rows: list[dict[str, Any]] = []

    for scan in scans:
        entry = scan.entry
        bucket_values = [
            corpus_counts[entry.corpus_label],
            task_counts[entry.task_id],
            run_type_counts[entry.run_type or "unknown"],
        ]
        for bucket in bucket_values:
            bucket["entries"] += 1
            bucket["findings"] += scan.finding_count
            if scan.flagged:
                bucket["flagged_entries"] += 1
            else:
                bucket["clean_entries"] += 1

        seen_rules: set[str] = set()
        for finding in scan.findings:
            severity = finding.get("severity", "")
            rule_id = finding.get("rule_id", "")
            rule_counts[rule_id]["finding_count"] += 1
            rule_counts[rule_id]["severity"] = severity
            if rule_id not in seen_rules:
                rule_counts[rule_id]["flagged_entry_count"] += 1
                seen_rules.add(rule_id)
            severity_counts[severity] += 1

        entry_rows.append(
            {
                "entry_id": entry.entry_id,
                "corpus_label": entry.corpus_label,
                "source_kind": entry.source_kind,
                "task_id": entry.task_id,
                "run_type": entry.run_type,
                "agent_id": entry.agent_id,
                "run_label": entry.run_label,
                "submission_dir": relative_to_workspace(entry.submission_dir, workspace_root),
                "manifest_path": (
                    relative_to_workspace(entry.manifest_path, workspace_root)
                    if entry.manifest_path is not None
                    else ""
                ),
                "fixture_id": entry.fixture_id or "",
                "flagged": scan.flagged,
                "finding_count": scan.finding_count,
                "rule_ids": list(scan.rule_ids),
                "scanned_files": scan.scanned_files,
                "skipped_files": scan.skipped_files,
                "expected_flagged": entry.expected_flagged,
                "expected_rule_ids": list(entry.expected_rule_ids),
                "notes": entry.notes,
            }
        )

    return {
        "entry_count": len(scans),
        "flagged_entry_count": sum(1 for scan in scans if scan.flagged),
        "clean_entry_count": sum(1 for scan in scans if not scan.flagged),
        "finding_count": sum(scan.finding_count for scan in scans),
        "scanned_file_count": sum(scan.scanned_files for scan in scans),
        "skipped_file_count": sum(scan.skipped_files for scan in scans),
        "corpus_counts": dict(sorted(corpus_counts.items())),
        "task_counts": dict(sorted(task_counts.items())),
        "run_type_counts": dict(sorted(run_type_counts.items())),
        "rule_counts": dict(sorted(rule_counts.items())),
        "severity_counts": dict(sorted(severity_counts.items())),
        "entries": entry_rows,
    }


def evaluate_fixture_expectations(
    scans: list[MethodologyCalibrationScan],
    *,
    workspace_root: Path,
) -> dict[str, Any]:
    fixture_rows: list[dict[str, Any]] = []
    true_positive_count = 0
    true_negative_count = 0
    false_positive_count = 0
    false_negative_count = 0
    rule_expectation_match_count = 0
    rule_expectation_mismatch_count = 0

    for scan in scans:
        entry = scan.entry
        if entry.source_kind != "curated_fixture":
            continue
        expected_flagged = entry.expected_flagged
        if expected_flagged is None:
            continue

        actual_flagged = scan.flagged
        if expected_flagged and actual_flagged:
            confusion_label = "true_positive"
            true_positive_count += 1
        elif expected_flagged and not actual_flagged:
            confusion_label = "false_negative"
            false_negative_count += 1
        elif not expected_flagged and actual_flagged:
            confusion_label = "false_positive"
            false_positive_count += 1
        else:
            confusion_label = "true_negative"
            true_negative_count += 1

        expected_rules = set(entry.expected_rule_ids)
        actual_rules = set(scan.rule_ids)
        missing_expected_rules = sorted(expected_rules - actual_rules)
        matched_expected_rules = sorted(expected_rules & actual_rules)
        if missing_expected_rules:
            rule_expectation_status = "missing_expected_rules"
            rule_expectation_mismatch_count += 1
        else:
            rule_expectation_status = "matched"
            if expected_rules:
                rule_expectation_match_count += 1

        fixture_rows.append(
            {
                "fixture_id": entry.fixture_id or "",
                "task_id": entry.task_id,
                "submission_dir": relative_to_workspace(entry.submission_dir, workspace_root),
                "expected_flagged": expected_flagged,
                "actual_flagged": actual_flagged,
                "confusion_label": confusion_label,
                "expected_rule_ids": list(entry.expected_rule_ids),
                "actual_rule_ids": list(scan.rule_ids),
                "matched_expected_rules": matched_expected_rules,
                "missing_expected_rules": missing_expected_rules,
                "rule_expectation_status": rule_expectation_status,
                "finding_count": scan.finding_count,
                "notes": entry.notes,
            }
        )

    return {
        "fixture_count": len(fixture_rows),
        "true_positive_count": true_positive_count,
        "true_negative_count": true_negative_count,
        "false_positive_count": false_positive_count,
        "false_negative_count": false_negative_count,
        "rule_expectation_match_count": rule_expectation_match_count,
        "rule_expectation_mismatch_count": rule_expectation_mismatch_count,
        "fixtures": fixture_rows,
    }


def pick_review_focus_file(submission_dir: Path) -> str:
    preferred = ("notebook.ipynb", "model.py", "notebook.py", "writeup.md", "audit_note.md")
    for name in preferred:
        candidate = submission_dir / name
        if candidate.exists():
            return name
    files = sorted(path.relative_to(submission_dir) for path in submission_dir.rglob("*") if path.is_file())
    return str(files[0]) if files else ""


def select_clean_control_scans(
    scans: list[MethodologyCalibrationScan],
    *,
    per_group: int = 1,
) -> list[MethodologyCalibrationScan]:
    grouped: dict[tuple[str, str], list[MethodologyCalibrationScan]] = defaultdict(list)
    for scan in scans:
        if scan.flagged or scan.entry.source_kind != "run_submission":
            continue
        key = (scan.entry.task_id, scan.entry.run_type)
        grouped[key].append(scan)

    selected: list[MethodologyCalibrationScan] = []
    for key in sorted(grouped):
        candidates = sorted(
            grouped[key],
            key=lambda item: (
                item.entry.corpus_label,
                item.entry.agent_id,
                item.entry.run_label,
                item.entry.entry_id,
            ),
        )
        selected.extend(candidates[: max(per_group, 0)])
    return selected


def build_methodology_calibration_review_packet_rows(
    scans: list[MethodologyCalibrationScan],
    *,
    workspace_root: Path,
    clean_control_per_group: int = 1,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scan in scans:
        entry = scan.entry
        expected_fixture_status = (
            "should_flag"
            if entry.expected_flagged is True
            else "should_stay_clean"
            if entry.expected_flagged is False
            else ""
        )
        for finding_index, finding in enumerate(scan.findings, start=1):
            rows.append(
                {
                    "review_case_id": f"finding::{entry.entry_id}::{finding_index:03d}",
                    "review_type": "finding_review",
                    "calibration_target": "true_positive_or_false_positive_check",
                    "corpus_label": entry.corpus_label,
                    "source_kind": entry.source_kind,
                    "task_id": entry.task_id,
                    "run_type": entry.run_type,
                    "agent_id": entry.agent_id,
                    "run_label": entry.run_label,
                    "fixture_id": entry.fixture_id or "",
                    "entry_id": entry.entry_id,
                    "submission_dir": relative_to_workspace(entry.submission_dir, workspace_root),
                    "manifest_path": (
                        relative_to_workspace(entry.manifest_path, workspace_root)
                        if entry.manifest_path is not None
                        else ""
                    ),
                    "file": finding.get("file", ""),
                    "location": finding.get("location", ""),
                    "rule_id": finding.get("rule_id", ""),
                    "severity": finding.get("severity", ""),
                    "message": finding.get("message", ""),
                    "context": finding.get("context", ""),
                    "expected_fixture_status": expected_fixture_status,
                    "expected_rule_ids": ", ".join(entry.expected_rule_ids),
                    "review_status": "template",
                    "review_decision": "",
                    "review_notes": "",
                }
            )

    for scan in select_clean_control_scans(scans, per_group=clean_control_per_group):
        entry = scan.entry
        rows.append(
            {
                "review_case_id": f"clean::{entry.entry_id}",
                "review_type": "clean_control_review",
                "calibration_target": "true_negative_or_false_negative_check",
                "corpus_label": entry.corpus_label,
                "source_kind": entry.source_kind,
                "task_id": entry.task_id,
                "run_type": entry.run_type,
                "agent_id": entry.agent_id,
                "run_label": entry.run_label,
                "fixture_id": entry.fixture_id or "",
                "entry_id": entry.entry_id,
                "submission_dir": relative_to_workspace(entry.submission_dir, workspace_root),
                "manifest_path": (
                    relative_to_workspace(entry.manifest_path, workspace_root)
                    if entry.manifest_path is not None
                    else ""
                ),
                "file": pick_review_focus_file(entry.submission_dir),
                "location": "",
                "rule_id": "",
                "severity": "",
                "message": "Clean-control submission selected for manual false-negative review.",
                "context": "",
                "expected_fixture_status": "should_stay_clean_control",
                "expected_rule_ids": "",
                "review_status": "template",
                "review_decision": "",
                "review_notes": "",
            }
        )

    return rows


def write_review_packet_csv(rows: list[dict[str, Any]], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "review_case_id",
        "review_type",
        "calibration_target",
        "corpus_label",
        "source_kind",
        "task_id",
        "run_type",
        "agent_id",
        "run_label",
        "fixture_id",
        "entry_id",
        "submission_dir",
        "manifest_path",
        "file",
        "location",
        "rule_id",
        "severity",
        "message",
        "context",
        "expected_fixture_status",
        "expected_rule_ids",
        "review_status",
        "review_decision",
        "review_notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def render_methodology_calibration_summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Methodology Calibration Summary",
        "",
        f"- Corpus entry count: `{summary['counts']['entry_count']}`",
        f"- Flagged entry count: `{summary['counts']['flagged_entry_count']}`",
        f"- Clean entry count: `{summary['counts']['clean_entry_count']}`",
        f"- Total methodology findings: `{summary['counts']['finding_count']}`",
        f"- Scanned files: `{summary['counts']['scanned_file_count']}`",
        f"- Skipped files: `{summary['counts']['skipped_file_count']}`",
        f"- Clean-control review rows: `{summary['review_packet']['clean_control_row_count']}`",
        "",
    ]

    corpus_rows = [
        [label, values["entries"], values["flagged_entries"], values["clean_entries"], values["findings"]]
        for label, values in summary["counts"]["corpus_counts"].items()
    ]
    if corpus_rows:
        lines.extend(
            [
                "## Corpus Coverage",
                "",
                markdown_table(
                    ["Corpus", "Entries", "Flagged", "Clean", "Findings"],
                    corpus_rows,
                ),
                "",
            ]
        )

    task_rows = [
        [task_id, values["entries"], values["flagged_entries"], values["clean_entries"], values["findings"]]
        for task_id, values in summary["counts"]["task_counts"].items()
    ]
    if task_rows:
        lines.extend(
            [
                "## Task Coverage",
                "",
                markdown_table(
                    ["Task ID", "Entries", "Flagged", "Clean", "Findings"],
                    task_rows,
                ),
                "",
            ]
        )

    rule_rows = [
        [rule_id, values["severity"], values["finding_count"], values["flagged_entry_count"]]
        for rule_id, values in summary["counts"]["rule_counts"].items()
    ]
    if rule_rows:
        lines.extend(
            [
                "## Rule Counts",
                "",
                markdown_table(
                    ["Rule ID", "Severity", "Finding Count", "Flagged Entries"],
                    rule_rows,
                ),
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Rule Counts",
                "",
                "No methodology findings were detected in the scanned corpus.",
                "",
            ]
        )

    fixture_summary = summary["fixture_evaluation"]
    lines.extend(
        [
            "## Fixture Evaluation",
            "",
            f"- Fixture count: `{fixture_summary['fixture_count']}`",
            f"- True positives: `{fixture_summary['true_positive_count']}`",
            f"- False negatives: `{fixture_summary['false_negative_count']}`",
            f"- False positives: `{fixture_summary['false_positive_count']}`",
            f"- True negatives: `{fixture_summary['true_negative_count']}`",
            f"- Expected-rule matches: `{fixture_summary['rule_expectation_match_count']}`",
            f"- Expected-rule mismatches: `{fixture_summary['rule_expectation_mismatch_count']}`",
            "",
        ]
    )
    fixture_rows = [
        [
            row["fixture_id"],
            row["task_id"],
            row["confusion_label"],
            row["finding_count"],
            ", ".join(row["actual_rule_ids"]) or "-",
            ", ".join(row["missing_expected_rules"]) or "-",
        ]
        for row in fixture_summary["fixtures"]
    ]
    if fixture_rows:
        lines.extend(
            [
                markdown_table(
                    [
                        "Fixture ID",
                        "Task ID",
                        "Confusion Label",
                        "Finding Count",
                        "Actual Rule IDs",
                        "Missing Expected Rules",
                    ],
                    fixture_rows,
                ),
                "",
            ]
        )

    lines.extend(
        [
            "## Next Review Action",
            "",
            "Fill `audits/methodology_calibration/reviews/calibration_review_packet.csv` to label finding rows as true or false positives and clean-control rows as true or false negatives.",
            "",
        ]
    )
    return "\n".join(lines)


def build_methodology_calibration_workflow(
    *,
    config_path: str | Path = DEFAULT_METHODOLOGY_CALIBRATION_CONFIG_PATH,
    tasks_root: str | Path = Path("tasks/pilot"),
    review_packet_path: str | Path = DEFAULT_METHODOLOGY_CALIBRATION_REVIEW_PACKET_PATH,
    summary_json_path: str | Path = DEFAULT_METHODOLOGY_CALIBRATION_SUMMARY_JSON_PATH,
    summary_markdown_path: str | Path = DEFAULT_METHODOLOGY_CALIBRATION_SUMMARY_MARKDOWN_PATH,
    clean_control_per_group: int = 1,
    workspace_root: str | Path = Path("."),
) -> dict[str, Any]:
    workspace_root_path = Path(workspace_root).resolve()
    config_file = Path(config_path).resolve()
    config_dir = config_file.parent
    tasks_root_path = Path(tasks_root).resolve()
    config = load_methodology_calibration_config(config_file)
    entries = discover_run_corpus_entries(
        config,
        config_dir=config_dir,
        workspace_root=workspace_root_path,
    ) + discover_fixture_corpus_entries(
        config,
        config_dir=config_dir,
        workspace_root=workspace_root_path,
    )
    scans = scan_methodology_calibration_entries(entries, tasks_root=tasks_root_path)
    counts = summarize_counts(scans, workspace_root=workspace_root_path)
    fixture_evaluation = evaluate_fixture_expectations(scans, workspace_root=workspace_root_path)
    review_packet_rows = build_methodology_calibration_review_packet_rows(
        scans,
        workspace_root=workspace_root_path,
        clean_control_per_group=clean_control_per_group,
    )
    review_packet = {
        "row_count": len(review_packet_rows),
        "finding_row_count": sum(1 for row in review_packet_rows if row["review_type"] == "finding_review"),
        "clean_control_row_count": sum(
            1 for row in review_packet_rows if row["review_type"] == "clean_control_review"
        ),
    }
    summary = {
        "config_path": relative_to_workspace(config_file, workspace_root_path),
        "tasks_root": relative_to_workspace(tasks_root_path, workspace_root_path),
        "counts": counts,
        "fixture_evaluation": fixture_evaluation,
        "review_packet": review_packet,
    }

    summary_json = Path(summary_json_path).resolve()
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary_markdown = Path(summary_markdown_path).resolve()
    summary_markdown.parent.mkdir(parents=True, exist_ok=True)
    summary_markdown.write_text(
        render_methodology_calibration_summary_markdown(summary),
        encoding="utf-8",
    )

    review_packet_csv = write_review_packet_csv(review_packet_rows, Path(review_packet_path).resolve())
    return {
        "summary_json_path": summary_json,
        "summary_markdown_path": summary_markdown,
        "review_packet_path": review_packet_csv,
        "summary": summary,
    }
