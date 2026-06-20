from pathlib import Path

from finds_agentbench.runs import (
    build_run_manifest,
    load_run_manifest,
    validate_run_manifest,
    write_run_manifest,
)


def test_build_and_validate_run_manifest(tmp_path: Path):
    submission_dir = tmp_path / "submission"
    submission_dir.mkdir()
    (submission_dir / "predictions.csv").write_text(
        "row_id,prediction,probability\nrow_1,1,0.8\n",
        encoding="utf-8",
    )
    (submission_dir / "writeup.md").write_text("short writeup", encoding="utf-8")

    manifest = build_run_manifest(
        task_id="synthetic_market_direction_v0",
        agent_id="momentum_baseline",
        agent_version="0.1.0",
        submission_dir=submission_dir,
        run_id="test_run",
        started_at="2026-06-20T00:00:00+00:00",
        completed_at="2026-06-20T00:01:00+00:00",
        scores={"overall_score": 0.5},
        validations={"artifact_validation": {"ok": True}},
        tool_permissions=["filesystem:read", "filesystem:write"],
        commands=[
            {
                "command": "python baseline.py",
                "started_at": "2026-06-20T00:00:00+00:00",
                "completed_at": "2026-06-20T00:00:10+00:00",
                "exit_code": 0,
            }
        ],
    )

    result = validate_run_manifest(manifest)

    assert result.ok, result.errors
    assert len(manifest["artifacts"]["files"]) == 2
    assert all("sha256" in item for item in manifest["artifacts"]["files"])


def test_validate_run_manifest_reports_missing_fields():
    result = validate_run_manifest({"schema_version": "0.1.0"})

    assert not result.ok
    assert any("missing top-level key: run_id" in error for error in result.errors)


def test_write_and_load_run_manifest(tmp_path: Path):
    submission_dir = tmp_path / "submission"
    submission_dir.mkdir()
    (submission_dir / "predictions.csv").write_text(
        "row_id,prediction,probability\nrow_1,1,0.8\n",
        encoding="utf-8",
    )
    manifest = build_run_manifest(
        task_id="synthetic_market_direction_v0",
        agent_id="baseline",
        agent_version="0.1.0",
        submission_dir=submission_dir,
        run_id="roundtrip",
    )
    output = tmp_path / "manifest.json"

    write_run_manifest(manifest, output)
    loaded = load_run_manifest(output)

    assert loaded["run_id"] == "roundtrip"
    assert validate_run_manifest(loaded).ok

