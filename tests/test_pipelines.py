import csv
import json
import sys
from pathlib import Path

from finds_agentbench.pipelines import (
    AgentSuiteResult,
    BaselineSuiteResult,
    run_front_end_spread_widening_v0_agent_command,
    run_front_end_spread_widening_v0_agent_command_suite,
    run_front_end_spread_widening_v0_baseline_suite,
    run_front_end_spread_widening_v0_random_forest_pipeline,
    run_pilot_agent_suite,
    run_pilot_baseline_suite,
    run_pilot_protocol,
    run_synthetic_market_baseline_suite,
    run_synthetic_market_agent_command,
    run_synthetic_market_agent_command_suite,
    run_synthetic_event_response_agent_command_suite,
    run_synthetic_event_response_rule_pipeline,
    run_usd_broad_direction_v0_agent_command,
    run_usd_broad_direction_v0_agent_command_suite,
    run_usd_broad_direction_v0_baseline_suite,
    run_usd_broad_direction_v0_random_forest_pipeline,
    run_yield_curve_10y3mo_steepening_agent_command,
    run_yield_curve_10y3mo_steepening_agent_command_suite,
    run_yield_curve_10y3mo_steepening_baseline_suite,
    run_yield_curve_10y3mo_steepening_random_forest_pipeline,
    run_yield_curve_10y2y_steepening_agent_command,
    run_yield_curve_10y2y_steepening_agent_command_suite,
    run_yield_curve_10y2y_steepening_baseline_suite,
    run_yield_curve_10y2y_steepening_random_forest_pipeline,
    run_yield_direction_treasury10y_agent_command,
    run_yield_direction_treasury10y_agent_command_suite,
    run_yield_direction_treasury10y_baseline_suite,
    run_yield_direction_treasury10y_random_forest_pipeline,
    run_synthetic_market_logistic_pipeline,
    run_synthetic_market_momentum_pipeline,
)
from finds_agentbench.runs import load_run_manifest, validate_run_manifest
from tests.treasury_test_utils import mock_treasury_source_frame, mock_usd_broad_source_frame


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


def test_research_sweep_env_agent_selects_market_candidate_and_records_ranking(tmp_path: Path):
    agent_script = Path("agents/examples/research_sweep_env_agent.py").resolve()
    runs_root = tmp_path / "runs"
    run_dir = runs_root / "synthetic_market_direction_v0" / "market_research_sweep_env_agent"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_synthetic_market_agent_command(
        agent_id="market_research_sweep_env_agent",
        agent_version="0.2.0",
        agent_command=[sys.executable, str(agent_script)],
        seed=61,
        data_output_dir=tmp_path / "data" / "raw",
        private_dir=tmp_path / "data" / "private",
        run_dir=run_dir,
        run_label="market_sweep_001",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command_timeout_seconds=60,
    )

    manifest = load_run_manifest(result.manifest_path)
    metadata = json.loads((result.run_dir / "baseline_metadata.json").read_text(encoding="utf-8"))
    writeup = (result.run_dir / "writeup.md").read_text(encoding="utf-8")
    stdout = (result.run_dir / "logs" / "stdout.txt").read_text(encoding="utf-8")

    assert result.status == "completed"
    assert manifest["run_type"] == "agent"
    assert manifest["agent"]["agent_id"] == "market_research_sweep_env_agent"
    assert metadata["agent_family"] == "research_sweep_env_agent"
    assert metadata["task_id"] == "synthetic_market_direction_v0"
    assert metadata["selected_candidate_id"] in {
        "logistic_regression_baseline",
        "momentum_baseline",
    }
    assert len(metadata["candidate_ranking"]) == 2
    assert metadata["candidate_ranking"][0]["candidate_id"] == metadata["selected_candidate_id"]
    assert {
        candidate["candidate_id"] for candidate in metadata["candidate_ranking"]
    } == {"logistic_regression_baseline", "momentum_baseline"}
    assert all(
        candidate["public_validation_balanced_accuracy"] >= 0.0
        for candidate in metadata["candidate_ranking"]
    )
    assert "Candidate Leaderboard" in writeup
    assert "public_validation_balanced_accuracy" in writeup
    assert "selected " in stdout
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


def test_run_yield_direction_treasury10y_random_forest_pipeline(tmp_path: Path):
    run_dir = tmp_path / "runs" / "yield_direction_treasury10y_v0" / "random_forest_baseline"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_yield_direction_treasury10y_random_forest_pipeline(
        data_output_dir=tmp_path / "data" / "treasury" / "raw",
        private_dir=tmp_path / "data" / "treasury" / "private",
        run_dir=run_dir,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command="test treasury random forest pipeline",
        source_frame=mock_treasury_source_frame(),
        snapshot_date="2026-06-21",
    )

    assert result.status == "completed"
    assert (run_dir / "predictions.csv").exists()
    assert (run_dir / "writeup.md").exists()
    assert (run_dir / "notebook.ipynb").exists()
    assert (run_dir / "baseline_metadata.json").exists()

    score = json.loads(result.score_path.read_text(encoding="utf-8"))
    validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
    manifest = load_run_manifest(result.manifest_path)

    assert score["task_id"] == "yield_direction_treasury10y_v0"
    assert score["execution_success"] == 1.0
    assert validation["ok"] is True
    assert validation["methodology_findings"] == []
    assert validate_run_manifest(manifest).ok
    assert manifest["task_id"] == "yield_direction_treasury10y_v0"
    assert manifest["agent"]["agent_id"] == "random_forest_baseline"
    assert summary_csv.exists()
    assert "yield_direction_treasury10y_v0" in summary_md.read_text(encoding="utf-8")


def test_run_yield_direction_treasury10y_agent_command(tmp_path: Path):
    agent_script = tmp_path / "treasury_agent.py"
    agent_script.write_text(
        """
import csv
import json
import os
from pathlib import Path

train_public_path = Path(os.environ["FINDS_TRAIN_PUBLIC_PATH"])
features_path = Path(os.environ["FINDS_HOLDOUT_FEATURES_PATH"])
submission_dir = Path(os.environ["FINDS_SUBMISSION_DIR"])
submission_dir.mkdir(parents=True, exist_ok=True)

if "FINDS_ANSWER_KEY_PATH" in os.environ:
    raise RuntimeError("answer key leaked")

with train_public_path.open("r", encoding="utf-8", newline="") as source:
    train_rows = list(csv.DictReader(source))
train_mean = sum(float(row["next_day_yield_up"]) for row in train_rows) / len(train_rows)
probability = 0.65 if train_mean >= 0.5 else 0.35

with features_path.open("r", encoding="utf-8", newline="") as source:
    rows = list(csv.DictReader(source))

with (submission_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=["row_id", "prediction", "probability"])
    writer.writeheader()
    for row in rows:
        writer.writerow({
            "row_id": row["row_id"],
            "prediction": 1 if probability >= 0.5 else 0,
            "probability": probability,
        })

(submission_dir / "writeup.md").write_text("Treasury dummy agent.\\n", encoding="utf-8")
(submission_dir / "notebook.ipynb").write_text(
    json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}),
    encoding="utf-8",
)
print(os.environ["FINDS_TASK_ID"])
""".lstrip(),
        encoding="utf-8",
    )
    runs_root = tmp_path / "runs"
    run_dir = runs_root / "yield_direction_treasury10y_v0" / "treasury_agent"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_yield_direction_treasury10y_agent_command(
        agent_id="treasury_agent",
        agent_version="0.0.1",
        agent_command=[sys.executable, str(agent_script)],
        seed=161,
        data_output_dir=tmp_path / "data" / "treasury" / "raw",
        private_dir=tmp_path / "data" / "treasury" / "private",
        run_dir=run_dir,
        run_label="treasury_agent_001",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command_timeout_seconds=60,
        source_frame=mock_treasury_source_frame(),
        snapshot_date="2026-06-21",
    )

    manifest = load_run_manifest(result.manifest_path)
    score = json.loads(result.score_path.read_text(encoding="utf-8"))
    validation = json.loads(result.validation_path.read_text(encoding="utf-8"))

    assert result.status == "completed"
    assert score["task_id"] == "yield_direction_treasury10y_v0"
    assert score["execution_success"] == 1.0
    assert validation["ok"] is True
    assert validate_run_manifest(manifest).ok
    assert manifest["run_type"] == "agent"
    assert manifest["agent"]["agent_id"] == "treasury_agent"
    assert manifest["commands"][0]["exit_code"] == 0
    assert manifest["trace"]["snapshot_date"] == "2026-06-21"
    assert (result.run_dir / "logs" / "stdout.txt").exists()

    with summary_csv.open("r", encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))

    assert len(summary_rows) == 1
    assert summary_rows[0]["agent_id"] == "treasury_agent"
    assert summary_rows[0]["run_type"] == "agent"
    assert summary_rows[0]["run_count"] == "1"
    assert report_md.exists()
    assert summary_md.exists()


def test_yield_direction_treasury10y_agent_command_suite_repeats_agent_runs(tmp_path: Path):
    agent_script = tmp_path / "treasury_suite_agent.py"
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
        probability = 0.61 if float(row["dgs10_change_1d"]) > 0 else 0.39
        writer.writerow({
            "row_id": row["row_id"],
            "prediction": 1 if probability >= 0.5 else 0,
            "probability": probability,
        })

(submission_dir / "writeup.md").write_text("Repeated treasury dummy agent.\\n", encoding="utf-8")
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

    result = run_yield_direction_treasury10y_agent_command_suite(
        agent_id="treasury_suite_agent",
        agent_version="0.0.1",
        agent_command=[sys.executable, str(agent_script)],
        seed=171,
        repeat=2,
        run_label_prefix="treasury_agent",
        data_output_dir=tmp_path / "data" / "treasury" / "raw",
        private_dir=tmp_path / "data" / "treasury" / "private",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command_timeout_seconds=60,
        source_frame=mock_treasury_source_frame(),
        snapshot_date="2026-06-21",
    )

    with report_csv.open("r", encoding="utf-8", newline="") as handle:
        result_rows = list(csv.DictReader(handle))
    with summary_csv.open("r", encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))

    assert result.status == "completed"
    assert len(result.results) == 2
    assert len(result_rows) == 2
    assert {row["task_id"] for row in result_rows} == {"yield_direction_treasury10y_v0"}
    assert {row["run_type"] for row in result_rows} == {"agent"}
    assert sorted(row["trace.run_label"] for row in result_rows) == [
        "treasury_agent_001_seed_171",
        "treasury_agent_002_seed_172",
    ]
    assert len(summary_rows) == 1
    assert summary_rows[0]["agent_id"] == "treasury_suite_agent"
    assert summary_rows[0]["run_count"] == "2"
    assert summary_rows[0]["score.overall_score.count"] == "2"
    assert report_md.exists()
    assert summary_md.exists()


def test_research_sweep_env_agent_selects_treasury_candidate_and_records_ranking(tmp_path: Path):
    agent_script = Path("agents/examples/research_sweep_env_agent.py").resolve()
    runs_root = tmp_path / "runs"
    run_dir = runs_root / "yield_direction_treasury10y_v0" / "treasury_research_sweep_env_agent"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_yield_direction_treasury10y_agent_command(
        agent_id="treasury_research_sweep_env_agent",
        agent_version="0.2.0",
        agent_command=[sys.executable, str(agent_script)],
        seed=173,
        data_output_dir=tmp_path / "data" / "treasury" / "raw",
        private_dir=tmp_path / "data" / "treasury" / "private",
        run_dir=run_dir,
        run_label="treasury_sweep_001",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command_timeout_seconds=60,
        source_frame=mock_treasury_source_frame(),
        snapshot_date="2026-06-21",
    )

    manifest = load_run_manifest(result.manifest_path)
    metadata = json.loads((result.run_dir / "baseline_metadata.json").read_text(encoding="utf-8"))
    stdout = (result.run_dir / "logs" / "stdout.txt").read_text(encoding="utf-8")

    assert result.status == "completed"
    assert manifest["run_type"] == "agent"
    assert manifest["agent"]["agent_id"] == "treasury_research_sweep_env_agent"
    assert metadata["task_id"] == "yield_direction_treasury10y_v0"
    assert metadata["selected_candidate_id"] in {
        "previous_day_direction_baseline",
        "logistic_regression_baseline",
        "random_forest_baseline",
        "extra_trees_baseline",
    }
    assert len(metadata["candidate_ranking"]) == 4
    assert metadata["candidate_ranking"][0]["candidate_id"] == metadata["selected_candidate_id"]
    assert {
        candidate["candidate_id"] for candidate in metadata["candidate_ranking"]
    } == {
        "previous_day_direction_baseline",
        "logistic_regression_baseline",
        "random_forest_baseline",
        "extra_trees_baseline",
    }
    assert manifest["trace"]["snapshot_date"] == "2026-06-21"
    assert "selected " in stdout
    assert report_md.exists()
    assert summary_md.exists()


def test_treasury_baseline_suite_runs_all_baselines_with_repeats(tmp_path: Path):
    runs_root = tmp_path / "runs"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_yield_direction_treasury10y_baseline_suite(
        seed=151,
        repeat=2,
        run_label_prefix="treasury_suite",
        data_output_dir=tmp_path / "data" / "treasury" / "raw",
        private_dir=tmp_path / "data" / "treasury" / "private",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command="test treasury baseline suite",
        source_frame=mock_treasury_source_frame(),
        snapshot_date="2026-06-21",
    )

    with report_csv.open("r", encoding="utf-8", newline="") as handle:
        result_rows = list(csv.DictReader(handle))
    with summary_csv.open("r", encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))

    assert result.status == "completed"
    assert len(result.results) == 8
    assert len(result_rows) == 8
    assert len(summary_rows) == 4
    assert {row["task_id"] for row in result_rows} == {"yield_direction_treasury10y_v0"}
    assert sorted(row["agent_id"] for row in summary_rows) == [
        "extra_trees_baseline",
        "logistic_regression_baseline",
        "previous_day_direction_baseline",
        "random_forest_baseline",
    ]
    assert {row["run_count"] for row in summary_rows} == {"2"}
    assert "yield_direction_treasury10y_v0" in summary_md.read_text(encoding="utf-8")


def test_run_yield_curve_10y2y_steepening_random_forest_pipeline(tmp_path: Path):
    run_dir = tmp_path / "runs" / "yield_curve_10y2y_steepening_v0" / "random_forest_baseline"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_yield_curve_10y2y_steepening_random_forest_pipeline(
        data_output_dir=tmp_path / "data" / "curve" / "raw",
        private_dir=tmp_path / "data" / "curve" / "private",
        run_dir=run_dir,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command="test yield curve random forest pipeline",
        source_frame=mock_treasury_source_frame(),
        snapshot_date="2026-06-21",
    )

    assert result.status == "completed"
    assert (run_dir / "predictions.csv").exists()
    assert (run_dir / "writeup.md").exists()
    assert (run_dir / "notebook.ipynb").exists()
    assert (run_dir / "baseline_metadata.json").exists()

    score = json.loads(result.score_path.read_text(encoding="utf-8"))
    validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
    manifest = load_run_manifest(result.manifest_path)

    assert score["task_id"] == "yield_curve_10y2y_steepening_v0"
    assert score["execution_success"] == 1.0
    assert validation["ok"] is True
    assert validation["methodology_findings"] == []
    assert validate_run_manifest(manifest).ok
    assert manifest["task_id"] == "yield_curve_10y2y_steepening_v0"
    assert manifest["agent"]["agent_id"] == "random_forest_baseline"
    assert summary_csv.exists()
    assert "yield_curve_10y2y_steepening_v0" in summary_md.read_text(encoding="utf-8")


def test_run_yield_curve_10y2y_steepening_agent_command(tmp_path: Path):
    agent_script = tmp_path / "yield_curve_agent.py"
    agent_script.write_text(
        """
import csv
import json
import os
from pathlib import Path

train_public_path = Path(os.environ["FINDS_TRAIN_PUBLIC_PATH"])
features_path = Path(os.environ["FINDS_HOLDOUT_FEATURES_PATH"])
submission_dir = Path(os.environ["FINDS_SUBMISSION_DIR"])
submission_dir.mkdir(parents=True, exist_ok=True)

if "FINDS_ANSWER_KEY_PATH" in os.environ:
    raise RuntimeError("answer key leaked")

with train_public_path.open("r", encoding="utf-8", newline="") as source:
    train_rows = list(csv.DictReader(source))
train_mean = sum(float(row["next_day_curve_steepening"]) for row in train_rows) / len(train_rows)
probability = 0.65 if train_mean >= 0.5 else 0.35

with features_path.open("r", encoding="utf-8", newline="") as source:
    rows = list(csv.DictReader(source))

with (submission_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=["row_id", "prediction", "probability"])
    writer.writeheader()
    for row in rows:
        writer.writerow({
            "row_id": row["row_id"],
            "prediction": 1 if probability >= 0.5 else 0,
            "probability": probability,
        })

(submission_dir / "writeup.md").write_text("Yield curve dummy agent.\\n", encoding="utf-8")
(submission_dir / "notebook.ipynb").write_text(
    json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}),
    encoding="utf-8",
)
print(os.environ["FINDS_TASK_ID"])
""".lstrip(),
        encoding="utf-8",
    )
    runs_root = tmp_path / "runs"
    run_dir = runs_root / "yield_curve_10y2y_steepening_v0" / "yield_curve_agent"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_yield_curve_10y2y_steepening_agent_command(
        agent_id="yield_curve_agent",
        agent_version="0.0.1",
        agent_command=[sys.executable, str(agent_script)],
        seed=176,
        data_output_dir=tmp_path / "data" / "curve" / "raw",
        private_dir=tmp_path / "data" / "curve" / "private",
        run_dir=run_dir,
        run_label="yield_curve_agent_001",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command_timeout_seconds=60,
        source_frame=mock_treasury_source_frame(),
        snapshot_date="2026-06-21",
    )

    manifest = load_run_manifest(result.manifest_path)
    score = json.loads(result.score_path.read_text(encoding="utf-8"))
    validation = json.loads(result.validation_path.read_text(encoding="utf-8"))

    assert result.status == "completed"
    assert score["task_id"] == "yield_curve_10y2y_steepening_v0"
    assert score["execution_success"] == 1.0
    assert validation["ok"] is True
    assert validate_run_manifest(manifest).ok
    assert manifest["run_type"] == "agent"
    assert manifest["agent"]["agent_id"] == "yield_curve_agent"
    assert manifest["commands"][0]["exit_code"] == 0
    assert manifest["trace"]["snapshot_date"] == "2026-06-21"
    assert (result.run_dir / "logs" / "stdout.txt").exists()

    with summary_csv.open("r", encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))

    assert len(summary_rows) == 1
    assert summary_rows[0]["agent_id"] == "yield_curve_agent"
    assert summary_rows[0]["run_type"] == "agent"
    assert summary_rows[0]["run_count"] == "1"
    assert report_md.exists()
    assert summary_md.exists()


def test_yield_curve_10y2y_steepening_agent_command_suite_repeats_agent_runs(tmp_path: Path):
    agent_script = tmp_path / "yield_curve_suite_agent.py"
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
        probability = 0.61 if float(row["curve_10y_2y_change_1d"]) > 0 else 0.39
        writer.writerow({
            "row_id": row["row_id"],
            "prediction": 1 if probability >= 0.5 else 0,
            "probability": probability,
        })

(submission_dir / "writeup.md").write_text("Repeated yield curve dummy agent.\\n", encoding="utf-8")
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

    result = run_yield_curve_10y2y_steepening_agent_command_suite(
        agent_id="yield_curve_suite_agent",
        agent_version="0.0.1",
        agent_command=[sys.executable, str(agent_script)],
        seed=177,
        repeat=2,
        run_label_prefix="yield_curve_agent",
        data_output_dir=tmp_path / "data" / "curve" / "raw",
        private_dir=tmp_path / "data" / "curve" / "private",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command_timeout_seconds=60,
        source_frame=mock_treasury_source_frame(),
        snapshot_date="2026-06-21",
    )

    with report_csv.open("r", encoding="utf-8", newline="") as handle:
        result_rows = list(csv.DictReader(handle))
    with summary_csv.open("r", encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))

    assert result.status == "completed"
    assert len(result.results) == 2
    assert len(result_rows) == 2
    assert {row["task_id"] for row in result_rows} == {"yield_curve_10y2y_steepening_v0"}
    assert {row["run_type"] for row in result_rows} == {"agent"}
    assert sorted(row["trace.run_label"] for row in result_rows) == [
        "yield_curve_agent_001_seed_177",
        "yield_curve_agent_002_seed_178",
    ]
    assert len(summary_rows) == 1
    assert summary_rows[0]["agent_id"] == "yield_curve_suite_agent"
    assert summary_rows[0]["run_count"] == "2"
    assert summary_rows[0]["score.overall_score.count"] == "2"
    assert report_md.exists()
    assert summary_md.exists()


def test_research_sweep_env_agent_selects_yield_curve_candidate_and_records_ranking(tmp_path: Path):
    agent_script = Path("agents/examples/research_sweep_env_agent.py").resolve()
    runs_root = tmp_path / "runs"
    run_dir = runs_root / "yield_curve_10y2y_steepening_v0" / "treasury_curve_research_sweep_env_agent"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_yield_curve_10y2y_steepening_agent_command(
        agent_id="treasury_curve_research_sweep_env_agent",
        agent_version="0.2.0",
        agent_command=[sys.executable, str(agent_script)],
        seed=179,
        data_output_dir=tmp_path / "data" / "curve" / "raw",
        private_dir=tmp_path / "data" / "curve" / "private",
        run_dir=run_dir,
        run_label="yield_curve_sweep_001",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command_timeout_seconds=60,
        source_frame=mock_treasury_source_frame(),
        snapshot_date="2026-06-21",
    )

    manifest = load_run_manifest(result.manifest_path)
    metadata = json.loads((result.run_dir / "baseline_metadata.json").read_text(encoding="utf-8"))
    stdout = (result.run_dir / "logs" / "stdout.txt").read_text(encoding="utf-8")

    assert result.status == "completed"
    assert manifest["run_type"] == "agent"
    assert manifest["agent"]["agent_id"] == "treasury_curve_research_sweep_env_agent"
    assert metadata["task_id"] == "yield_curve_10y2y_steepening_v0"
    assert metadata["selected_candidate_id"] in {
        "previous_day_direction_baseline",
        "logistic_regression_baseline",
        "random_forest_baseline",
        "extra_trees_baseline",
    }
    assert len(metadata["candidate_ranking"]) == 4
    assert metadata["candidate_ranking"][0]["candidate_id"] == metadata["selected_candidate_id"]
    assert {
        candidate["candidate_id"] for candidate in metadata["candidate_ranking"]
    } == {
        "previous_day_direction_baseline",
        "logistic_regression_baseline",
        "random_forest_baseline",
        "extra_trees_baseline",
    }
    assert manifest["trace"]["snapshot_date"] == "2026-06-21"
    assert "selected " in stdout
    assert report_md.exists()
    assert summary_md.exists()


def test_yield_curve_baseline_suite_runs_all_baselines_with_repeats(tmp_path: Path):
    runs_root = tmp_path / "runs"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_yield_curve_10y2y_steepening_baseline_suite(
        seed=178,
        repeat=2,
        run_label_prefix="yield_curve_suite",
        data_output_dir=tmp_path / "data" / "curve" / "raw",
        private_dir=tmp_path / "data" / "curve" / "private",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command="test yield curve baseline suite",
        source_frame=mock_treasury_source_frame(),
        snapshot_date="2026-06-21",
    )

    with report_csv.open("r", encoding="utf-8", newline="") as handle:
        result_rows = list(csv.DictReader(handle))
    with summary_csv.open("r", encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))

    assert result.status == "completed"
    assert len(result.results) == 8
    assert len(result_rows) == 8
    assert len(summary_rows) == 4
    assert {row["task_id"] for row in result_rows} == {"yield_curve_10y2y_steepening_v0"}
    assert sorted(row["agent_id"] for row in summary_rows) == [
        "extra_trees_baseline",
        "logistic_regression_baseline",
        "previous_day_direction_baseline",
        "random_forest_baseline",
    ]
    assert {row["run_count"] for row in summary_rows} == {"2"}
    assert "yield_curve_10y2y_steepening_v0" in summary_md.read_text(encoding="utf-8")


def test_run_yield_curve_10y3mo_steepening_random_forest_pipeline(tmp_path: Path):
    run_dir = tmp_path / "runs" / "yield_curve_10y3mo_steepening_v0" / "random_forest_baseline"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_yield_curve_10y3mo_steepening_random_forest_pipeline(
        data_output_dir=tmp_path / "data" / "curve3mo" / "raw",
        private_dir=tmp_path / "data" / "curve3mo" / "private",
        run_dir=run_dir,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command="test yield curve 10y3mo random forest pipeline",
        source_frame=mock_treasury_source_frame(),
        snapshot_date="2026-06-21",
    )

    assert result.status == "completed"
    assert (run_dir / "predictions.csv").exists()
    assert (run_dir / "writeup.md").exists()
    assert (run_dir / "notebook.ipynb").exists()
    assert (run_dir / "baseline_metadata.json").exists()

    score = json.loads(result.score_path.read_text(encoding="utf-8"))
    validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
    manifest = load_run_manifest(result.manifest_path)

    assert score["task_id"] == "yield_curve_10y3mo_steepening_v0"
    assert score["execution_success"] == 1.0
    assert validation["ok"] is True
    assert validation["methodology_findings"] == []
    assert validate_run_manifest(manifest).ok
    assert manifest["task_id"] == "yield_curve_10y3mo_steepening_v0"
    assert manifest["agent"]["agent_id"] == "random_forest_baseline"
    assert summary_csv.exists()
    assert "yield_curve_10y3mo_steepening_v0" in summary_md.read_text(encoding="utf-8")


def test_run_yield_curve_10y3mo_steepening_agent_command(tmp_path: Path):
    agent_script = tmp_path / "yield_curve_10y3mo_agent.py"
    agent_script.write_text(
        """
import csv
import json
import os
from pathlib import Path

train_public_path = Path(os.environ["FINDS_TRAIN_PUBLIC_PATH"])
features_path = Path(os.environ["FINDS_HOLDOUT_FEATURES_PATH"])
submission_dir = Path(os.environ["FINDS_SUBMISSION_DIR"])
submission_dir.mkdir(parents=True, exist_ok=True)

if "FINDS_ANSWER_KEY_PATH" in os.environ:
    raise RuntimeError("answer key leaked")

with train_public_path.open("r", encoding="utf-8", newline="") as source:
    train_rows = list(csv.DictReader(source))
train_mean = sum(float(row["next_day_curve_10y3mo_steepening"]) for row in train_rows) / len(train_rows)
probability = 0.65 if train_mean >= 0.5 else 0.35

with features_path.open("r", encoding="utf-8", newline="") as source:
    rows = list(csv.DictReader(source))

with (submission_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=["row_id", "prediction", "probability"])
    writer.writeheader()
    for row in rows:
        writer.writerow({
            "row_id": row["row_id"],
            "prediction": 1 if probability >= 0.5 else 0,
            "probability": probability,
        })

(submission_dir / "writeup.md").write_text("Yield curve 10Y-3M dummy agent.\\n", encoding="utf-8")
(submission_dir / "notebook.ipynb").write_text(
    json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}),
    encoding="utf-8",
)
print(os.environ["FINDS_TASK_ID"])
""".lstrip(),
        encoding="utf-8",
    )
    runs_root = tmp_path / "runs"
    run_dir = runs_root / "yield_curve_10y3mo_steepening_v0" / "yield_curve_10y3mo_agent"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_yield_curve_10y3mo_steepening_agent_command(
        agent_id="yield_curve_10y3mo_agent",
        agent_version="0.0.1",
        agent_command=[sys.executable, str(agent_script)],
        seed=176,
        data_output_dir=tmp_path / "data" / "curve3mo" / "raw",
        private_dir=tmp_path / "data" / "curve3mo" / "private",
        run_dir=run_dir,
        run_label="yield_curve_10y3mo_agent_001",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command_timeout_seconds=60,
        source_frame=mock_treasury_source_frame(),
        snapshot_date="2026-06-21",
    )

    manifest = load_run_manifest(result.manifest_path)
    score = json.loads(result.score_path.read_text(encoding="utf-8"))
    validation = json.loads(result.validation_path.read_text(encoding="utf-8"))

    assert result.status == "completed"
    assert score["task_id"] == "yield_curve_10y3mo_steepening_v0"
    assert score["execution_success"] == 1.0
    assert validation["ok"] is True
    assert validate_run_manifest(manifest).ok
    assert manifest["run_type"] == "agent"
    assert manifest["agent"]["agent_id"] == "yield_curve_10y3mo_agent"
    assert manifest["commands"][0]["exit_code"] == 0
    assert manifest["trace"]["snapshot_date"] == "2026-06-21"
    assert (result.run_dir / "logs" / "stdout.txt").exists()

    with summary_csv.open("r", encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))

    assert len(summary_rows) == 1
    assert summary_rows[0]["agent_id"] == "yield_curve_10y3mo_agent"
    assert summary_rows[0]["run_type"] == "agent"
    assert summary_rows[0]["run_count"] == "1"
    assert report_md.exists()
    assert summary_md.exists()


def test_yield_curve_10y3mo_steepening_agent_command_suite_repeats_agent_runs(tmp_path: Path):
    agent_script = tmp_path / "yield_curve_10y3mo_suite_agent.py"
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
        probability = 0.61 if float(row["curve_10y_3mo_change_1d"]) > 0 else 0.39
        writer.writerow({
            "row_id": row["row_id"],
            "prediction": 1 if probability >= 0.5 else 0,
            "probability": probability,
        })

(submission_dir / "writeup.md").write_text("Repeated yield curve 10Y-3M dummy agent.\\n", encoding="utf-8")
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

    result = run_yield_curve_10y3mo_steepening_agent_command_suite(
        agent_id="yield_curve_10y3mo_suite_agent",
        agent_version="0.0.1",
        agent_command=[sys.executable, str(agent_script)],
        seed=177,
        repeat=2,
        run_label_prefix="yield_curve_10y3mo_agent",
        data_output_dir=tmp_path / "data" / "curve3mo" / "raw",
        private_dir=tmp_path / "data" / "curve3mo" / "private",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command_timeout_seconds=60,
        source_frame=mock_treasury_source_frame(),
        snapshot_date="2026-06-21",
    )

    with report_csv.open("r", encoding="utf-8", newline="") as handle:
        result_rows = list(csv.DictReader(handle))
    with summary_csv.open("r", encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))

    assert result.status == "completed"
    assert len(result.results) == 2
    assert len(result_rows) == 2
    assert {row["task_id"] for row in result_rows} == {"yield_curve_10y3mo_steepening_v0"}
    assert {row["run_type"] for row in result_rows} == {"agent"}
    assert sorted(row["trace.run_label"] for row in result_rows) == [
        "yield_curve_10y3mo_agent_001_seed_177",
        "yield_curve_10y3mo_agent_002_seed_178",
    ]
    assert len(summary_rows) == 1
    assert summary_rows[0]["agent_id"] == "yield_curve_10y3mo_suite_agent"
    assert summary_rows[0]["run_count"] == "2"
    assert summary_rows[0]["score.overall_score.count"] == "2"
    assert report_md.exists()
    assert summary_md.exists()


def test_research_sweep_env_agent_selects_yield_curve_10y3mo_candidate_and_records_ranking(
    tmp_path: Path,
):
    agent_script = Path("agents/examples/research_sweep_env_agent.py").resolve()
    runs_root = tmp_path / "runs"
    run_dir = (
        runs_root
        / "yield_curve_10y3mo_steepening_v0"
        / "treasury_curve_10y3mo_research_sweep_env_agent"
    )
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_yield_curve_10y3mo_steepening_agent_command(
        agent_id="treasury_curve_10y3mo_research_sweep_env_agent",
        agent_version="0.2.0",
        agent_command=[sys.executable, str(agent_script)],
        seed=179,
        data_output_dir=tmp_path / "data" / "curve3mo" / "raw",
        private_dir=tmp_path / "data" / "curve3mo" / "private",
        run_dir=run_dir,
        run_label="yield_curve_10y3mo_sweep_001",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command_timeout_seconds=60,
        source_frame=mock_treasury_source_frame(),
        snapshot_date="2026-06-21",
    )

    manifest = load_run_manifest(result.manifest_path)
    metadata = json.loads((result.run_dir / "baseline_metadata.json").read_text(encoding="utf-8"))
    stdout = (result.run_dir / "logs" / "stdout.txt").read_text(encoding="utf-8")

    assert result.status == "completed"
    assert manifest["run_type"] == "agent"
    assert manifest["agent"]["agent_id"] == "treasury_curve_10y3mo_research_sweep_env_agent"
    assert metadata["task_id"] == "yield_curve_10y3mo_steepening_v0"
    assert metadata["selected_candidate_id"] in {
        "previous_day_direction_baseline",
        "logistic_regression_baseline",
        "random_forest_baseline",
        "extra_trees_baseline",
    }
    assert len(metadata["candidate_ranking"]) == 4
    assert metadata["candidate_ranking"][0]["candidate_id"] == metadata["selected_candidate_id"]
    assert {
        candidate["candidate_id"] for candidate in metadata["candidate_ranking"]
    } == {
        "previous_day_direction_baseline",
        "logistic_regression_baseline",
        "random_forest_baseline",
        "extra_trees_baseline",
    }
    assert manifest["trace"]["snapshot_date"] == "2026-06-21"
    assert "selected " in stdout
    assert report_md.exists()
    assert summary_md.exists()


def test_yield_curve_10y3mo_baseline_suite_runs_all_baselines_with_repeats(tmp_path: Path):
    runs_root = tmp_path / "runs"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_yield_curve_10y3mo_steepening_baseline_suite(
        seed=178,
        repeat=2,
        run_label_prefix="yield_curve_10y3mo_suite",
        data_output_dir=tmp_path / "data" / "curve3mo" / "raw",
        private_dir=tmp_path / "data" / "curve3mo" / "private",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command="test yield curve 10y3mo baseline suite",
        source_frame=mock_treasury_source_frame(),
        snapshot_date="2026-06-21",
    )

    with report_csv.open("r", encoding="utf-8", newline="") as handle:
        result_rows = list(csv.DictReader(handle))
    with summary_csv.open("r", encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))

    assert result.status == "completed"
    assert len(result.results) == 8
    assert len(result_rows) == 8
    assert len(summary_rows) == 4
    assert {row["task_id"] for row in result_rows} == {"yield_curve_10y3mo_steepening_v0"}
    assert sorted(row["agent_id"] for row in summary_rows) == [
        "extra_trees_baseline",
        "logistic_regression_baseline",
        "previous_day_direction_baseline",
        "random_forest_baseline",
    ]
    assert {row["run_count"] for row in summary_rows} == {"2"}
    assert "yield_curve_10y3mo_steepening_v0" in summary_md.read_text(encoding="utf-8")


def test_run_front_end_spread_widening_v0_random_forest_pipeline(tmp_path: Path):
    run_dir = tmp_path / "runs" / "front_end_spread_widening_v0" / "random_forest_baseline"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_front_end_spread_widening_v0_random_forest_pipeline(
        data_output_dir=tmp_path / "data" / "front_end" / "raw",
        private_dir=tmp_path / "data" / "front_end" / "private",
        run_dir=run_dir,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command="test front-end random forest pipeline",
        source_frame=mock_treasury_source_frame(),
        snapshot_date="2026-06-21",
    )

    assert result.status == "completed"
    assert (run_dir / "predictions.csv").exists()
    assert (run_dir / "writeup.md").exists()
    assert (run_dir / "notebook.ipynb").exists()
    assert (run_dir / "baseline_metadata.json").exists()

    score = json.loads(result.score_path.read_text(encoding="utf-8"))
    validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
    manifest = load_run_manifest(result.manifest_path)

    assert score["task_id"] == "front_end_spread_widening_v0"
    assert score["execution_success"] == 1.0
    assert validation["ok"] is True
    assert validation["methodology_findings"] == []
    assert validate_run_manifest(manifest).ok
    assert manifest["task_id"] == "front_end_spread_widening_v0"
    assert manifest["agent"]["agent_id"] == "random_forest_baseline"
    assert summary_csv.exists()
    assert "front_end_spread_widening_v0" in summary_md.read_text(encoding="utf-8")


def test_run_front_end_spread_widening_v0_agent_command(tmp_path: Path):
    agent_script = tmp_path / "front_end_agent.py"
    agent_script.write_text(
        """
import csv
import json
import os
from pathlib import Path

train_public_path = Path(os.environ["FINDS_TRAIN_PUBLIC_PATH"])
features_path = Path(os.environ["FINDS_HOLDOUT_FEATURES_PATH"])
submission_dir = Path(os.environ["FINDS_SUBMISSION_DIR"])
submission_dir.mkdir(parents=True, exist_ok=True)

if "FINDS_ANSWER_KEY_PATH" in os.environ:
    raise RuntimeError("answer key leaked")

with train_public_path.open("r", encoding="utf-8", newline="") as source:
    train_rows = list(csv.DictReader(source))
train_mean = sum(float(row["next_day_front_end_widening"]) for row in train_rows) / len(train_rows)
probability = 0.65 if train_mean >= 0.5 else 0.35

with features_path.open("r", encoding="utf-8", newline="") as source:
    rows = list(csv.DictReader(source))

with (submission_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=["row_id", "prediction", "probability"])
    writer.writeheader()
    for row in rows:
        writer.writerow({
            "row_id": row["row_id"],
            "prediction": 1 if probability >= 0.5 else 0,
            "probability": probability,
        })

(submission_dir / "writeup.md").write_text("Front-end dummy agent.\\n", encoding="utf-8")
(submission_dir / "notebook.ipynb").write_text(
    json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}),
    encoding="utf-8",
)
print(os.environ["FINDS_TASK_ID"])
""".lstrip(),
        encoding="utf-8",
    )
    runs_root = tmp_path / "runs"
    run_dir = runs_root / "front_end_spread_widening_v0" / "front_end_agent"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_front_end_spread_widening_v0_agent_command(
        agent_id="front_end_agent",
        agent_version="0.0.1",
        agent_command=[sys.executable, str(agent_script)],
        seed=181,
        data_output_dir=tmp_path / "data" / "front_end" / "raw",
        private_dir=tmp_path / "data" / "front_end" / "private",
        run_dir=run_dir,
        run_label="front_end_agent_001",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command_timeout_seconds=60,
        source_frame=mock_treasury_source_frame(),
        snapshot_date="2026-06-21",
    )

    manifest = load_run_manifest(result.manifest_path)
    score = json.loads(result.score_path.read_text(encoding="utf-8"))
    validation = json.loads(result.validation_path.read_text(encoding="utf-8"))

    assert result.status == "completed"
    assert score["task_id"] == "front_end_spread_widening_v0"
    assert score["execution_success"] == 1.0
    assert validation["ok"] is True
    assert validate_run_manifest(manifest).ok
    assert manifest["run_type"] == "agent"
    assert manifest["agent"]["agent_id"] == "front_end_agent"
    assert manifest["commands"][0]["exit_code"] == 0
    assert manifest["trace"]["snapshot_date"] == "2026-06-21"
    assert (result.run_dir / "logs" / "stdout.txt").exists()

    with summary_csv.open("r", encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))

    assert len(summary_rows) == 1
    assert summary_rows[0]["agent_id"] == "front_end_agent"
    assert summary_rows[0]["run_type"] == "agent"
    assert summary_rows[0]["run_count"] == "1"
    assert report_md.exists()
    assert summary_md.exists()


def test_front_end_baseline_suite_runs_all_baselines_with_repeats(tmp_path: Path):
    runs_root = tmp_path / "runs"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_front_end_spread_widening_v0_baseline_suite(
        seed=182,
        repeat=2,
        run_label_prefix="front_end_suite",
        data_output_dir=tmp_path / "data" / "front_end" / "raw",
        private_dir=tmp_path / "data" / "front_end" / "private",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command="test front-end baseline suite",
        source_frame=mock_treasury_source_frame(),
        snapshot_date="2026-06-21",
    )

    with report_csv.open("r", encoding="utf-8", newline="") as handle:
        result_rows = list(csv.DictReader(handle))
    with summary_csv.open("r", encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))

    assert result.status == "completed"
    assert len(result.results) == 8
    assert len(result_rows) == 8
    assert len(summary_rows) == 4
    assert {row["task_id"] for row in result_rows} == {"front_end_spread_widening_v0"}
    assert sorted(row["agent_id"] for row in summary_rows) == [
        "extra_trees_baseline",
        "logistic_regression_baseline",
        "previous_day_direction_baseline",
        "random_forest_baseline",
    ]
    assert {row["run_count"] for row in summary_rows} == {"2"}
    assert "front_end_spread_widening_v0" in summary_md.read_text(encoding="utf-8")


def test_run_usd_broad_direction_v0_random_forest_pipeline(tmp_path: Path):
    run_dir = tmp_path / "runs" / "usd_broad_direction_v0" / "random_forest_baseline"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_usd_broad_direction_v0_random_forest_pipeline(
        data_output_dir=tmp_path / "data" / "usd" / "raw",
        private_dir=tmp_path / "data" / "usd" / "private",
        run_dir=run_dir,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command="test usd broad random forest pipeline",
        source_frame=mock_usd_broad_source_frame(),
        snapshot_date="2026-06-21",
    )

    assert result.status == "completed"
    assert (run_dir / "predictions.csv").exists()
    assert (run_dir / "writeup.md").exists()
    assert (run_dir / "notebook.ipynb").exists()
    assert (run_dir / "baseline_metadata.json").exists()

    score = json.loads(result.score_path.read_text(encoding="utf-8"))
    validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
    manifest = load_run_manifest(result.manifest_path)

    assert score["task_id"] == "usd_broad_direction_v0"
    assert score["execution_success"] == 1.0
    assert validation["ok"] is True
    assert validation["methodology_findings"] == []
    assert validate_run_manifest(manifest).ok
    assert manifest["task_id"] == "usd_broad_direction_v0"
    assert manifest["agent"]["agent_id"] == "random_forest_baseline"
    assert summary_csv.exists()
    assert "usd_broad_direction_v0" in summary_md.read_text(encoding="utf-8")


def test_run_usd_broad_direction_v0_agent_command(tmp_path: Path):
    agent_script = tmp_path / "usd_agent.py"
    agent_script.write_text(
        """
import csv
import json
import os
from pathlib import Path

train_public_path = Path(os.environ["FINDS_TRAIN_PUBLIC_PATH"])
features_path = Path(os.environ["FINDS_HOLDOUT_FEATURES_PATH"])
submission_dir = Path(os.environ["FINDS_SUBMISSION_DIR"])
submission_dir.mkdir(parents=True, exist_ok=True)

if "FINDS_ANSWER_KEY_PATH" in os.environ:
    raise RuntimeError("answer key leaked")

with train_public_path.open("r", encoding="utf-8", newline="") as source:
    train_rows = list(csv.DictReader(source))
train_mean = sum(float(row["next_day_usd_broad_up"]) for row in train_rows) / len(train_rows)
probability = 0.65 if train_mean >= 0.5 else 0.35

with features_path.open("r", encoding="utf-8", newline="") as source:
    rows = list(csv.DictReader(source))

with (submission_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=["row_id", "prediction", "probability"])
    writer.writeheader()
    for row in rows:
        writer.writerow({
            "row_id": row["row_id"],
            "prediction": 1 if probability >= 0.5 else 0,
            "probability": probability,
        })

(submission_dir / "writeup.md").write_text("USD broad dummy agent.\\n", encoding="utf-8")
(submission_dir / "notebook.ipynb").write_text(
    json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}),
    encoding="utf-8",
)
print(os.environ["FINDS_TASK_ID"])
""".lstrip(),
        encoding="utf-8",
    )
    runs_root = tmp_path / "runs"
    run_dir = runs_root / "usd_broad_direction_v0" / "usd_agent"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_usd_broad_direction_v0_agent_command(
        agent_id="usd_agent",
        agent_version="0.0.1",
        agent_command=[sys.executable, str(agent_script)],
        seed=181,
        data_output_dir=tmp_path / "data" / "usd" / "raw",
        private_dir=tmp_path / "data" / "usd" / "private",
        run_dir=run_dir,
        run_label="usd_agent_001",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command_timeout_seconds=60,
        source_frame=mock_usd_broad_source_frame(),
        snapshot_date="2026-06-21",
    )

    manifest = load_run_manifest(result.manifest_path)
    score = json.loads(result.score_path.read_text(encoding="utf-8"))
    validation = json.loads(result.validation_path.read_text(encoding="utf-8"))

    assert result.status == "completed"
    assert score["task_id"] == "usd_broad_direction_v0"
    assert score["execution_success"] == 1.0
    assert validation["ok"] is True
    assert validate_run_manifest(manifest).ok
    assert manifest["run_type"] == "agent"
    assert manifest["agent"]["agent_id"] == "usd_agent"
    assert manifest["commands"][0]["exit_code"] == 0
    assert manifest["trace"]["snapshot_date"] == "2026-06-21"
    assert (result.run_dir / "logs" / "stdout.txt").exists()

    with summary_csv.open("r", encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))

    assert len(summary_rows) == 1
    assert summary_rows[0]["agent_id"] == "usd_agent"
    assert summary_rows[0]["run_type"] == "agent"
    assert summary_rows[0]["run_count"] == "1"
    assert report_md.exists()
    assert summary_md.exists()


def test_usd_broad_direction_v0_agent_command_suite_repeats_agent_runs(tmp_path: Path):
    agent_script = tmp_path / "usd_suite_agent.py"
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
        probability = 0.61 if float(row["usd_broad_return_1d"]) > 0 else 0.39
        writer.writerow({
            "row_id": row["row_id"],
            "prediction": 1 if probability >= 0.5 else 0,
            "probability": probability,
        })

(submission_dir / "writeup.md").write_text("Repeated USD broad dummy agent.\\n", encoding="utf-8")
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

    result = run_usd_broad_direction_v0_agent_command_suite(
        agent_id="usd_suite_agent",
        agent_version="0.0.1",
        agent_command=[sys.executable, str(agent_script)],
        seed=191,
        repeat=2,
        run_label_prefix="usd_agent",
        data_output_dir=tmp_path / "data" / "usd" / "raw",
        private_dir=tmp_path / "data" / "usd" / "private",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command_timeout_seconds=60,
        source_frame=mock_usd_broad_source_frame(),
        snapshot_date="2026-06-21",
    )

    with report_csv.open("r", encoding="utf-8", newline="") as handle:
        result_rows = list(csv.DictReader(handle))
    with summary_csv.open("r", encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))

    assert result.status == "completed"
    assert len(result.results) == 2
    assert len(result_rows) == 2
    assert {row["task_id"] for row in result_rows} == {"usd_broad_direction_v0"}
    assert {row["run_type"] for row in result_rows} == {"agent"}
    assert sorted(row["trace.run_label"] for row in result_rows) == [
        "usd_agent_001_seed_191",
        "usd_agent_002_seed_192",
    ]
    assert len(summary_rows) == 1
    assert summary_rows[0]["agent_id"] == "usd_suite_agent"
    assert summary_rows[0]["run_count"] == "2"
    assert summary_rows[0]["score.overall_score.count"] == "2"
    assert report_md.exists()
    assert summary_md.exists()


def test_research_sweep_env_agent_selects_usd_candidate_and_records_ranking(tmp_path: Path):
    agent_script = Path("agents/examples/research_sweep_env_agent.py").resolve()
    runs_root = tmp_path / "runs"
    run_dir = runs_root / "usd_broad_direction_v0" / "usd_research_sweep_env_agent"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_usd_broad_direction_v0_agent_command(
        agent_id="usd_research_sweep_env_agent",
        agent_version="0.2.0",
        agent_command=[sys.executable, str(agent_script)],
        seed=193,
        data_output_dir=tmp_path / "data" / "usd" / "raw",
        private_dir=tmp_path / "data" / "usd" / "private",
        run_dir=run_dir,
        run_label="usd_sweep_001",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command_timeout_seconds=60,
        source_frame=mock_usd_broad_source_frame(),
        snapshot_date="2026-06-21",
    )

    manifest = load_run_manifest(result.manifest_path)
    metadata = json.loads((result.run_dir / "baseline_metadata.json").read_text(encoding="utf-8"))
    stdout = (result.run_dir / "logs" / "stdout.txt").read_text(encoding="utf-8")

    assert result.status == "completed"
    assert manifest["run_type"] == "agent"
    assert manifest["agent"]["agent_id"] == "usd_research_sweep_env_agent"
    assert metadata["task_id"] == "usd_broad_direction_v0"
    assert metadata["selected_candidate_id"] in {
        "previous_day_direction_baseline",
        "logistic_regression_baseline",
        "random_forest_baseline",
        "extra_trees_baseline",
    }
    assert len(metadata["candidate_ranking"]) == 4
    assert metadata["candidate_ranking"][0]["candidate_id"] == metadata["selected_candidate_id"]
    assert {
        candidate["candidate_id"] for candidate in metadata["candidate_ranking"]
    } == {
        "previous_day_direction_baseline",
        "logistic_regression_baseline",
        "random_forest_baseline",
        "extra_trees_baseline",
    }
    assert manifest["trace"]["snapshot_date"] == "2026-06-21"
    assert "selected " in stdout
    assert report_md.exists()
    assert summary_md.exists()


def test_usd_broad_baseline_suite_runs_all_baselines_with_repeats(tmp_path: Path):
    runs_root = tmp_path / "runs"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_usd_broad_direction_v0_baseline_suite(
        seed=181,
        repeat=2,
        run_label_prefix="usd_suite",
        data_output_dir=tmp_path / "data" / "usd" / "raw",
        private_dir=tmp_path / "data" / "usd" / "private",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command="test usd broad baseline suite",
        source_frame=mock_usd_broad_source_frame(),
        snapshot_date="2026-06-21",
    )

    with report_csv.open("r", encoding="utf-8", newline="") as handle:
        result_rows = list(csv.DictReader(handle))
    with summary_csv.open("r", encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))

    assert result.status == "completed"
    assert len(result.results) == 8
    assert len(result_rows) == 8
    assert len(summary_rows) == 4
    assert {row["task_id"] for row in result_rows} == {"usd_broad_direction_v0"}
    assert sorted(row["agent_id"] for row in summary_rows) == [
        "extra_trees_baseline",
        "logistic_regression_baseline",
        "previous_day_direction_baseline",
        "random_forest_baseline",
    ]
    assert {row["run_count"] for row in summary_rows} == {"2"}
    assert "usd_broad_direction_v0" in summary_md.read_text(encoding="utf-8")


def test_pilot_baseline_suite_runs_all_implemented_baselines(tmp_path: Path):
    runs_root = tmp_path / "runs"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_pilot_baseline_suite(
        market_seed=91,
        event_seed=101,
        treasury_seed=111,
        curve_seed=115,
        curve3mo_seed=117,
        front_end_seed=119,
        usd_seed=121,
        repeat=2,
        run_label_prefix="pilot_suite",
        market_data_output_dir=tmp_path / "data" / "market" / "raw",
        market_private_dir=tmp_path / "data" / "market" / "private",
        event_data_output_dir=tmp_path / "data" / "event" / "raw",
        event_private_dir=tmp_path / "data" / "event" / "private",
        treasury_data_output_dir=tmp_path / "data" / "treasury" / "raw",
        treasury_private_dir=tmp_path / "data" / "treasury" / "private",
        curve_data_output_dir=tmp_path / "data" / "curve" / "raw",
        curve_private_dir=tmp_path / "data" / "curve" / "private",
        curve3mo_data_output_dir=tmp_path / "data" / "curve3mo" / "raw",
        curve3mo_private_dir=tmp_path / "data" / "curve3mo" / "private",
        front_end_data_output_dir=tmp_path / "data" / "front_end" / "raw",
        front_end_private_dir=tmp_path / "data" / "front_end" / "private",
        usd_data_output_dir=tmp_path / "data" / "usd" / "raw",
        usd_private_dir=tmp_path / "data" / "usd" / "private",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command="test pilot baseline suite",
        treasury_source_frame=mock_treasury_source_frame(),
        treasury_snapshot_date="2026-06-21",
        curve_source_frame=mock_treasury_source_frame(),
        curve_snapshot_date="2026-06-21",
        curve3mo_source_frame=mock_treasury_source_frame(),
        curve3mo_snapshot_date="2026-06-21",
        front_end_source_frame=mock_treasury_source_frame(),
        front_end_snapshot_date="2026-06-21",
        usd_source_frame=mock_usd_broad_source_frame(),
        usd_snapshot_date="2026-06-21",
    )

    with report_csv.open("r", encoding="utf-8", newline="") as handle:
        result_rows = list(csv.DictReader(handle))
    with summary_csv.open("r", encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))

    assert result.status == "completed"
    assert len(result.results) == 54
    assert len(result_rows) == 54
    assert len(summary_rows) == 27
    assert {row["task_id"] for row in result_rows} == {
        "front_end_spread_widening_v0",
        "synthetic_event_response_v0",
        "synthetic_market_direction_v0",
        "usd_afe_vs_eme_relative_direction_v0",
        "usd_broad_direction_v0",
        "yield_curve_10y3mo_steepening_v0",
        "yield_curve_10y2y_steepening_v0",
        "yield_direction_treasury10y_v0",
    }
    assert sorted(row["agent_id"] for row in summary_rows) == [
        "event_rule_baseline",
        "extra_trees_baseline",
        "extra_trees_baseline",
        "extra_trees_baseline",
        "extra_trees_baseline",
        "extra_trees_baseline",
        "extra_trees_baseline",
        "logistic_regression_baseline",
        "logistic_regression_baseline",
        "logistic_regression_baseline",
        "logistic_regression_baseline",
        "logistic_regression_baseline",
        "logistic_regression_baseline",
        "logistic_regression_baseline",
        "momentum_baseline",
        "previous_day_direction_baseline",
        "previous_day_direction_baseline",
        "previous_day_direction_baseline",
        "previous_day_direction_baseline",
        "previous_day_direction_baseline",
        "previous_day_direction_baseline",
        "random_forest_baseline",
        "random_forest_baseline",
        "random_forest_baseline",
        "random_forest_baseline",
        "random_forest_baseline",
        "random_forest_baseline",
    ]
    assert {row["run_count"] for row in summary_rows} == {"2"}
    assert {row["score.overall_score.count"] for row in summary_rows} == {"2"}
    assert report_md.exists()
    assert "synthetic_event_response_v0" in summary_md.read_text(encoding="utf-8")
    assert "synthetic_market_direction_v0" in summary_md.read_text(encoding="utf-8")
    assert "yield_direction_treasury10y_v0" in summary_md.read_text(encoding="utf-8")
    assert "yield_curve_10y2y_steepening_v0" in summary_md.read_text(encoding="utf-8")
    assert "yield_curve_10y3mo_steepening_v0" in summary_md.read_text(encoding="utf-8")
    assert "front_end_spread_widening_v0" in summary_md.read_text(encoding="utf-8")
    assert "usd_afe_vs_eme_relative_direction_v0" in summary_md.read_text(encoding="utf-8")
    assert "usd_broad_direction_v0" in summary_md.read_text(encoding="utf-8")


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


def test_pilot_agent_suite_runs_all_implemented_agent_wrappers(tmp_path: Path):
    market_agent_script = tmp_path / "market_agent.py"
    market_agent_script.write_text(
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

(submission_dir / "writeup.md").write_text("Pilot market agent.\\n", encoding="utf-8")
(submission_dir / "notebook.ipynb").write_text(
    json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}),
    encoding="utf-8",
)
""".lstrip(),
        encoding="utf-8",
    )
    event_agent_script = tmp_path / "event_agent.py"
    event_agent_script.write_text(
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

(submission_dir / "writeup.md").write_text("Pilot event agent.\\n", encoding="utf-8")
(submission_dir / "notebook.ipynb").write_text(
    json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}),
    encoding="utf-8",
)
""".lstrip(),
        encoding="utf-8",
    )
    treasury_agent_script = tmp_path / "treasury_agent.py"
    treasury_agent_script.write_text(
        """
import csv
import json
import os
from pathlib import Path

train_public_path = Path(os.environ["FINDS_TRAIN_PUBLIC_PATH"])
features_path = Path(os.environ["FINDS_HOLDOUT_FEATURES_PATH"])
submission_dir = Path(os.environ["FINDS_SUBMISSION_DIR"])
submission_dir.mkdir(parents=True, exist_ok=True)

with train_public_path.open("r", encoding="utf-8", newline="") as source:
    train_rows = list(csv.DictReader(source))
train_mean = sum(float(row["next_day_yield_up"]) for row in train_rows) / len(train_rows)
probability = 0.62 if train_mean >= 0.5 else 0.38

with features_path.open("r", encoding="utf-8", newline="") as source:
    rows = list(csv.DictReader(source))

with (submission_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=["row_id", "prediction", "probability"])
    writer.writeheader()
    for row in rows:
        writer.writerow({
            "row_id": row["row_id"],
            "prediction": 1 if probability >= 0.5 else 0,
            "probability": probability,
        })

(submission_dir / "writeup.md").write_text("Pilot treasury agent.\\n", encoding="utf-8")
(submission_dir / "notebook.ipynb").write_text(
    json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}),
    encoding="utf-8",
)
""".lstrip(),
        encoding="utf-8",
    )
    curve_agent_script = tmp_path / "curve_agent.py"
    curve_agent_script.write_text(
        """
import csv
import json
import os
from pathlib import Path

train_public_path = Path(os.environ["FINDS_TRAIN_PUBLIC_PATH"])
features_path = Path(os.environ["FINDS_HOLDOUT_FEATURES_PATH"])
submission_dir = Path(os.environ["FINDS_SUBMISSION_DIR"])
submission_dir.mkdir(parents=True, exist_ok=True)

with train_public_path.open("r", encoding="utf-8", newline="") as source:
    train_rows = list(csv.DictReader(source))
train_mean = sum(float(row["next_day_curve_steepening"]) for row in train_rows) / len(train_rows)
probability = 0.61 if train_mean >= 0.5 else 0.39

with features_path.open("r", encoding="utf-8", newline="") as source:
    rows = list(csv.DictReader(source))

with (submission_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=["row_id", "prediction", "probability"])
    writer.writeheader()
    for row in rows:
        writer.writerow({
            "row_id": row["row_id"],
            "prediction": 1 if probability >= 0.5 else 0,
            "probability": probability,
        })

(submission_dir / "writeup.md").write_text("Pilot yield curve agent.\\n", encoding="utf-8")
(submission_dir / "notebook.ipynb").write_text(
    json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}),
    encoding="utf-8",
)
""".lstrip(),
        encoding="utf-8",
    )
    curve3mo_agent_script = tmp_path / "curve3mo_agent.py"
    curve3mo_agent_script.write_text(
        """
import csv
import json
import os
from pathlib import Path

train_public_path = Path(os.environ["FINDS_TRAIN_PUBLIC_PATH"])
features_path = Path(os.environ["FINDS_HOLDOUT_FEATURES_PATH"])
submission_dir = Path(os.environ["FINDS_SUBMISSION_DIR"])
submission_dir.mkdir(parents=True, exist_ok=True)

with train_public_path.open("r", encoding="utf-8", newline="") as source:
    train_rows = list(csv.DictReader(source))
train_mean = sum(float(row["next_day_curve_10y3mo_steepening"]) for row in train_rows) / len(train_rows)
probability = 0.61 if train_mean >= 0.5 else 0.39

with features_path.open("r", encoding="utf-8", newline="") as source:
    rows = list(csv.DictReader(source))

with (submission_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=["row_id", "prediction", "probability"])
    writer.writeheader()
    for row in rows:
        writer.writerow({
            "row_id": row["row_id"],
            "prediction": 1 if probability >= 0.5 else 0,
            "probability": probability,
        })

(submission_dir / "writeup.md").write_text("Pilot yield curve 10Y-3M agent.\\n", encoding="utf-8")
(submission_dir / "notebook.ipynb").write_text(
    json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}),
    encoding="utf-8",
)
""".lstrip(),
        encoding="utf-8",
    )
    front_end_agent_script = tmp_path / "front_end_agent.py"
    front_end_agent_script.write_text(
        """
import csv
import json
import os
from pathlib import Path

train_public_path = Path(os.environ["FINDS_TRAIN_PUBLIC_PATH"])
features_path = Path(os.environ["FINDS_HOLDOUT_FEATURES_PATH"])
submission_dir = Path(os.environ["FINDS_SUBMISSION_DIR"])
submission_dir.mkdir(parents=True, exist_ok=True)

with train_public_path.open("r", encoding="utf-8", newline="") as source:
    train_rows = list(csv.DictReader(source))
train_mean = sum(float(row["next_day_front_end_widening"]) for row in train_rows) / len(train_rows)
probability = 0.60 if train_mean >= 0.5 else 0.40

with features_path.open("r", encoding="utf-8", newline="") as source:
    rows = list(csv.DictReader(source))

with (submission_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=["row_id", "prediction", "probability"])
    writer.writeheader()
    for row in rows:
        writer.writerow({
            "row_id": row["row_id"],
            "prediction": 1 if probability >= 0.5 else 0,
            "probability": probability,
        })

(submission_dir / "writeup.md").write_text("Pilot front-end agent.\\n", encoding="utf-8")
(submission_dir / "notebook.ipynb").write_text(
    json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}),
    encoding="utf-8",
)
""".lstrip(),
        encoding="utf-8",
    )
    usd_agent_script = tmp_path / "usd_agent.py"
    usd_agent_script.write_text(
        """
import csv
import json
import os
from pathlib import Path

train_public_path = Path(os.environ["FINDS_TRAIN_PUBLIC_PATH"])
features_path = Path(os.environ["FINDS_HOLDOUT_FEATURES_PATH"])
submission_dir = Path(os.environ["FINDS_SUBMISSION_DIR"])
submission_dir.mkdir(parents=True, exist_ok=True)

with train_public_path.open("r", encoding="utf-8", newline="") as source:
    train_rows = list(csv.DictReader(source))
label_column = (
    "next_day_afe_outperforms_eme"
    if os.environ["FINDS_TASK_ID"] == "usd_afe_vs_eme_relative_direction_v0"
    else "next_day_usd_broad_up"
)
train_mean = sum(float(row[label_column]) for row in train_rows) / len(train_rows)
probability = 0.63 if train_mean >= 0.5 else 0.37

with features_path.open("r", encoding="utf-8", newline="") as source:
    rows = list(csv.DictReader(source))

with (submission_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=["row_id", "prediction", "probability"])
    writer.writeheader()
    for row in rows:
        writer.writerow({
            "row_id": row["row_id"],
            "prediction": 1 if probability >= 0.5 else 0,
            "probability": probability,
        })

(submission_dir / "writeup.md").write_text("Pilot USD agent.\\n", encoding="utf-8")
(submission_dir / "notebook.ipynb").write_text(
    json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}),
    encoding="utf-8",
)
""".lstrip(),
        encoding="utf-8",
    )
    runs_root = tmp_path / "runs"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    result = run_pilot_agent_suite(
        market_agent_id="pilot_market_agent",
        market_agent_version="0.0.1",
        market_agent_command=[sys.executable, str(market_agent_script)],
        event_agent_id="pilot_event_agent",
        event_agent_version="0.0.1",
        event_agent_command=[sys.executable, str(event_agent_script)],
        treasury_agent_id="pilot_treasury_agent",
        treasury_agent_version="0.0.1",
        treasury_agent_command=[sys.executable, str(treasury_agent_script)],
        curve_agent_id="pilot_curve_agent",
        curve_agent_version="0.0.1",
        curve_agent_command=[sys.executable, str(curve_agent_script)],
        curve3mo_agent_id="pilot_curve3mo_agent",
        curve3mo_agent_version="0.0.1",
        curve3mo_agent_command=[sys.executable, str(curve3mo_agent_script)],
        front_end_agent_id="pilot_front_end_agent",
        front_end_agent_version="0.0.1",
        front_end_agent_command=[sys.executable, str(front_end_agent_script)],
        usd_agent_id="pilot_usd_agent",
        usd_agent_version="0.0.1",
        usd_agent_command=[sys.executable, str(usd_agent_script)],
        market_seed=111,
        event_seed=121,
        treasury_seed=131,
        curve_seed=137,
        curve3mo_seed=138,
        front_end_seed=139,
        usd_seed=141,
        repeat=2,
        run_label_prefix="pilot_agent",
        market_data_output_dir=tmp_path / "data" / "market" / "raw",
        market_private_dir=tmp_path / "data" / "market" / "private",
        event_data_output_dir=tmp_path / "data" / "event" / "raw",
        event_private_dir=tmp_path / "data" / "event" / "private",
        treasury_data_output_dir=tmp_path / "data" / "treasury" / "raw",
        treasury_private_dir=tmp_path / "data" / "treasury" / "private",
        curve_data_output_dir=tmp_path / "data" / "curve" / "raw",
        curve_private_dir=tmp_path / "data" / "curve" / "private",
        curve3mo_data_output_dir=tmp_path / "data" / "curve3mo" / "raw",
        curve3mo_private_dir=tmp_path / "data" / "curve3mo" / "private",
        front_end_data_output_dir=tmp_path / "data" / "front_end" / "raw",
        front_end_private_dir=tmp_path / "data" / "front_end" / "private",
        usd_data_output_dir=tmp_path / "data" / "usd" / "raw",
        usd_private_dir=tmp_path / "data" / "usd" / "private",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command_timeout_seconds=60,
        treasury_source_frame=mock_treasury_source_frame(),
        treasury_snapshot_date="2026-06-21",
        curve_source_frame=mock_treasury_source_frame(),
        curve_snapshot_date="2026-06-21",
        curve3mo_source_frame=mock_treasury_source_frame(),
        curve3mo_snapshot_date="2026-06-21",
        front_end_source_frame=mock_treasury_source_frame(),
        front_end_snapshot_date="2026-06-21",
        usd_source_frame=mock_usd_broad_source_frame(),
        usd_snapshot_date="2026-06-21",
    )

    with report_csv.open("r", encoding="utf-8", newline="") as handle:
        result_rows = list(csv.DictReader(handle))
    with summary_csv.open("r", encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))

    assert result.status == "completed"
    assert len(result.results) == 16
    assert len(result_rows) == 16
    assert len(summary_rows) == 8
    assert {row["task_id"] for row in result_rows} == {
        "front_end_spread_widening_v0",
        "synthetic_event_response_v0",
        "synthetic_market_direction_v0",
        "usd_afe_vs_eme_relative_direction_v0",
        "usd_broad_direction_v0",
        "yield_curve_10y3mo_steepening_v0",
        "yield_curve_10y2y_steepening_v0",
        "yield_direction_treasury10y_v0",
    }
    assert {row["run_type"] for row in result_rows} == {"agent"}
    assert sorted(row["agent_id"] for row in summary_rows) == [
        "pilot_curve3mo_agent",
        "pilot_curve_agent",
        "pilot_event_agent",
        "pilot_front_end_agent",
        "pilot_market_agent",
        "pilot_treasury_agent",
        "pilot_usd_agent",
        "pilot_usd_agent",
    ]
    assert {row["run_count"] for row in summary_rows} == {"2"}
    assert {row["score.overall_score.count"] for row in summary_rows} == {"2"}
    assert report_md.exists()
    assert "synthetic_event_response_v0" in summary_md.read_text(encoding="utf-8")
    assert "synthetic_market_direction_v0" in summary_md.read_text(encoding="utf-8")
    assert "yield_direction_treasury10y_v0" in summary_md.read_text(encoding="utf-8")
    assert "yield_curve_10y2y_steepening_v0" in summary_md.read_text(encoding="utf-8")
    assert "yield_curve_10y3mo_steepening_v0" in summary_md.read_text(encoding="utf-8")
    assert "front_end_spread_widening_v0" in summary_md.read_text(encoding="utf-8")
    assert "usd_afe_vs_eme_relative_direction_v0" in summary_md.read_text(encoding="utf-8")
    assert "usd_broad_direction_v0" in summary_md.read_text(encoding="utf-8")


def test_pilot_protocol_runs_combined_baseline_and_agent_evaluations(tmp_path: Path):
    market_agent_script = tmp_path / "protocol_market_agent.py"
    market_agent_script.write_text(
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

(submission_dir / "writeup.md").write_text("Protocol market agent.\\n", encoding="utf-8")
(submission_dir / "notebook.ipynb").write_text(
    json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}),
    encoding="utf-8",
)
""".lstrip(),
        encoding="utf-8",
    )
    event_agent_script = tmp_path / "protocol_event_agent.py"
    event_agent_script.write_text(
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

(submission_dir / "writeup.md").write_text("Protocol event agent.\\n", encoding="utf-8")
(submission_dir / "notebook.ipynb").write_text(
    json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}),
    encoding="utf-8",
)
""".lstrip(),
        encoding="utf-8",
    )
    treasury_agent_script = tmp_path / "protocol_treasury_agent.py"
    treasury_agent_script.write_text(
        """
import csv
import json
import os
from pathlib import Path

train_public_path = Path(os.environ["FINDS_TRAIN_PUBLIC_PATH"])
features_path = Path(os.environ["FINDS_HOLDOUT_FEATURES_PATH"])
submission_dir = Path(os.environ["FINDS_SUBMISSION_DIR"])
submission_dir.mkdir(parents=True, exist_ok=True)

with train_public_path.open("r", encoding="utf-8", newline="") as source:
    train_rows = list(csv.DictReader(source))
train_mean = sum(float(row["next_day_yield_up"]) for row in train_rows) / len(train_rows)
probability = 0.63 if train_mean >= 0.5 else 0.37

with features_path.open("r", encoding="utf-8", newline="") as source:
    rows = list(csv.DictReader(source))

with (submission_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=["row_id", "prediction", "probability"])
    writer.writeheader()
    for row in rows:
        writer.writerow({
            "row_id": row["row_id"],
            "prediction": 1 if probability >= 0.5 else 0,
            "probability": probability,
        })

(submission_dir / "writeup.md").write_text("Protocol treasury agent.\\n", encoding="utf-8")
(submission_dir / "notebook.ipynb").write_text(
    json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}),
    encoding="utf-8",
)
""".lstrip(),
        encoding="utf-8",
    )
    curve_agent_script = tmp_path / "protocol_curve_agent.py"
    curve_agent_script.write_text(
        """
import csv
import json
import os
from pathlib import Path

train_public_path = Path(os.environ["FINDS_TRAIN_PUBLIC_PATH"])
features_path = Path(os.environ["FINDS_HOLDOUT_FEATURES_PATH"])
submission_dir = Path(os.environ["FINDS_SUBMISSION_DIR"])
submission_dir.mkdir(parents=True, exist_ok=True)

with train_public_path.open("r", encoding="utf-8", newline="") as source:
    train_rows = list(csv.DictReader(source))
train_mean = sum(float(row["next_day_curve_steepening"]) for row in train_rows) / len(train_rows)
probability = 0.64 if train_mean >= 0.5 else 0.36

with features_path.open("r", encoding="utf-8", newline="") as source:
    rows = list(csv.DictReader(source))

with (submission_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=["row_id", "prediction", "probability"])
    writer.writeheader()
    for row in rows:
        writer.writerow({
            "row_id": row["row_id"],
            "prediction": 1 if probability >= 0.5 else 0,
            "probability": probability,
        })

(submission_dir / "writeup.md").write_text("Protocol yield curve agent.\\n", encoding="utf-8")
(submission_dir / "notebook.ipynb").write_text(
    json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}),
    encoding="utf-8",
)
""".lstrip(),
        encoding="utf-8",
    )
    curve3mo_agent_script = tmp_path / "protocol_curve3mo_agent.py"
    curve3mo_agent_script.write_text(
        """
import csv
import json
import os
from pathlib import Path

train_public_path = Path(os.environ["FINDS_TRAIN_PUBLIC_PATH"])
features_path = Path(os.environ["FINDS_HOLDOUT_FEATURES_PATH"])
submission_dir = Path(os.environ["FINDS_SUBMISSION_DIR"])
submission_dir.mkdir(parents=True, exist_ok=True)

with train_public_path.open("r", encoding="utf-8", newline="") as source:
    train_rows = list(csv.DictReader(source))
train_mean = sum(float(row["next_day_curve_10y3mo_steepening"]) for row in train_rows) / len(train_rows)
probability = 0.64 if train_mean >= 0.5 else 0.36

with features_path.open("r", encoding="utf-8", newline="") as source:
    rows = list(csv.DictReader(source))

with (submission_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=["row_id", "prediction", "probability"])
    writer.writeheader()
    for row in rows:
        writer.writerow({
            "row_id": row["row_id"],
            "prediction": 1 if probability >= 0.5 else 0,
            "probability": probability,
        })

(submission_dir / "writeup.md").write_text("Protocol yield curve 10Y-3M agent.\\n", encoding="utf-8")
(submission_dir / "notebook.ipynb").write_text(
    json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}),
    encoding="utf-8",
)
""".lstrip(),
        encoding="utf-8",
    )
    front_end_agent_script = tmp_path / "protocol_front_end_agent.py"
    front_end_agent_script.write_text(
        """
import csv
import json
import os
from pathlib import Path

train_public_path = Path(os.environ["FINDS_TRAIN_PUBLIC_PATH"])
features_path = Path(os.environ["FINDS_HOLDOUT_FEATURES_PATH"])
submission_dir = Path(os.environ["FINDS_SUBMISSION_DIR"])
submission_dir.mkdir(parents=True, exist_ok=True)

with train_public_path.open("r", encoding="utf-8", newline="") as source:
    train_rows = list(csv.DictReader(source))
train_mean = sum(float(row["next_day_front_end_widening"]) for row in train_rows) / len(train_rows)
probability = 0.60 if train_mean >= 0.5 else 0.40

with features_path.open("r", encoding="utf-8", newline="") as source:
    rows = list(csv.DictReader(source))

with (submission_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=["row_id", "prediction", "probability"])
    writer.writeheader()
    for row in rows:
        writer.writerow({
            "row_id": row["row_id"],
            "prediction": 1 if probability >= 0.5 else 0,
            "probability": probability,
        })

(submission_dir / "writeup.md").write_text("Protocol front-end agent.\\n", encoding="utf-8")
(submission_dir / "notebook.ipynb").write_text(
    json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}),
    encoding="utf-8",
)
""".lstrip(),
        encoding="utf-8",
    )
    usd_agent_script = tmp_path / "protocol_usd_agent.py"
    usd_agent_script.write_text(
        """
import csv
import json
import os
from pathlib import Path

train_public_path = Path(os.environ["FINDS_TRAIN_PUBLIC_PATH"])
features_path = Path(os.environ["FINDS_HOLDOUT_FEATURES_PATH"])
submission_dir = Path(os.environ["FINDS_SUBMISSION_DIR"])
submission_dir.mkdir(parents=True, exist_ok=True)

with train_public_path.open("r", encoding="utf-8", newline="") as source:
    train_rows = list(csv.DictReader(source))
label_column = (
    "next_day_afe_outperforms_eme"
    if os.environ["FINDS_TASK_ID"] == "usd_afe_vs_eme_relative_direction_v0"
    else "next_day_usd_broad_up"
)
train_mean = sum(float(row[label_column]) for row in train_rows) / len(train_rows)
probability = 0.62 if train_mean >= 0.5 else 0.38

with features_path.open("r", encoding="utf-8", newline="") as source:
    rows = list(csv.DictReader(source))

with (submission_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=["row_id", "prediction", "probability"])
    writer.writeheader()
    for row in rows:
        writer.writerow({
            "row_id": row["row_id"],
            "prediction": 1 if probability >= 0.5 else 0,
            "probability": probability,
        })

(submission_dir / "writeup.md").write_text("Protocol USD agent.\\n", encoding="utf-8")
(submission_dir / "notebook.ipynb").write_text(
    json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}),
    encoding="utf-8",
)
""".lstrip(),
        encoding="utf-8",
    )
    runs_root = tmp_path / "runs"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"

    run_synthetic_market_agent_command(
        agent_id="stale_market_agent",
        agent_version="0.0.1",
        agent_command=[sys.executable, str(market_agent_script)],
        seed=129,
        data_output_dir=tmp_path / "data" / "market" / "stale_raw",
        private_dir=tmp_path / "data" / "market" / "stale_private",
        run_dir=runs_root / "synthetic_market_direction_v0" / "stale_market_agent",
        run_label="stale_market_001",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command_timeout_seconds=60,
    )

    result = run_pilot_protocol(
        market_agent_id="protocol_market_agent",
        market_agent_version="0.0.1",
        market_agent_command=[sys.executable, str(market_agent_script)],
        event_agent_id="protocol_event_agent",
        event_agent_version="0.0.1",
        event_agent_command=[sys.executable, str(event_agent_script)],
        treasury_agent_id="protocol_treasury_agent",
        treasury_agent_version="0.0.1",
        treasury_agent_command=[sys.executable, str(treasury_agent_script)],
        curve_agent_id="protocol_curve_agent",
        curve_agent_version="0.0.1",
        curve_agent_command=[sys.executable, str(curve_agent_script)],
        curve3mo_agent_id="protocol_curve3mo_agent",
        curve3mo_agent_version="0.0.1",
        curve3mo_agent_command=[sys.executable, str(curve3mo_agent_script)],
        front_end_agent_id="protocol_front_end_agent",
        front_end_agent_version="0.0.1",
        front_end_agent_command=[sys.executable, str(front_end_agent_script)],
        usd_agent_id="protocol_usd_agent",
        usd_agent_version="0.0.1",
        usd_agent_command=[sys.executable, str(usd_agent_script)],
        market_seed=131,
        event_seed=141,
        treasury_seed=151,
        curve_seed=157,
        curve3mo_seed=158,
        front_end_seed=159,
        usd_seed=161,
        repeat=2,
        run_label_prefix="pilot_protocol",
        market_data_output_dir=tmp_path / "data" / "market" / "raw",
        market_private_dir=tmp_path / "data" / "market" / "private",
        event_data_output_dir=tmp_path / "data" / "event" / "raw",
        event_private_dir=tmp_path / "data" / "event" / "private",
        treasury_data_output_dir=tmp_path / "data" / "treasury" / "raw",
        treasury_private_dir=tmp_path / "data" / "treasury" / "private",
        curve_data_output_dir=tmp_path / "data" / "curve" / "raw",
        curve_private_dir=tmp_path / "data" / "curve" / "private",
        curve3mo_data_output_dir=tmp_path / "data" / "curve3mo" / "raw",
        curve3mo_private_dir=tmp_path / "data" / "curve3mo" / "private",
        front_end_data_output_dir=tmp_path / "data" / "front_end" / "raw",
        front_end_private_dir=tmp_path / "data" / "front_end" / "private",
        usd_data_output_dir=tmp_path / "data" / "usd" / "raw",
        usd_private_dir=tmp_path / "data" / "usd" / "private",
        runs_root=runs_root,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
        execute_notebook=False,
        command_timeout_seconds=60,
        command="test pilot protocol",
        treasury_source_frame=mock_treasury_source_frame(),
        treasury_snapshot_date="2026-06-21",
        curve_source_frame=mock_treasury_source_frame(),
        curve_snapshot_date="2026-06-21",
        curve3mo_source_frame=mock_treasury_source_frame(),
        curve3mo_snapshot_date="2026-06-21",
        front_end_source_frame=mock_treasury_source_frame(),
        front_end_snapshot_date="2026-06-21",
        usd_source_frame=mock_usd_broad_source_frame(),
        usd_snapshot_date="2026-06-21",
    )

    with report_csv.open("r", encoding="utf-8", newline="") as handle:
        result_rows = list(csv.DictReader(handle))
    with summary_csv.open("r", encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))

    assert result.status == "completed"
    assert len(result.baseline_result.results) == 54
    assert len(result.agent_result.results) == 16
    assert len(result.results) == 70
    assert len(result_rows) == 70
    assert len(summary_rows) == 35
    assert {row["run_type"] for row in result_rows} == {"agent", "baseline"}
    assert {row["task_id"] for row in result_rows} == {
        "front_end_spread_widening_v0",
        "synthetic_event_response_v0",
        "synthetic_market_direction_v0",
        "usd_afe_vs_eme_relative_direction_v0",
        "usd_broad_direction_v0",
        "yield_curve_10y3mo_steepening_v0",
        "yield_curve_10y2y_steepening_v0",
        "yield_direction_treasury10y_v0",
    }
    assert "stale_market_agent" not in {row["agent_id"] for row in result_rows}
    assert "stale_market_agent" not in {row["agent_id"] for row in summary_rows}
    assert {row["run_count"] for row in summary_rows} == {"2"}
    assert {row["score.overall_score.count"] for row in summary_rows} == {"2"}
    assert report_md.exists()
    assert "protocol_market_agent" in summary_md.read_text(encoding="utf-8")
    assert "protocol_curve_agent" in summary_md.read_text(encoding="utf-8")
    assert "protocol_curve3mo_agent" in summary_md.read_text(encoding="utf-8")
    assert "protocol_front_end_agent" in summary_md.read_text(encoding="utf-8")
    assert "protocol_treasury_agent" in summary_md.read_text(encoding="utf-8")
    assert "protocol_usd_agent" in summary_md.read_text(encoding="utf-8")
    assert "momentum_baseline" in summary_md.read_text(encoding="utf-8")
    assert "yield_direction_treasury10y_v0" in summary_md.read_text(encoding="utf-8")
    assert "yield_curve_10y2y_steepening_v0" in summary_md.read_text(encoding="utf-8")
    assert "yield_curve_10y3mo_steepening_v0" in summary_md.read_text(encoding="utf-8")
    assert "front_end_spread_widening_v0" in summary_md.read_text(encoding="utf-8")
    assert "usd_afe_vs_eme_relative_direction_v0" in summary_md.read_text(encoding="utf-8")
    assert "usd_broad_direction_v0" in summary_md.read_text(encoding="utf-8")


def test_pilot_protocol_clean_existing_runs_clears_stale_outputs_once(tmp_path: Path, monkeypatch):
    calls: dict[str, dict[str, object]] = {}
    runs_root = tmp_path / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)
    stale_run_marker = runs_root / "stale.txt"
    stale_run_marker.write_text("stale\n", encoding="utf-8")
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"
    summary_csv = tmp_path / "reports" / "run_summary.csv"
    summary_md = tmp_path / "reports" / "run_summary.md"
    for output_path in (report_csv, report_md, summary_csv, summary_md):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("stale\n", encoding="utf-8")

    def fake_baseline_suite(**kwargs):
        calls["baseline"] = kwargs
        assert kwargs["clean_existing_runs"] is False
        assert not stale_run_marker.exists()
        assert not Path(kwargs["summary_csv_path"]).exists()
        return BaselineSuiteResult(results=[])

    def fake_agent_suite(**kwargs):
        calls["agent"] = kwargs
        assert kwargs["clean_existing_runs"] is False
        assert not stale_run_marker.exists()
        assert not Path(kwargs["summary_csv_path"]).exists()
        return AgentSuiteResult(results=[])

    def fake_write_benchmark_reports_for_results(**kwargs):
        calls["reports"] = kwargs
        return report_csv, report_md, summary_csv, summary_md

    monkeypatch.setattr("finds_agentbench.pipelines.run_pilot_baseline_suite", fake_baseline_suite)
    monkeypatch.setattr("finds_agentbench.pipelines.run_pilot_agent_suite", fake_agent_suite)
    monkeypatch.setattr(
        "finds_agentbench.pipelines.write_benchmark_reports_for_results",
        fake_write_benchmark_reports_for_results,
    )

    result = run_pilot_protocol(
        market_agent_id="market_agent",
        market_agent_version="0.0.1",
        market_agent_command="python market_agent.py",
        event_agent_id="event_agent",
        event_agent_version="0.0.1",
        event_agent_command="python event_agent.py",
        treasury_agent_id="treasury_agent",
        treasury_agent_version="0.0.1",
        treasury_agent_command="python treasury_agent.py",
        curve_agent_id="curve_agent",
        curve_agent_version="0.0.1",
        curve_agent_command="python curve_agent.py",
        curve3mo_agent_id="curve3mo_agent",
        curve3mo_agent_version="0.0.1",
        curve3mo_agent_command="python curve3mo_agent.py",
        front_end_agent_id="front_end_agent",
        front_end_agent_version="0.0.1",
        front_end_agent_command="python front_end_agent.py",
        usd_agent_id="usd_agent",
        usd_agent_version="0.0.1",
        usd_agent_command="python usd_agent.py",
        runs_root=runs_root,
        clean_existing_runs=True,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_md,
    )

    assert result.status == "completed"
    assert calls["baseline"]["runs_root"] == runs_root
    assert calls["agent"]["runs_root"] == runs_root
    assert calls["reports"]["results"] == []
