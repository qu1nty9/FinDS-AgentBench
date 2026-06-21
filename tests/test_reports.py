import csv
from pathlib import Path

from finds_agentbench.reports import (
    load_result_rows,
    results_to_markdown,
    write_results_csv,
    write_results_markdown,
)
from finds_agentbench.runs import build_run_manifest, write_run_manifest


def write_manifest(tmp_path: Path, *, task_id: str, agent_id: str, score: float) -> Path:
    submission_dir = tmp_path / task_id / agent_id / "submission"
    submission_dir.mkdir(parents=True)
    (submission_dir / "predictions.csv").write_text(
        "row_id,prediction,probability\nrow_1,1,0.8\n",
        encoding="utf-8",
    )
    manifest = build_run_manifest(
        task_id=task_id,
        agent_id=agent_id,
        agent_version="0.1.0",
        submission_dir=submission_dir,
        run_id=f"{task_id}_{agent_id}",
        scores={
            "overall_score": score,
            "balanced_accuracy": score,
            "execution_success": 1.0,
        },
        validations={"artifact_validation": {"ok": True}},
    )
    output = tmp_path / task_id / agent_id / "run_manifest.json"
    write_run_manifest(manifest, output)
    return output


def test_load_result_rows_flattens_scores_and_validations(tmp_path: Path):
    write_manifest(
        tmp_path,
        task_id="synthetic_market_direction_v0",
        agent_id="momentum_baseline",
        score=0.54,
    )

    rows = load_result_rows(tmp_path, strict=True)

    assert len(rows) == 1
    row = rows[0]
    assert row["task_id"] == "synthetic_market_direction_v0"
    assert row["agent_id"] == "momentum_baseline"
    assert row["score.overall_score"] == 0.54
    assert row["score.execution_success"] == 1.0
    assert row["validation.artifact_validation.ok"] is True
    assert row["artifact_file_count"] == 1
    assert row["manifest_valid"] is True


def test_write_results_csv_and_markdown(tmp_path: Path):
    write_manifest(tmp_path, task_id="task_a", agent_id="agent_a", score=0.5)
    write_manifest(tmp_path, task_id="task_b", agent_id="agent_b", score=0.7)
    rows = load_result_rows(tmp_path, strict=True)
    csv_output = tmp_path / "report.csv"
    markdown_output = tmp_path / "report.md"

    write_results_csv(rows, csv_output)
    write_results_markdown(
        rows,
        markdown_output,
        columns=["task_id", "agent_id", "score.overall_score"],
    )

    with csv_output.open("r", encoding="utf-8", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    markdown = markdown_output.read_text(encoding="utf-8")

    assert len(csv_rows) == 2
    assert "score.overall_score" in csv_rows[0]
    assert "| task_id | agent_id | score.overall_score |" in markdown
    assert "| task_a | agent_a | 0.5 |" in markdown


def test_results_to_markdown_handles_empty_values():
    markdown = results_to_markdown(
        [{"task_id": "task_a", "agent_id": "agent_a"}],
        columns=["task_id", "agent_id", "score.overall_score"],
    )

    assert "| task_a | agent_a |  |" in markdown

