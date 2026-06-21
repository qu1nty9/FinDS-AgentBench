import csv
import json
import sys
from pathlib import Path

from finds_agentbench.pipelines import (
    run_pilot_baseline_suite,
    run_synthetic_market_baseline_suite,
    run_synthetic_market_agent_command,
    run_synthetic_market_agent_command_suite,
    run_synthetic_event_response_agent_command_suite,
    run_synthetic_event_response_rule_pipeline,
    run_synthetic_market_logistic_pipeline,
    run_synthetic_market_momentum_pipeline,
)
from finds_agentbench.runs import load_run_manifest, validate_run_manifest


def test_run_synthetic_market_momentum_pipeline(tmp_path: Path):
    run_dir = tmp_path / "runs" / "synthetic_market_direction_v0" / "momentum_baseline"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_synthetic_market_momentum_pipeline(
        data_output_dir=tmp_path / "data" / "raw",
        private_dir=tmp_path / "data" / "private",
        run_dir=run_dir,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command="test pipeline",
    )

    assert result.status == "completed"
    assert (run_dir / "predictions.csv").exists()
    assert (run_dir / "writeup.md").exists()
    assert (run_dir / "notebook.ipynb").exists()
    assert result.score_path.exists()
    assert result.validation_path.exists()
    assert result.manifest_path.exists()
    assert report_csv.exists()
    assert report_md.exists()
    assert summary_csv.exists()
    assert summary_md.exists()

    score = json.loads(result.score_path.read_text(encoding="utf-8"))
    validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
    manifest = load_run_manifest(result.manifest_path)

    assert score["execution_success"] == 1.0
    assert validation["ok"] is True
    assert validation["methodology_findings"] == []
    assert validate_run_manifest(manifest).ok
    assert manifest["scores"]["overall_score"] == score["overall_score"]
    assert "score.overall_score" in report_md.read_text(encoding="utf-8")
    assert "score.overall_score.mean" in summary_md.read_text(encoding="utf-8")


def test_run_synthetic_market_logistic_pipeline(tmp_path: Path):
    run_dir = tmp_path / "runs" / "synthetic_market_direction_v0" / "logistic_baseline"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_synthetic_market_logistic_pipeline(
        data_output_dir=tmp_path / "data" / "raw",
        private_dir=tmp_path / "data" / "private",
        run_dir=run_dir,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command="test logistic pipeline",
    )

    assert result.status == "completed"
    assert (run_dir / "predictions.csv").exists()
    assert (run_dir / "writeup.md").exists()
    assert (run_dir / "notebook.ipynb").exists()
    assert (run_dir / "baseline_metadata.json").exists()

    metadata = json.loads((run_dir / "baseline_metadata.json").read_text(encoding="utf-8"))
    score = json.loads(result.score_path.read_text(encoding="utf-8"))
    validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
    manifest = load_run_manifest(result.manifest_path)

    assert 0.0 <= metadata["selected_threshold"] <= 1.0
    assert metadata["train_rows"] > 0
    assert metadata["public_validation_rows"] > 0
    assert score["execution_success"] == 1.0
    assert validation["ok"] is True
    assert validation["methodology_findings"] == []
    assert validate_run_manifest(manifest).ok
    assert manifest["agent"]["agent_id"] == "logistic_regression_baseline"
    assert summary_csv.exists()
    assert summary_md.exists()


def test_repeated_momentum_pipeline_writes_distinct_runs_and_summary(tmp_path: Path):
    runs_root = tmp_path / "runs"
    run_dir = runs_root / "synthetic_market_direction_v0" / "momentum_baseline"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    for offset, seed in enumerate((11, 12), start=1):
        label = f"repeat_{offset:03d}_seed_{seed}"
        result = run_synthetic_market_momentum_pipeline(
            seed=seed,
            data_output_dir=tmp_path / "data" / "raw" / label,
            private_dir=tmp_path / "data" / "private" / label,
            run_dir=run_dir,
            run_label=label,
            repeat_index=offset,
            repeat_count=2,
            runs_root=runs_root,
            report_csv_path=report_csv,
            report_markdown_path=report_md,
            summary_csv_path=summary_csv,
            summary_markdown_path=summary_md,
            execute_notebook=False,
            command="test repeated momentum pipeline",
        )
        assert result.status == "completed"

    with report_csv.open("r", encoding="utf-8", newline="") as handle:
        result_rows = list(csv.DictReader(handle))
    with summary_csv.open("r", encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))

    assert len(result_rows) == 2
    assert sorted(row["trace.run_label"] for row in result_rows) == [
        "repeat_001_seed_11",
        "repeat_002_seed_12",
    ]
    assert len(summary_rows) == 1
    assert summary_rows[0]["run_count"] == "2"
    assert summary_rows[0]["completed_count"] == "2"
    assert summary_rows[0]["score.overall_score.count"] == "2"
    assert "score.overall_score.std" in summary_md.read_text(encoding="utf-8")


def test_synthetic_market_baseline_suite_runs_all_baselines_with_repeats(tmp_path: Path):
    runs_root = tmp_path / "runs"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_synthetic_market_baseline_suite(
        seed=31,
        repeat=2,
        run_label_prefix="suite",
        data_output_dir=tmp_path / "data" / "raw",
        private_dir=tmp_path / "data" / "private",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command="test baseline suite",
    )

    with report_csv.open("r", encoding="utf-8", newline="") as handle:
        result_rows = list(csv.DictReader(handle))
    with summary_csv.open("r", encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))

    assert result.status == "completed"
    assert len(result.results) == 4
    assert len(result_rows) == 4
    assert len(summary_rows) == 2
    assert sorted(row["agent_id"] for row in summary_rows) == [
        "logistic_regression_baseline",
        "momentum_baseline",
    ]
    assert {row["run_count"] for row in summary_rows} == {"2"}
    assert {row["score.overall_score.count"] for row in summary_rows} == {"2"}
    assert report_md.exists()
    assert "score.overall_score.std" in summary_md.read_text(encoding="utf-8")


def test_synthetic_market_agent_command_pipeline_captures_artifacts(tmp_path: Path):
    agent_script = tmp_path / "dummy_agent.py"
    agent_script.write_text(
        """
import csv
import json
import os
from pathlib import Path

if "FINDS_ANSWER_KEY_PATH" in os.environ:
    raise SystemExit("private answer key leaked to agent env")

features_path = Path(os.environ["FINDS_HOLDOUT_FEATURES_PATH"])
submission_dir = Path(os.environ["FINDS_SUBMISSION_DIR"])
submission_dir.mkdir(parents=True, exist_ok=True)

with features_path.open("r", encoding="utf-8", newline="") as source:
    rows = list(csv.DictReader(source))

with (submission_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=["row_id", "prediction", "probability"])
    writer.writeheader()
    for row in rows:
        writer.writerow({"row_id": row["row_id"], "prediction": 1, "probability": 0.51})

(submission_dir / "writeup.md").write_text(
    "Dummy agent submission using public holdout features only.\\n",
    encoding="utf-8",
)
(submission_dir / "notebook.ipynb").write_text(
    json.dumps({
        "cells": [],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }),
    encoding="utf-8",
)
print(f"wrote {len(rows)} predictions")
""".lstrip(),
        encoding="utf-8",
    )
    runs_root = tmp_path / "runs"
    run_dir = runs_root / "synthetic_market_direction_v0" / "dummy_agent"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_synthetic_market_agent_command(
        agent_id="dummy_agent",
        agent_version="0.0.1",
        agent_command=[sys.executable, str(agent_script)],
        seed=41,
        data_output_dir=tmp_path / "data" / "raw",
        private_dir=tmp_path / "data" / "private",
        run_dir=run_dir,
        run_label="agent_001",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command_timeout_seconds=60,
    )

    manifest = load_run_manifest(result.manifest_path)
    score = json.loads(result.score_path.read_text(encoding="utf-8"))
    validation = json.loads(result.validation_path.read_text(encoding="utf-8"))

    assert result.status == "completed"
    assert score["execution_success"] == 1.0
    assert validation["ok"] is True
    assert validate_run_manifest(manifest).ok
    assert manifest["run_type"] == "agent"
    assert manifest["agent"]["agent_id"] == "dummy_agent"
    assert manifest["commands"][0]["exit_code"] == 0
    assert manifest["commands"][0]["timed_out"] is False
    assert (result.run_dir / "logs" / "stdout.txt").exists()
    assert "wrote" in (result.run_dir / "logs" / "stdout.txt").read_text(encoding="utf-8")
    assert "FINDS_ANSWER_KEY_PATH" not in manifest["commands"][0]["command"]

    with summary_csv.open("r", encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))

    assert len(summary_rows) == 1
    assert summary_rows[0]["agent_id"] == "dummy_agent"
    assert summary_rows[0]["run_type"] == "agent"
    assert summary_rows[0]["run_count"] == "1"
    assert report_md.exists()
    assert summary_md.exists()


def test_synthetic_market_agent_command_suite_repeats_agent_runs(tmp_path: Path):
    agent_script = tmp_path / "suite_agent.py"
    agent_script.write_text(
        """
import csv
import json
import os
from pathlib import Path

features_path = Path(os.environ["FINDS_HOLDOUT_FEATURES_PATH"])
submission_dir = Path(os.environ["FINDS_SUBMISSION_DIR"])
submission_dir.mkdir(parents=True, exist_ok=True)

with features_path.open("r", encoding="utf-8", newline="") as source:
    rows = list(csv.DictReader(source))

with (submission_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=["row_id", "prediction", "probability"])
    writer.writeheader()
    for row in rows:
        writer.writerow({"row_id": row["row_id"], "prediction": 1, "probability": 0.51})

(submission_dir / "writeup.md").write_text("Repeated dummy agent.\\n", encoding="utf-8")
(submission_dir / "notebook.ipynb").write_text(
    json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}),
    encoding="utf-8",
)
print(os.environ["FINDS_RUN_SEED"])
""".lstrip(),
        encoding="utf-8",
    )
    runs_root = tmp_path / "runs"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_synthetic_market_agent_command_suite(
        agent_id="suite_agent",
        agent_version="0.0.1",
        agent_command=[sys.executable, str(agent_script)],
        seed=51,
        repeat=2,
        run_label_prefix="agent_suite",
        data_output_dir=tmp_path / "data" / "raw",
        private_dir=tmp_path / "data" / "private",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command_timeout_seconds=60,
    )

    with report_csv.open("r", encoding="utf-8", newline="") as handle:
        result_rows = list(csv.DictReader(handle))
    with summary_csv.open("r", encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))

    assert result.status == "completed"
    assert len(result.results) == 2
    assert len(result_rows) == 2
    assert sorted(row["trace.run_label"] for row in result_rows) == [
        "agent_suite_001_seed_51",
        "agent_suite_002_seed_52",
    ]
    assert {row["run_type"] for row in result_rows} == {"agent"}
    assert len(summary_rows) == 1
    assert summary_rows[0]["agent_id"] == "suite_agent"
    assert summary_rows[0]["run_count"] == "2"
    assert summary_rows[0]["score.overall_score.count"] == "2"
    assert report_md.exists()
    assert summary_md.exists()


def test_run_synthetic_event_response_rule_pipeline(tmp_path: Path):
    run_dir = tmp_path / "runs" / "synthetic_event_response_v0" / "event_rule_baseline"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_synthetic_event_response_rule_pipeline(
        data_output_dir=tmp_path / "data" / "raw",
        private_dir=tmp_path / "data" / "private",
        run_dir=run_dir,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command="test event rule pipeline",
    )

    assert result.status == "completed"
    assert (run_dir / "predictions.csv").exists()
    assert (run_dir / "writeup.md").exists()
    assert (run_dir / "notebook.ipynb").exists()

    score = json.loads(result.score_path.read_text(encoding="utf-8"))
    validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
    manifest = load_run_manifest(result.manifest_path)

    assert score["task_id"] == "synthetic_event_response_v0"
    assert score["execution_success"] == 1.0
    assert validation["ok"] is True
    assert validation["methodology_findings"] == []
    assert validate_run_manifest(manifest).ok
    assert manifest["task_id"] == "synthetic_event_response_v0"
    assert manifest["agent"]["agent_id"] == "event_rule_baseline"
    assert summary_csv.exists()
    assert "synthetic_event_response_v0" in summary_md.read_text(encoding="utf-8")


def test_pilot_baseline_suite_runs_all_implemented_baselines(tmp_path: Path):
    runs_root = tmp_path / "runs"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_pilot_baseline_suite(
        market_seed=91,
        event_seed=101,
        repeat=2,
        run_label_prefix="pilot_suite",
        market_data_output_dir=tmp_path / "data" / "market" / "raw",
        market_private_dir=tmp_path / "data" / "market" / "private",
        event_data_output_dir=tmp_path / "data" / "event" / "raw",
        event_private_dir=tmp_path / "data" / "event" / "private",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command="test pilot baseline suite",
    )

    with report_csv.open("r", encoding="utf-8", newline="") as handle:
        result_rows = list(csv.DictReader(handle))
    with summary_csv.open("r", encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))

    assert result.status == "completed"
    assert len(result.results) == 6
    assert len(result_rows) == 6
    assert len(summary_rows) == 3
    assert {row["task_id"] for row in result_rows} == {
        "synthetic_event_response_v0",
        "synthetic_market_direction_v0",
    }
    assert sorted(row["agent_id"] for row in summary_rows) == [
        "event_rule_baseline",
        "logistic_regression_baseline",
        "momentum_baseline",
    ]
    assert {row["run_count"] for row in summary_rows} == {"2"}
    assert {row["score.overall_score.count"] for row in summary_rows} == {"2"}
    assert report_md.exists()
    assert "synthetic_event_response_v0" in summary_md.read_text(encoding="utf-8")
    assert "synthetic_market_direction_v0" in summary_md.read_text(encoding="utf-8")


def test_synthetic_event_response_agent_command_suite_repeats_agent_runs(tmp_path: Path):
    agent_script = tmp_path / "event_agent.py"
    agent_script.write_text(
        """
import csv
import json
import os
from pathlib import Path

features_path = Path(os.environ["FINDS_HOLDOUT_FEATURES_PATH"])
submission_dir = Path(os.environ["FINDS_SUBMISSION_DIR"])
submission_dir.mkdir(parents=True, exist_ok=True)

with features_path.open("r", encoding="utf-8", newline="") as source:
    rows = list(csv.DictReader(source))

with (submission_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=["row_id", "prediction", "probability"])
    writer.writeheader()
    for row in rows:
        probability = 0.65 if float(row["event_surprise"]) >= 0 else 0.35
        writer.writerow({
            "row_id": row["row_id"],
            "prediction": 1 if probability >= 0.5 else 0,
            "probability": probability,
        })

(submission_dir / "writeup.md").write_text("Repeated event dummy agent.\\n", encoding="utf-8")
(submission_dir / "notebook.ipynb").write_text(
    json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}),
    encoding="utf-8",
)
print(os.environ["FINDS_TASK_ID"])
""".lstrip(),
        encoding="utf-8",
    )
    runs_root = tmp_path / "runs"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_synthetic_event_response_agent_command_suite(
        agent_id="event_suite_agent",
        agent_version="0.0.1",
        agent_command=[sys.executable, str(agent_script)],
        seed=71,
        repeat=2,
        run_label_prefix="event_agent",
        data_output_dir=tmp_path / "data" / "raw",
        private_dir=tmp_path / "data" / "private",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command_timeout_seconds=60,
    )

    with report_csv.open("r", encoding="utf-8", newline="") as handle:
        result_rows = list(csv.DictReader(handle))
    with summary_csv.open("r", encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))

    assert result.status == "completed"
    assert len(result.results) == 2
    assert len(result_rows) == 2
    assert {row["task_id"] for row in result_rows} == {"synthetic_event_response_v0"}
    assert {row["run_type"] for row in result_rows} == {"agent"}
    assert sorted(row["trace.run_label"] for row in result_rows) == [
        "event_agent_001_seed_71",
        "event_agent_002_seed_72",
    ]
    assert len(summary_rows) == 1
    assert summary_rows[0]["agent_id"] == "event_suite_agent"
    assert summary_rows[0]["run_count"] == "2"
    assert summary_rows[0]["score.overall_score.count"] == "2"
    assert report_md.exists()
    assert summary_md.exists()
