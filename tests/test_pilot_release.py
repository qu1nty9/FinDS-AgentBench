from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from finds_agentbench.pilot_release import build_pilot_release


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
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [",".join(header)]
    for row in rows:
        lines.append(",".join(row[column] for column in header))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def touch_report_artifacts(*, results_csv: Path, results_markdown: Path, summary_csv: Path, summary_markdown: Path) -> None:
    results_csv.parent.mkdir(parents=True, exist_ok=True)
    results_csv.write_text("task_id,agent_id\n", encoding="utf-8")
    results_markdown.write_text("| task_id | agent_id |\n| --- | --- |\n", encoding="utf-8")
    summary_markdown.write_text("| task_id | agent_id |\n| --- | --- |\n", encoding="utf-8")
    if not summary_csv.exists():
        raise AssertionError("summary_csv must be written before touch_report_artifacts")


def test_build_pilot_release_runs_suites_and_rebuilds_release_artifacts(
    tmp_path: Path,
    monkeypatch,
):
    calls: dict[str, dict[str, object]] = {}

    baseline_rows = [
        {
            "task_id": "synthetic_market_direction_v0",
            "agent_id": "momentum_baseline",
            "run_type": "baseline",
            "run_count": "2",
            "completed_count": "2",
            "score.overall_score.mean": "0.52",
            "score.overall_score.std": "0.01",
            "score.balanced_accuracy.mean": "0.52",
            "score.balanced_accuracy.std": "0.01",
            "score.roc_auc.mean": "0.51",
            "score.roc_auc.std": "0.02",
        }
    ]
    agent_rows = [
        {
            "task_id": "synthetic_market_direction_v0",
            "agent_id": "market_research_sweep_env_agent",
            "run_type": "agent",
            "run_count": "2",
            "completed_count": "2",
            "score.overall_score.mean": "0.51",
            "score.overall_score.std": "0.02",
            "score.balanced_accuracy.mean": "0.51",
            "score.balanced_accuracy.std": "0.02",
            "score.roc_auc.mean": "0.52",
            "score.roc_auc.std": "0.02",
        }
    ]
    protocol_rows = [*baseline_rows, *agent_rows]

    def fake_baseline_suite(**kwargs):
        calls["baseline"] = kwargs
        write_summary_csv(kwargs["summary_csv_path"], baseline_rows)
        touch_report_artifacts(
            results_csv=kwargs["report_csv_path"],
            results_markdown=kwargs["report_markdown_path"],
            summary_csv=kwargs["summary_csv_path"],
            summary_markdown=kwargs["summary_markdown_path"],
        )
        return SimpleNamespace(status="completed")

    def fake_agent_suite(**kwargs):
        calls["agent"] = kwargs
        write_summary_csv(kwargs["summary_csv_path"], agent_rows)
        touch_report_artifacts(
            results_csv=kwargs["report_csv_path"],
            results_markdown=kwargs["report_markdown_path"],
            summary_csv=kwargs["summary_csv_path"],
            summary_markdown=kwargs["summary_markdown_path"],
        )
        return SimpleNamespace(status="completed")

    def fake_protocol_suite(**kwargs):
        calls["protocol"] = kwargs
        write_summary_csv(kwargs["summary_csv_path"], protocol_rows)
        touch_report_artifacts(
            results_csv=kwargs["report_csv_path"],
            results_markdown=kwargs["report_markdown_path"],
            summary_csv=kwargs["summary_csv_path"],
            summary_markdown=kwargs["summary_markdown_path"],
        )
        return SimpleNamespace(status="completed")

    def fake_build_benchmark_manifest(**kwargs):
        output_root = Path(kwargs["output_root"])
        output_root.mkdir(parents=True, exist_ok=True)
        manifest_path = output_root / "manifest.json"
        readme_path = output_root / "README.md"
        manifest_path.write_text(json.dumps({"ok": True}) + "\n", encoding="utf-8")
        readme_path.write_text("# release\n", encoding="utf-8")
        cards_index = output_root / "cards_index.md"
        data_index = output_root / "data_index.md"
        cards_index.write_text("# cards\n", encoding="utf-8")
        data_index.write_text("# data\n", encoding="utf-8")
        return SimpleNamespace(
            manifest_path=manifest_path,
            readme_path=readme_path,
            cards_index_path=cards_index,
            data_manifests_readme_path=data_index,
        )

    monkeypatch.setattr("finds_agentbench.pilot_release.run_pilot_baseline_suite", fake_baseline_suite)
    monkeypatch.setattr("finds_agentbench.pilot_release.run_pilot_agent_suite", fake_agent_suite)
    monkeypatch.setattr("finds_agentbench.pilot_release.run_pilot_protocol", fake_protocol_suite)
    monkeypatch.setattr(
        "finds_agentbench.pilot_release.build_benchmark_manifest",
        fake_build_benchmark_manifest,
    )

    result = build_pilot_release(
        curve3mo_agent_id="test_curve3mo_agent",
        curve3mo_agent_version="0.0.2",
        curve3mo_agent_command="python curve3mo_agent.py",
        curve3mo_seed=233,
        curve3mo_task_path=tmp_path / "tasks" / "yield_curve_10y3mo_steepening_v0.yaml",
        curve3mo_data_output_dir=tmp_path / "data" / "curve3mo" / "raw",
        curve3mo_private_dir=tmp_path / "data" / "curve3mo" / "private",
        repeat=2,
        reports_root=tmp_path / "reports",
        release_output_root=tmp_path / "release",
        reference_results_markdown_path=tmp_path / "release" / "reference_results.md",
        reference_results_json_path=tmp_path / "release" / "reference_results.json",
        paper_artifacts_output_dir=tmp_path / "release" / "paper_artifacts",
        statistical_artifacts_output_dir=tmp_path / "release" / "statistical_artifacts",
        cards_root=tmp_path / "cards",
        data_manifests_root=tmp_path / "data_manifests",
    )

    assert calls["baseline"]["run_label_prefix"] == "pilot"
    assert calls["baseline"]["curve3mo_seed"] == 233
    assert calls["baseline"]["curve3mo_task_path"] == tmp_path / "tasks" / "yield_curve_10y3mo_steepening_v0.yaml"
    assert calls["baseline"]["curve3mo_data_output_dir"] == tmp_path / "data" / "curve3mo" / "raw"
    assert calls["baseline"]["curve3mo_private_dir"] == tmp_path / "data" / "curve3mo" / "private"
    assert calls["agent"]["run_label_prefix"] == "pilot_agent"
    assert calls["agent"]["curve3mo_agent_id"] == "test_curve3mo_agent"
    assert calls["agent"]["curve3mo_agent_version"] == "0.0.2"
    assert calls["agent"]["curve3mo_agent_command"] == "python curve3mo_agent.py"
    assert calls["agent"]["curve3mo_seed"] == 233
    assert calls["protocol"]["run_label_prefix"] == "pilot_protocol"
    assert calls["protocol"]["curve3mo_agent_id"] == "test_curve3mo_agent"
    assert calls["protocol"]["curve3mo_agent_version"] == "0.0.2"
    assert calls["protocol"]["curve3mo_agent_command"] == "python curve3mo_agent.py"
    assert calls["protocol"]["curve3mo_seed"] == 233
    assert calls["protocol"]["repeat"] == 2
    assert result.reference_results_markdown_path.exists()
    assert result.reference_results_json_path.exists()
    assert result.paper_artifact_paths["readme"].exists()
    assert result.statistical_artifact_paths["readme"].exists()
    assert result.manifest_path.exists()
    assert result.release_readme_path.exists()

    reference_markdown = result.reference_results_markdown_path.read_text(encoding="utf-8")
    reference_payload = json.loads(result.reference_results_json_path.read_text(encoding="utf-8"))
    assert "Combined Pilot Protocol" in reference_markdown
    assert reference_payload["sections"][2]["rows"][1]["agent_id"] == "market_research_sweep_env_agent"
    assert sorted(result.report_paths) == [
        "pilot_agent_results_csv",
        "pilot_agent_results_markdown",
        "pilot_agent_summary_csv",
        "pilot_agent_summary_markdown",
        "pilot_baseline_results_csv",
        "pilot_baseline_results_markdown",
        "pilot_baseline_summary_csv",
        "pilot_baseline_summary_markdown",
        "pilot_protocol_results_csv",
        "pilot_protocol_results_markdown",
        "pilot_protocol_summary_csv",
        "pilot_protocol_summary_markdown",
    ]


def test_build_pilot_release_cleans_existing_outputs_and_forwards_clean_flags(
    tmp_path: Path,
    monkeypatch,
):
    calls: dict[str, dict[str, object]] = {}

    baseline_rows = [
        {
            "task_id": "synthetic_market_direction_v0",
            "agent_id": "momentum_baseline",
            "run_type": "baseline",
            "run_count": "1",
            "completed_count": "1",
            "score.overall_score.mean": "0.52",
            "score.overall_score.std": "0.00",
            "score.balanced_accuracy.mean": "0.52",
            "score.balanced_accuracy.std": "0.00",
            "score.roc_auc.mean": "0.51",
            "score.roc_auc.std": "0.00",
        }
    ]
    agent_rows = [
        {
            "task_id": "synthetic_market_direction_v0",
            "agent_id": "market_research_sweep_env_agent",
            "run_type": "agent",
            "run_count": "1",
            "completed_count": "1",
            "score.overall_score.mean": "0.51",
            "score.overall_score.std": "0.00",
            "score.balanced_accuracy.mean": "0.51",
            "score.balanced_accuracy.std": "0.00",
            "score.roc_auc.mean": "0.52",
            "score.roc_auc.std": "0.00",
        }
    ]
    protocol_rows = [*baseline_rows, *agent_rows]

    tasks_root = tmp_path / "tasks"
    tasks_root.mkdir(parents=True, exist_ok=True)
    (tasks_root / "current_task.yaml").write_text(
        "metadata:\n  task_id: current_task_v0\n",
        encoding="utf-8",
    )

    baseline_runs_root = tmp_path / "runs" / "baseline"
    agent_runs_root = tmp_path / "runs" / "agent"
    protocol_runs_root = tmp_path / "runs" / "protocol"
    for root in (baseline_runs_root, agent_runs_root, protocol_runs_root):
        root.mkdir(parents=True, exist_ok=True)
        (root / "stale.txt").write_text("stale\n", encoding="utf-8")

    reports_root = tmp_path / "reports"
    reports_root.mkdir(parents=True, exist_ok=True)
    stale_report_paths = [
        reports_root / "pilot_baseline_run_summary.csv",
        reports_root / "pilot_agent_run_summary.csv",
        reports_root / "pilot_protocol_run_summary.csv",
    ]
    for report_path in stale_report_paths:
        report_path.write_text("stale\n", encoding="utf-8")

    release_root = tmp_path / "release"
    release_root.mkdir(parents=True, exist_ok=True)
    (release_root / "manifest.json").write_text('{"stale": true}\n', encoding="utf-8")
    (release_root / "README.md").write_text("stale\n", encoding="utf-8")
    reference_markdown_path = release_root / "reference_results.md"
    reference_json_path = release_root / "reference_results.json"
    reference_markdown_path.write_text("stale\n", encoding="utf-8")
    reference_json_path.write_text('{"stale": true}\n', encoding="utf-8")
    paper_artifacts_output_dir = release_root / "paper_artifacts"
    paper_artifacts_output_dir.mkdir(parents=True, exist_ok=True)
    stale_paper_artifact = paper_artifacts_output_dir / "stale.txt"
    stale_paper_artifact.write_text("stale\n", encoding="utf-8")
    statistical_artifacts_output_dir = release_root / "statistical_artifacts"
    statistical_artifacts_output_dir.mkdir(parents=True, exist_ok=True)
    stale_statistical_artifact = statistical_artifacts_output_dir / "stale.txt"
    stale_statistical_artifact.write_text("stale\n", encoding="utf-8")

    cards_root = tmp_path / "cards"
    (cards_root / "tasks").mkdir(parents=True, exist_ok=True)
    (cards_root / "evaluations").mkdir(parents=True, exist_ok=True)
    stale_task_card = cards_root / "tasks" / "stale_task_v0.md"
    stale_evaluation_card = cards_root / "evaluations" / "stale_task_v0.md"
    stale_task_card.write_text("stale\n", encoding="utf-8")
    stale_evaluation_card.write_text("stale\n", encoding="utf-8")
    (cards_root / "task_registry.json").write_text(
        json.dumps([{"task_id": "stale_task_v0"}]) + "\n",
        encoding="utf-8",
    )
    (cards_root / "task_registry.csv").write_text("task_id\nstale_task_v0\n", encoding="utf-8")
    (cards_root / "README.md").write_text("stale\n", encoding="utf-8")

    data_manifests_root = tmp_path / "data_manifests"
    data_manifests_root.mkdir(parents=True, exist_ok=True)
    stale_data_manifest = data_manifests_root / "stale_task_v0.json"
    stale_data_manifest.write_text('{"task_id":"stale_task_v0"}\n', encoding="utf-8")
    (data_manifests_root / "index.json").write_text(
        json.dumps([{"task_id": "stale_task_v0"}]) + "\n",
        encoding="utf-8",
    )
    (data_manifests_root / "index.csv").write_text("task_id\nstale_task_v0\n", encoding="utf-8")
    (data_manifests_root / "README.md").write_text("stale\n", encoding="utf-8")

    def fake_baseline_suite(**kwargs):
        calls["baseline"] = kwargs
        assert kwargs["clean_existing_runs"] is True
        write_summary_csv(kwargs["summary_csv_path"], baseline_rows)
        touch_report_artifacts(
            results_csv=kwargs["report_csv_path"],
            results_markdown=kwargs["report_markdown_path"],
            summary_csv=kwargs["summary_csv_path"],
            summary_markdown=kwargs["summary_markdown_path"],
        )
        return SimpleNamespace(status="completed")

    def fake_agent_suite(**kwargs):
        calls["agent"] = kwargs
        assert kwargs["clean_existing_runs"] is True
        write_summary_csv(kwargs["summary_csv_path"], agent_rows)
        touch_report_artifacts(
            results_csv=kwargs["report_csv_path"],
            results_markdown=kwargs["report_markdown_path"],
            summary_csv=kwargs["summary_csv_path"],
            summary_markdown=kwargs["summary_markdown_path"],
        )
        return SimpleNamespace(status="completed")

    def fake_protocol_suite(**kwargs):
        calls["protocol"] = kwargs
        assert kwargs["clean_existing_runs"] is True
        write_summary_csv(kwargs["summary_csv_path"], protocol_rows)
        touch_report_artifacts(
            results_csv=kwargs["report_csv_path"],
            results_markdown=kwargs["report_markdown_path"],
            summary_csv=kwargs["summary_csv_path"],
            summary_markdown=kwargs["summary_markdown_path"],
        )
        return SimpleNamespace(status="completed")

    def fake_build_benchmark_manifest(**kwargs):
        assert not stale_task_card.exists()
        assert not stale_evaluation_card.exists()
        assert not stale_data_manifest.exists()
        assert not (cards_root / "task_registry.json").exists()
        assert not (data_manifests_root / "index.json").exists()

        output_root = Path(kwargs["output_root"])
        output_root.mkdir(parents=True, exist_ok=True)
        manifest_path = output_root / "manifest.json"
        readme_path = output_root / "README.md"
        manifest_path.write_text(json.dumps({"ok": True}) + "\n", encoding="utf-8")
        readme_path.write_text("# release\n", encoding="utf-8")
        cards_index = output_root / "cards_index.md"
        data_index = output_root / "data_index.md"
        cards_index.write_text("# cards\n", encoding="utf-8")
        data_index.write_text("# data\n", encoding="utf-8")
        return SimpleNamespace(
            manifest_path=manifest_path,
            readme_path=readme_path,
            cards_index_path=cards_index,
            data_manifests_readme_path=data_index,
        )

    monkeypatch.setattr("finds_agentbench.pilot_release.run_pilot_baseline_suite", fake_baseline_suite)
    monkeypatch.setattr("finds_agentbench.pilot_release.run_pilot_agent_suite", fake_agent_suite)
    monkeypatch.setattr("finds_agentbench.pilot_release.run_pilot_protocol", fake_protocol_suite)
    monkeypatch.setattr(
        "finds_agentbench.pilot_release.build_benchmark_manifest",
        fake_build_benchmark_manifest,
    )

    result = build_pilot_release(
        repeat=1,
        tasks_root=tasks_root,
        baseline_runs_root=baseline_runs_root,
        agent_runs_root=agent_runs_root,
        protocol_runs_root=protocol_runs_root,
        reports_root=reports_root,
        release_output_root=release_root,
        reference_results_markdown_path=reference_markdown_path,
        reference_results_json_path=reference_json_path,
        paper_artifacts_output_dir=paper_artifacts_output_dir,
        statistical_artifacts_output_dir=statistical_artifacts_output_dir,
        cards_root=cards_root,
        data_manifests_root=data_manifests_root,
        clean_existing_outputs=True,
    )

    assert calls["baseline"]["clean_existing_runs"] is True
    assert calls["agent"]["clean_existing_runs"] is True
    assert calls["protocol"]["clean_existing_runs"] is True
    assert not stale_paper_artifact.exists()
    assert not stale_statistical_artifact.exists()
    assert not stale_task_card.exists()
    assert not stale_evaluation_card.exists()
    assert not stale_data_manifest.exists()
    assert result.reference_results_markdown_path.exists()
    assert result.reference_results_json_path.exists()
    assert result.paper_artifact_paths["readme"].exists()
    assert result.statistical_artifact_paths["readme"].exists()
