import csv
import json
from pathlib import Path

from finds_agentbench.statistical_artifacts import (
    build_agent_vs_best_baseline_rows,
    build_statistical_artifacts,
    build_summary_uncertainty_rows,
    exact_two_sided_sign_test_p_value,
    release_facing_source_path,
)


def write_protocol_results(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "task_id",
        "agent_id",
        "run_type",
        "status",
        "score.overall_score",
        "score.balanced_accuracy",
        "score.roc_auc",
        "trace.repeat_index",
        "trace.seed",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sample_protocol_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    baseline_a_scores = [0.50, 0.51, 0.49]
    baseline_b_scores = [0.55, 0.56, 0.54]
    agent_scores = [0.57, 0.58, 0.59]
    for index, (baseline_a, baseline_b, agent) in enumerate(
        zip(baseline_a_scores, baseline_b_scores, agent_scores, strict=True),
        start=1,
    ):
        rows.extend(
            [
                {
                    "task_id": "task_v0",
                    "agent_id": "baseline_a",
                    "run_type": "baseline",
                    "status": "completed",
                    "score.overall_score": baseline_a,
                    "score.balanced_accuracy": baseline_a,
                    "score.roc_auc": baseline_a,
                    "trace.repeat_index": index,
                    "trace.seed": 10 + index,
                },
                {
                    "task_id": "task_v0",
                    "agent_id": "baseline_b",
                    "run_type": "baseline",
                    "status": "completed",
                    "score.overall_score": baseline_b,
                    "score.balanced_accuracy": baseline_b,
                    "score.roc_auc": baseline_b,
                    "trace.repeat_index": index,
                    "trace.seed": 20 + index,
                },
                {
                    "task_id": "task_v0",
                    "agent_id": "research_agent",
                    "run_type": "agent",
                    "status": "completed",
                    "score.overall_score": agent,
                    "score.balanced_accuracy": agent,
                    "score.roc_auc": agent,
                    "trace.repeat_index": index,
                    "trace.seed": 30 + index,
                },
            ]
        )
    rows.append(
        {
            "task_id": "task_v0",
            "agent_id": "failed_agent",
            "run_type": "agent",
            "status": "failed",
            "score.overall_score": 1.0,
            "score.balanced_accuracy": 1.0,
            "score.roc_auc": 1.0,
            "trace.repeat_index": 1,
            "trace.seed": 99,
        }
    )
    return rows


def test_summary_uncertainty_rows_use_completed_numeric_values():
    rows = sample_protocol_rows()

    summary_rows = build_summary_uncertainty_rows(rows, metrics=["score.overall_score"])

    agent_row = next(row for row in summary_rows if row["agent_id"] == "research_agent")
    assert agent_row["n"] == 3
    assert round(agent_row["mean"], 6) == 0.58
    assert round(agent_row["std"], 6) == 0.01
    assert agent_row["ci95_low"] < agent_row["mean"] < agent_row["ci95_high"]
    assert not any(row["agent_id"] == "failed_agent" for row in summary_rows)


def test_agent_vs_best_baseline_uses_metric_best_baseline_and_sign_test():
    rows = sample_protocol_rows()

    comparison_rows = build_agent_vs_best_baseline_rows(rows, metrics=["score.overall_score"])

    comparison = comparison_rows[0]
    assert comparison["agent_id"] == "research_agent"
    assert comparison["best_baseline_agent_id"] == "baseline_b"
    assert comparison["paired_count"] == 3
    assert comparison["agent_higher_count"] == 3
    assert comparison["baseline_higher_count"] == 0
    assert comparison["direction"] == "agent_higher"
    assert round(comparison["mean_difference"], 6) == 0.03
    assert comparison["sign_test_p_value"] == 0.25


def test_exact_two_sided_sign_test_handles_ties_and_empty_nonzero_set():
    assert exact_two_sided_sign_test_p_value([0.1, 0.2, 0.3]) == 0.25
    assert exact_two_sided_sign_test_p_value([0.1, -0.2, 0.0]) == 1.0
    assert exact_two_sided_sign_test_p_value([0.0, 0.0]) is None


def test_release_facing_source_path_strips_ephemeral_build_roots():
    assert (
        release_facing_source_path("tmp/check/first/reports/pilot_protocol_run_results.csv")
        == "reports/pilot_protocol_run_results.csv"
    )
    assert (
        release_facing_source_path("reports/release_runs/pilot_protocol_run_results.csv")
        == "reports/release_runs/pilot_protocol_run_results.csv"
    )


def test_build_statistical_artifacts_writes_csv_json_markdown_and_readme(tmp_path: Path):
    protocol_csv = tmp_path / "reports" / "pilot_protocol_run_results.csv"
    write_protocol_results(protocol_csv, sample_protocol_rows())

    written = build_statistical_artifacts(
        protocol_results_csv_path=protocol_csv,
        output_dir=tmp_path / "statistical_artifacts",
    )

    assert written["readme"].exists()
    assert written["summary_uncertainty_csv"].exists()
    assert written["summary_uncertainty_json"].exists()
    assert written["summary_uncertainty_markdown"].exists()
    assert written["agent_vs_best_baseline_csv"].exists()
    assert written["agent_vs_best_baseline_json"].exists()
    assert written["agent_vs_best_baseline_markdown"].exists()
    assert written["summary_uncertainty_latex"].exists()
    assert written["agent_vs_best_baseline_latex"].exists()
    assert written["statistical_methods_markdown"].exists()
    assert written["statistical_methods_latex"].exists()

    summary_payload = json.loads(written["summary_uncertainty_json"].read_text(encoding="utf-8"))
    comparison_payload = json.loads(
        written["agent_vs_best_baseline_json"].read_text(encoding="utf-8")
    )
    readme = written["readme"].read_text(encoding="utf-8")
    summary_latex = written["summary_uncertainty_latex"].read_text(encoding="utf-8")
    comparison_latex = written["agent_vs_best_baseline_latex"].read_text(encoding="utf-8")
    methods_latex = written["statistical_methods_latex"].read_text(encoding="utf-8")

    assert summary_payload["metrics"] == [
        "score.overall_score",
        "score.balanced_accuracy",
        "score.roc_auc",
    ]
    assert any(row["agent_id"] == "research_agent" for row in comparison_payload["rows"])
    assert "small repeated-run count" in readme
    assert "agent_vs_best_baseline.csv" in readme
    assert "tables/summary_uncertainty_overall_score.tex" in readme
    assert "methods/statistical_methods.tex" in readme
    assert "\\begin{table}[t]" in summary_latex
    assert "Pilot repeated-run uncertainty" in summary_latex
    assert "research agent" in comparison_latex
    assert "\\label{tab:pilot-agent-vs-best-baseline-score-overall-score}" in comparison_latex
    assert "\\paragraph{Statistical reporting.}" in methods_latex
