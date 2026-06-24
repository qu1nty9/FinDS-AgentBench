import json
from pathlib import Path

import pytest

from finds_agentbench.reference_results import (
    AGENT_SUITE_DESCRIPTION,
    BASELINE_SUITE_DESCRIPTION,
    PILOT_PROTOCOL_DESCRIPTION,
    load_csv_rows,
    render_reference_results_markdown,
    write_reference_results_snapshot,
)


def write_summary_csv(path: Path, rows: list[dict[str, str]]) -> None:
    header = [
        "task_id",
        "agent_id",
        "run_type",
        "run_count",
        "completed_count",
        "score.overall_score.mean",
        "score.overall_score.std",
        "score.balanced_accuracy.mean",
        "score.balanced_accuracy.std",
        "score.roc_auc.mean",
        "score.roc_auc.std",
    ]
    lines = [",".join(header)]
    for row in rows:
        lines.append(",".join(row[column] for column in header))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_write_reference_results_snapshot_renders_sections(tmp_path: Path):
    baseline_csv = tmp_path / "baseline.csv"
    agent_csv = tmp_path / "agent.csv"
    protocol_csv = tmp_path / "protocol.csv"
    write_summary_csv(
        baseline_csv,
        [
            {
                "task_id": "synthetic_market_direction_v0",
                "agent_id": "momentum_baseline",
                "run_type": "baseline",
                "run_count": "3",
                "completed_count": "3",
                "score.overall_score.mean": "0.52",
                "score.overall_score.std": "0.01",
                "score.balanced_accuracy.mean": "0.52",
                "score.balanced_accuracy.std": "0.01",
                "score.roc_auc.mean": "0.51",
                "score.roc_auc.std": "0.02",
            }
        ],
    )
    write_summary_csv(
        agent_csv,
        [
            {
                "task_id": "yield_direction_treasury10y_v0",
                "agent_id": "treasury_logistic_env_agent",
                "run_type": "agent",
                "run_count": "3",
                "completed_count": "3",
                "score.overall_score.mean": "0.489822",
                "score.overall_score.std": "0.0",
                "score.balanced_accuracy.mean": "0.489822",
                "score.balanced_accuracy.std": "0.0",
                "score.roc_auc.mean": "0.486226",
                "score.roc_auc.std": "0.0",
            }
        ],
    )
    write_summary_csv(
        protocol_csv,
        [
            {
                "task_id": "synthetic_market_direction_v0",
                "agent_id": "momentum_baseline",
                "run_type": "baseline",
                "run_count": "3",
                "completed_count": "3",
                "score.overall_score.mean": "0.52",
                "score.overall_score.std": "0.01",
                "score.balanced_accuracy.mean": "0.52",
                "score.balanced_accuracy.std": "0.01",
                "score.roc_auc.mean": "0.51",
                "score.roc_auc.std": "0.02",
            },
            {
                "task_id": "yield_direction_treasury10y_v0",
                "agent_id": "treasury_logistic_env_agent",
                "run_type": "agent",
                "run_count": "3",
                "completed_count": "3",
                "score.overall_score.mean": "0.489822",
                "score.overall_score.std": "0.0",
                "score.balanced_accuracy.mean": "0.489822",
                "score.balanced_accuracy.std": "0.0",
                "score.roc_auc.mean": "0.486226",
                "score.roc_auc.std": "0.0",
            }
        ],
    )

    markdown_path, json_path = write_reference_results_snapshot(
        output_markdown_path=tmp_path / "reference_results.md",
        output_json_path=tmp_path / "reference_results.json",
        benchmark_id="finds_agentbench_pilot_v0",
        benchmark_version="0.1.0",
        release_stage="pilot",
        treasury_snapshot_date="2026-06-21",
        baseline_rows=load_csv_rows(baseline_csv),
        agent_rows=load_csv_rows(agent_csv),
        protocol_rows=load_csv_rows(protocol_csv),
        baseline_command="python baseline",
        agent_command="python agent",
        protocol_command="python protocol",
        expected_run_count=3,
    )

    markdown = markdown_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "Pilot Reference Results" in markdown
    assert "Treasury Snapshot Date | 2026-06-21" in markdown
    assert "Official command: `python agent`" in markdown
    assert BASELINE_SUITE_DESCRIPTION in markdown
    assert AGENT_SUITE_DESCRIPTION in markdown
    assert PILOT_PROTOCOL_DESCRIPTION in markdown
    assert "| yield_direction_treasury10y_v0 | treasury_logistic_env_agent | agent |" in markdown
    assert payload["benchmark_id"] == "finds_agentbench_pilot_v0"
    assert payload["sections"][1]["section_id"] == "pilot_agent_suite"
    assert payload["sections"][1]["rows"][0]["agent_id"] == "treasury_logistic_env_agent"


def test_render_reference_results_markdown_sorts_rows():
    markdown = render_reference_results_markdown(
        benchmark_id="finds_agentbench_pilot_v0",
        benchmark_version="0.1.0",
        release_stage="pilot",
        treasury_snapshot_date="2026-06-21",
        baseline_rows=[
            {"task_id": "b_task", "agent_id": "z_agent", "run_type": "baseline"},
            {"task_id": "a_task", "agent_id": "a_agent", "run_type": "baseline"},
        ],
        agent_rows=[],
        protocol_rows=[],
        baseline_command="python baseline",
        agent_command="python agent",
        protocol_command="python protocol",
    )

    assert markdown.index("| a_task | a_agent | baseline |") < markdown.index(
        "| b_task | z_agent | baseline |"
    )


def test_write_reference_results_snapshot_rejects_protocol_contamination(tmp_path: Path):
    baseline_rows = [
        {
            "task_id": "synthetic_market_direction_v0",
            "agent_id": "momentum_baseline",
            "run_type": "baseline",
            "run_count": 3,
            "completed_count": 3,
            "score.overall_score.mean": 0.52,
            "score.overall_score.std": 0.01,
            "score.balanced_accuracy.mean": 0.52,
            "score.balanced_accuracy.std": 0.01,
            "score.roc_auc.mean": 0.51,
            "score.roc_auc.std": 0.02,
        }
    ]
    agent_rows = [
        {
            "task_id": "synthetic_market_direction_v0",
            "agent_id": "market_research_sweep_env_agent",
            "run_type": "agent",
            "run_count": 3,
            "completed_count": 3,
            "score.overall_score.mean": 0.51,
            "score.overall_score.std": 0.02,
            "score.balanced_accuracy.mean": 0.51,
            "score.balanced_accuracy.std": 0.02,
            "score.roc_auc.mean": 0.52,
            "score.roc_auc.std": 0.02,
        }
    ]
    protocol_rows = [
        *baseline_rows,
        *agent_rows,
        {
            "task_id": "synthetic_market_direction_v0",
            "agent_id": "momentum_env_agent",
            "run_type": "agent",
            "run_count": 3,
            "completed_count": 3,
            "score.overall_score.mean": 0.49,
            "score.overall_score.std": 0.0,
            "score.balanced_accuracy.mean": 0.49,
            "score.balanced_accuracy.std": 0.0,
            "score.roc_auc.mean": 0.50,
            "score.roc_auc.std": 0.0,
        },
    ]

    with pytest.raises(ValueError, match="unexpected summary rows"):
        write_reference_results_snapshot(
            output_markdown_path=tmp_path / "reference_results.md",
            output_json_path=tmp_path / "reference_results.json",
            benchmark_id="finds_agentbench_pilot_v0",
            benchmark_version="0.1.0",
            release_stage="pilot",
            treasury_snapshot_date="2026-06-21",
            baseline_rows=baseline_rows,
            agent_rows=agent_rows,
            protocol_rows=protocol_rows,
            baseline_command="python baseline",
            agent_command="python agent",
            protocol_command="python protocol",
            expected_run_count=3,
        )


def test_write_reference_results_snapshot_rejects_run_count_mismatch(tmp_path: Path):
    baseline_rows = [
        {
            "task_id": "synthetic_market_direction_v0",
            "agent_id": "momentum_baseline",
            "run_type": "baseline",
            "run_count": 4,
            "completed_count": 4,
            "score.overall_score.mean": 0.52,
            "score.overall_score.std": 0.01,
            "score.balanced_accuracy.mean": 0.52,
            "score.balanced_accuracy.std": 0.01,
            "score.roc_auc.mean": 0.51,
            "score.roc_auc.std": 0.02,
        }
    ]

    with pytest.raises(ValueError, match="run_count=4; expected 3"):
        write_reference_results_snapshot(
            output_markdown_path=tmp_path / "reference_results.md",
            output_json_path=tmp_path / "reference_results.json",
            benchmark_id="finds_agentbench_pilot_v0",
            benchmark_version="0.1.0",
            release_stage="pilot",
            treasury_snapshot_date="2026-06-21",
            baseline_rows=baseline_rows,
            agent_rows=[],
            protocol_rows=[],
            baseline_command="python baseline",
            agent_command="python agent",
            protocol_command="python protocol",
            expected_run_count=3,
        )
