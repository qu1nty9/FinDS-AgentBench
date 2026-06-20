from pathlib import Path

import nbformat

from finds_agentbench.artifacts import validate_submission_artifacts
from finds_agentbench.io import load_yaml
from finds_agentbench.leakage import scan_submission_for_leakage


def write_notebook(path: Path, source: str) -> None:
    notebook = nbformat.v4.new_notebook()
    notebook.cells = [nbformat.v4.new_code_cell(source)]
    nbformat.write(notebook, path)


def test_scan_clean_submission(tmp_path: Path):
    submission_dir = tmp_path / "submission"
    submission_dir.mkdir()
    (submission_dir / "model.py").write_text(
        "features_path = 'data/raw/synthetic_market_direction_v0/private_holdout_features.csv'\n",
        encoding="utf-8",
    )

    result = scan_submission_for_leakage(submission_dir)

    assert result.ok
    assert result.findings == []
    assert result.scanned_files == 1


def test_scan_python_file_detects_private_answer_access(tmp_path: Path):
    submission_dir = tmp_path / "submission"
    submission_dir.mkdir()
    (submission_dir / "model.py").write_text(
        "labels = open('data/private/synthetic_market_direction_v0/answer_key.csv').read()\n",
        encoding="utf-8",
    )

    result = scan_submission_for_leakage(submission_dir)

    assert not result.ok
    assert {finding.term for finding in result.findings} == {"data/private", "answer_key"}


def test_scan_notebook_detects_answer_key_access(tmp_path: Path):
    submission_dir = tmp_path / "submission"
    submission_dir.mkdir()
    write_notebook(
        submission_dir / "notebook.ipynb",
        "answer_key_path = 'data/private/synthetic_market_direction_v0/answer_key.csv'",
    )

    result = scan_submission_for_leakage(submission_dir)

    assert not result.ok
    assert any(finding.file == "notebook.ipynb" for finding in result.findings)
    assert any(finding.location.startswith("cell:1") for finding in result.findings)


def test_artifact_validation_can_fail_on_leakage_scan(tmp_path: Path):
    task_spec = load_yaml("tasks/pilot/synthetic_market_direction_v0.yaml")
    submission_dir = tmp_path / "submission"
    submission_dir.mkdir()
    write_notebook(
        submission_dir / "notebook.ipynb",
        "labels = 'data/private/synthetic_market_direction_v0/answer_key.csv'",
    )
    (submission_dir / "writeup.md").write_text("short", encoding="utf-8")
    (submission_dir / "predictions.csv").write_text(
        "row_id,prediction,probability\nrow_1,1,0.7\n",
        encoding="utf-8",
    )

    result = validate_submission_artifacts(
        task_spec=task_spec,
        submission_dir=submission_dir,
        execute=False,
        scan_leakage=True,
    )

    assert not result.ok
    assert any("leakage_scan_failed" in error for error in result.errors)
    assert result.leakage_findings

