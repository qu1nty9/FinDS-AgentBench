import json
from pathlib import Path

from finds_agentbench.paper_artifacts import build_paper_artifacts


def test_build_paper_artifacts_writes_tables_figures_and_readme(tmp_path: Path):
    reference_results = {
        "benchmark_id": "finds_agentbench_pilot_v0",
        "sections": [
            {
                "section_id": "pilot_baseline_suite",
                "title": "Pilot Baseline Suite",
                "rows": [
                    {
                        "task_id": "synthetic_market_direction_v0",
                        "agent_id": "momentum_baseline",
                        "run_type": "baseline",
                        "run_count": 3,
                        "completed_count": 3,
                        "score.overall_score.mean": 0.521015,
                        "score.overall_score.std": 0.018434,
                        "score.balanced_accuracy.mean": 0.521015,
                        "score.balanced_accuracy.std": 0.018434,
                        "score.roc_auc.mean": 0.517726,
                        "score.roc_auc.std": 0.023536,
                    },
                    {
                        "task_id": "yield_curve_10y3mo_steepening_v0",
                        "agent_id": "treasury_curve_10y3mo_research_sweep_env_agent",
                        "run_type": "agent",
                        "run_count": 3,
                        "completed_count": 3,
                        "score.overall_score.mean": 0.517247,
                        "score.overall_score.std": 0.0,
                        "score.balanced_accuracy.mean": 0.517247,
                        "score.balanced_accuracy.std": 0.0,
                        "score.roc_auc.mean": 0.526163,
                        "score.roc_auc.std": 0.0,
                    },
                ],
            }
        ],
    }
    reference_path = tmp_path / "reference_results.json"
    reference_path.write_text(json.dumps(reference_results), encoding="utf-8")

    written = build_paper_artifacts(
        reference_results_path=reference_path,
        output_dir=tmp_path / "paper_artifacts",
    )

    readme = (tmp_path / "paper_artifacts" / "README.md").read_text(encoding="utf-8")
    latex = (tmp_path / "paper_artifacts" / "tables" / "pilot_baseline_suite.tex").read_text(
        encoding="utf-8"
    )
    svg = (
        tmp_path / "paper_artifacts" / "figures" / "pilot_baseline_suite_overall_score.svg"
    ).read_text(encoding="utf-8")

    assert written["readme"].exists()
    assert "\\begin{table}[t]" in latex
    assert "Synthetic Market" in latex
    assert "Treasury 10Y-3M Curve" in latex
    assert "Treasury 10Y-3M Sweep Env-Agent" in latex
    assert "0.521 \\pm 0.018" in latex
    assert "<svg" in svg
    assert "Pilot Baseline Suite" in svg
    assert "Momentum" in svg
    assert "Treasury 10Y-3M Curve" in svg
    assert "paper-ready exports" in readme.lower()
