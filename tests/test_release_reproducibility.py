import csv
import json
from pathlib import Path

import pytest

from finds_agentbench.release_reproducibility import (
    SUMMARY_REPORT_FILENAMES,
    build_release_repro_paths,
    build_release_artifact_comparison,
    collect_release_artifact_digests,
    compare_release_artifact_digests,
    iter_release_comparison_targets,
    run_release_reproducibility_check,
    validate_summary_run_counts,
    write_release_reproducibility_forensics,
)


def write_summary_csv(path: Path, run_count: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["task_id", "agent_id", "run_count"])
        writer.writeheader()
        writer.writerow(
            {
                "task_id": "synthetic_market_direction_v0",
                "agent_id": "market_research_sweep_env_agent",
                "run_count": run_count,
            }
        )


def test_iter_release_comparison_targets_collects_release_facing_outputs(tmp_path: Path):
    paths = build_release_repro_paths(tmp_path / "run")
    (paths.reports_root / "pilot_protocol_run_summary.csv").parent.mkdir(parents=True, exist_ok=True)
    (paths.reports_root / "pilot_protocol_run_summary.csv").write_text("header\n", encoding="utf-8")
    (paths.reports_root / "pilot_protocol_run_results.csv").write_text("ignored\n", encoding="utf-8")
    (paths.release_output_root / "manifest.json").parent.mkdir(parents=True, exist_ok=True)
    (paths.release_output_root / "manifest.json").write_text("{}\n", encoding="utf-8")
    (paths.release_output_root / "statistical_artifacts").mkdir(parents=True, exist_ok=True)
    (paths.release_output_root / "statistical_artifacts" / "README.md").write_text(
        "# stats\n",
        encoding="utf-8",
    )
    (paths.cards_root / "tasks").mkdir(parents=True, exist_ok=True)
    (paths.cards_root / "tasks" / "synthetic_market_direction_v0.md").write_text(
        "# task\n",
        encoding="utf-8",
    )
    (paths.data_manifests_root / "synthetic_market_direction_v0.json").parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    (paths.data_manifests_root / "synthetic_market_direction_v0.json").write_text(
        "{}\n",
        encoding="utf-8",
    )

    targets = dict(iter_release_comparison_targets(paths))

    assert "reports/pilot_protocol_run_summary.csv" in targets
    assert "release/manifest.json" in targets
    assert "release/statistical_artifacts/README.md" in targets
    assert "cards/tasks/synthetic_market_direction_v0.md" in targets
    assert "data_manifests/synthetic_market_direction_v0.json" in targets
    assert "reports/pilot_protocol_run_results.csv" not in targets


def test_compare_release_artifact_digests_reports_mismatches():
    with pytest.raises(ValueError, match="content mismatch: release/manifest.json"):
        compare_release_artifact_digests(
            {"release/manifest.json": "abc"},
            {"release/manifest.json": "def"},
        )


def test_build_release_artifact_comparison_tracks_missing_and_changed():
    comparison = build_release_artifact_comparison(
        {
            "release/manifest.json": "abc",
            "release/reference_results.json": "same",
        },
        {
            "release/manifest.json": "def",
            "cards/README.md": "new",
            "release/reference_results.json": "same",
        },
    )

    assert comparison.matches is False
    assert comparison.shared_relative_paths == (
        "release/manifest.json",
        "release/reference_results.json",
    )
    assert comparison.changed == ("release/manifest.json",)
    assert comparison.missing_in_second == ()
    assert comparison.missing_in_first == ("cards/README.md",)


def test_collect_release_artifact_digests_hashes_files(tmp_path: Path):
    paths = build_release_repro_paths(tmp_path / "run")
    (paths.release_output_root / "README.md").parent.mkdir(parents=True, exist_ok=True)
    (paths.release_output_root / "README.md").write_text("release\n", encoding="utf-8")

    digests = collect_release_artifact_digests(paths)

    assert "release/README.md" in digests
    assert len(digests["release/README.md"]) == 64


def test_validate_summary_run_counts_accepts_expected_value(tmp_path: Path):
    paths = build_release_repro_paths(tmp_path / "run")
    for filename in SUMMARY_REPORT_FILENAMES:
        target = paths.reports_root / filename
        if filename.endswith(".csv"):
            write_summary_csv(target, "2")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("| ok |\n", encoding="utf-8")

    validate_summary_run_counts(paths, expected_run_count=2)


def test_validate_summary_run_counts_rejects_contamination(tmp_path: Path):
    paths = build_release_repro_paths(tmp_path / "run")
    for filename in SUMMARY_REPORT_FILENAMES:
        target = paths.reports_root / filename
        if filename.endswith(".csv"):
            write_summary_csv(target, "3")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("| ok |\n", encoding="utf-8")

    with pytest.raises(ValueError, match="expected 2"):
        validate_summary_run_counts(paths, expected_run_count=2)


def test_write_release_reproducibility_forensics_writes_summary_diffs_and_snapshots(tmp_path: Path):
    first_paths = build_release_repro_paths(tmp_path / "first")
    second_paths = build_release_repro_paths(tmp_path / "second")

    first_manifest = first_paths.release_output_root / "manifest.json"
    first_manifest.parent.mkdir(parents=True, exist_ok=True)
    first_manifest.write_text('{"status":"first"}\n', encoding="utf-8")

    second_manifest = second_paths.release_output_root / "manifest.json"
    second_manifest.parent.mkdir(parents=True, exist_ok=True)
    second_manifest.write_text('{"status":"second"}\n', encoding="utf-8")

    first_card = first_paths.cards_root / "tasks" / "synthetic_market_direction_v0.md"
    first_card.parent.mkdir(parents=True, exist_ok=True)
    first_card.write_text("# task\n", encoding="utf-8")

    result = write_release_reproducibility_forensics(
        first_paths=first_paths,
        second_paths=second_paths,
        output_dir=tmp_path / "forensics",
        failure_message="content mismatch",
    )

    summary = json.loads(result.summary_json_path.read_text(encoding="utf-8"))

    assert summary["status"] == "failed"
    assert summary["failure_message"] == "content mismatch"
    assert summary["changed_artifact_count"] == 1
    assert summary["missing_in_second_count"] == 1
    assert summary["changed"][0]["relative_path"] == "release/manifest.json"
    assert result.summary_markdown_path.exists()
    assert (
        result.output_dir
        / "diffs"
        / "release"
        / "manifest.json.diff"
    ).exists()
    assert (
        result.output_dir
        / "snapshots"
        / "first"
        / "cards"
        / "tasks"
        / "synthetic_market_direction_v0.md"
    ).exists()


def test_run_release_reproducibility_check_routes_statistical_artifacts_to_isolated_roots(
    tmp_path: Path,
    monkeypatch,
):
    calls: list[dict[str, object]] = []

    def fake_build_pilot_release(**kwargs):
        calls.append(kwargs)
        reports_root = Path(kwargs["reports_root"])
        for filename in SUMMARY_REPORT_FILENAMES:
            target = reports_root / filename
            if filename.endswith(".csv"):
                write_summary_csv(target, str(kwargs["repeat"]))
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("| ok |\n", encoding="utf-8")

        release_root = Path(kwargs["release_output_root"])
        release_root.mkdir(parents=True, exist_ok=True)
        (release_root / "manifest.json").write_text('{"ok": true}\n', encoding="utf-8")
        stats_root = Path(kwargs["statistical_artifacts_output_dir"])
        stats_root.mkdir(parents=True, exist_ok=True)
        (stats_root / "README.md").write_text("# stats\n", encoding="utf-8")

    monkeypatch.setattr(
        "finds_agentbench.release_reproducibility.build_pilot_release",
        fake_build_pilot_release,
    )

    result = run_release_reproducibility_check(work_root=tmp_path / "work", repeat=1)

    assert len(calls) == 2
    for call in calls:
        release_root = Path(call["release_output_root"])
        stats_root = Path(call["statistical_artifacts_output_dir"])
        assert stats_root == release_root / "statistical_artifacts"
    assert "release/statistical_artifacts/README.md" in result.compared_relative_paths
