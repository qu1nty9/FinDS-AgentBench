import json
from pathlib import Path

from finds_agentbench.pipelines import run_synthetic_market_momentum_pipeline
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
    assert validate_run_manifest(manifest).ok
    assert manifest["scores"]["overall_score"] == score["overall_score"]
    assert "score.overall_score" in report_md.read_text(encoding="utf-8")

