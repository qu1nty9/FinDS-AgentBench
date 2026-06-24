import csv
import json
from pathlib import Path

from finds_agentbench.methodology_calibration import (
    build_methodology_calibration_workflow,
    discover_fixture_corpus_entries,
    discover_run_corpus_entries,
    load_methodology_calibration_config,
)
from finds_agentbench.runs import build_run_manifest, write_run_manifest


def write_json_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_task_spec(path: Path, *, target_name: str, horizon: str, forbidden_columns: list[str]) -> None:
    write_json_yaml(
        path,
        {
            "target": {
                "name": target_name,
                "horizon": horizon,
                "definition": "Test target definition.",
                "label_construction": "Test label construction.",
            },
            "information_set": {
                "prediction_timestamp": "End of day t before t+1 target is known.",
            },
            "splits": {
                "embargo_or_gap": horizon,
            },
            "leakage_checks": {
                "forbidden_columns": forbidden_columns,
            },
        },
    )


def write_clean_submission(path: Path, *, code: str = "print('clean')\n") -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "notebook.ipynb").write_text(
        json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "execution_count": None,
                        "id": "cell-1",
                        "metadata": {},
                        "outputs": [],
                        "source": [code],
                    }
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (path / "writeup.md").write_text("clean writeup\n", encoding="utf-8")


def write_run_submission(
    workspace_root: Path,
    *,
    run_root: Path,
    task_id: str,
    agent_id: str,
    run_label: str,
    run_type: str = "baseline",
) -> Path:
    submission_dir = run_root / task_id / agent_id / run_label
    write_clean_submission(submission_dir)
    manifest = build_run_manifest(
        task_id=task_id,
        agent_id=agent_id,
        agent_version="0.1.0",
        submission_dir=str(submission_dir.relative_to(workspace_root)),
        run_type=run_type,
    )
    write_run_manifest(manifest, submission_dir / "run_manifest.json")
    return submission_dir


def write_config(config_path: Path, run_root: Path, fixture_path: Path) -> None:
    write_json_yaml(
        config_path,
        {
            "run_corpora": [
                {
                    "label": "pilot_baselines",
                    "root": str(run_root),
                }
            ],
            "fixtures": [
                {
                    "fixture_id": "front_end_future_join_positive",
                    "task_id": "front_end_spread_widening_v0",
                    "submission_dir": str(fixture_path),
                    "expected_flagged": True,
                    "expected_rule_ids": ["future_aligned_merge_join"],
                    "notes": "Short-horizon future merge fixture.",
                }
            ],
        },
    )


def test_discover_methodology_calibration_entries(tmp_path: Path):
    workspace_root = tmp_path
    tasks_root = workspace_root / "tasks" / "pilot"
    write_task_spec(
        tasks_root / "front_end_spread_widening_v0.yaml",
        target_name="next_day_front_end_widening",
        horizon="1 business day",
        forbidden_columns=["next_day_front_end_change_bp"],
    )
    run_root = workspace_root / "runs" / "suites" / "pilot_baselines_v0"
    write_run_submission(
        workspace_root,
        run_root=run_root,
        task_id="front_end_spread_widening_v0",
        agent_id="clean_baseline",
        run_label="run_001",
    )
    fixture_dir = workspace_root / "audits" / "methodology_calibration" / "fixtures" / "future_join"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    (fixture_dir / "model.py").write_text(
        'joined = features.merge(next_day_policy_frame, on="date", how="left")\n',
        encoding="utf-8",
    )
    config_path = workspace_root / "audits" / "methodology_calibration" / "corpus.yaml"
    write_config(config_path, run_root, fixture_dir)

    config = load_methodology_calibration_config(config_path)
    run_entries = discover_run_corpus_entries(
        config,
        config_dir=config_path.parent,
        workspace_root=workspace_root,
    )
    fixture_entries = discover_fixture_corpus_entries(
        config,
        config_dir=config_path.parent,
        workspace_root=workspace_root,
    )

    assert len(run_entries) == 1
    assert run_entries[0].source_kind == "run_submission"
    assert run_entries[0].task_id == "front_end_spread_widening_v0"
    assert len(fixture_entries) == 1
    assert fixture_entries[0].source_kind == "curated_fixture"
    assert fixture_entries[0].expected_rule_ids == ("future_aligned_merge_join",)


def test_build_methodology_calibration_workflow_writes_summary_and_review_packet(tmp_path: Path):
    workspace_root = tmp_path
    tasks_root = workspace_root / "tasks" / "pilot"
    write_task_spec(
        tasks_root / "front_end_spread_widening_v0.yaml",
        target_name="next_day_front_end_widening",
        horizon="1 business day",
        forbidden_columns=["next_day_front_end_change_bp"],
    )
    run_root = workspace_root / "runs" / "suites" / "pilot_baselines_v0"
    write_run_submission(
        workspace_root,
        run_root=run_root,
        task_id="front_end_spread_widening_v0",
        agent_id="clean_baseline",
        run_label="run_001",
    )
    write_run_submission(
        workspace_root,
        run_root=run_root,
        task_id="front_end_spread_widening_v0",
        agent_id="clean_baseline",
        run_label="run_002",
    )
    fixture_dir = workspace_root / "audits" / "methodology_calibration" / "fixtures" / "future_join"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    (fixture_dir / "model.py").write_text(
        'joined = features.merge(next_day_policy_frame, on="date", how="left")\n',
        encoding="utf-8",
    )
    config_path = workspace_root / "audits" / "methodology_calibration" / "corpus.yaml"
    write_config(config_path, run_root, fixture_dir)

    result = build_methodology_calibration_workflow(
        config_path=config_path,
        tasks_root=tasks_root,
        review_packet_path=workspace_root
        / "audits"
        / "methodology_calibration"
        / "reviews"
        / "calibration_review_packet.csv",
        summary_json_path=workspace_root
        / "audits"
        / "methodology_calibration"
        / "reports"
        / "summary.json",
        summary_markdown_path=workspace_root
        / "audits"
        / "methodology_calibration"
        / "reports"
        / "summary.md",
        clean_control_per_group=1,
        workspace_root=workspace_root,
    )

    summary = result["summary"]
    assert summary["counts"]["entry_count"] == 3
    assert summary["counts"]["flagged_entry_count"] == 1
    assert summary["counts"]["clean_entry_count"] == 2
    assert summary["fixture_evaluation"]["true_positive_count"] == 1
    assert summary["fixture_evaluation"]["false_negative_count"] == 0
    assert summary["review_packet"]["finding_row_count"] == 1
    assert summary["review_packet"]["clean_control_row_count"] == 1

    with result["review_packet_path"].open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert {row["review_type"] for row in rows} == {
        "finding_review",
        "clean_control_review",
    }
    clean_control_row = next(row for row in rows if row["review_type"] == "clean_control_review")
    assert clean_control_row["file"] == "notebook.ipynb"

    summary_json = json.loads(result["summary_json_path"].read_text(encoding="utf-8"))
    assert summary_json["counts"]["entry_count"] == 3
    assert "Methodology Calibration Summary" in result["summary_markdown_path"].read_text(
        encoding="utf-8"
    )
