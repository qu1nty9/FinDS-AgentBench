import json
from pathlib import Path

from finds_agentbench.pipelines import (
    run_synthetic_market_logistic_pipeline,
    run_synthetic_market_momentum_pipeline,
)
from finds_agentbench.runs import load_run_manifest, validate_run_manifest


def test_run_synthetic_market_momentum_pipeline(tmp_path: Path):
    run_dir = tmp_path / "runs" / "synthetic_market_direction_v0" / "momentum_baseline"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"

    result = run_synthetic_market_momentum_pipeline(
        data_output_dir=tmp_path / "data" / "raw",
        private_dir=tmp_path / "data" / "private",
        run_dir=run_dir,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
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

    score = json.loads(result.score_path.read_text(encoding="utf-8"))
    validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
    manifest = load_run_manifest(result.manifest_path)

    assert score["execution_success"] == 1.0
    assert validation["ok"] is True
    assert validation["methodology_findings"] == []
    assert validate_run_manifest(manifest).ok
    assert manifest["scores"]["overall_score"] == score["overall_score"]
    assert "score.overall_score" in report_md.read_text(encoding="utf-8")


def test_run_synthetic_market_logistic_pipeline(tmp_path: Path):
    run_dir = tmp_path / "runs" / "synthetic_market_direction_v0" / "logistic_baseline"
    report_csv = tmp_path / "reports" / "run_results.csv"
    report_md = tmp_path / "reports" / "run_results.md"

    result = run_synthetic_market_logistic_pipeline(
        data_output_dir=tmp_path / "data" / "raw",
        private_dir=tmp_path / "data" / "private",
        run_dir=run_dir,
        report_csv_path=report_csv,
        report_markdown_path=report_md,
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
