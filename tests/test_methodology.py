from pathlib import Path

import nbformat

from finds_agentbench.artifacts import validate_submission_artifacts
from finds_agentbench.io import load_yaml
from finds_agentbench.methodology import scan_submission_methodology


def write_notebook(path: Path, source: str) -> None:
    notebook = nbformat.v4.new_notebook()
    notebook.cells = [nbformat.v4.new_code_cell(source)]
    nbformat.write(notebook, path)


def test_scan_clean_submission_methodology(tmp_path: Path):
    submission_dir = tmp_path / "submission"
    submission_dir.mkdir()
    (submission_dir / "model.py").write_text(
        "train_rows = [row for row in rows if row['split'] == 'train']\n",
        encoding="utf-8",
    )

    result = scan_submission_methodology(submission_dir)

    assert result.ok
    assert result.findings == []


def test_scan_random_split_methodology_error(tmp_path: Path):
    submission_dir = tmp_path / "submission"
    submission_dir.mkdir()
    (submission_dir / "model.py").write_text(
        "X_train, X_test = train_test_split(X, y, shuffle=True)\n",
        encoding="utf-8",
    )

    result = scan_submission_methodology(submission_dir)

    assert not result.ok
    assert {finding.rule_id for finding in result.findings} == {
        "random_train_test_split",
        "explicit_shuffle",
    }


def test_scan_suspicious_feature_construction_warnings(tmp_path: Path):
    submission_dir = tmp_path / "submission"
    submission_dir.mkdir()
    (submission_dir / "model.py").write_text(
        "future_signal = returns.shift(-1)\n"
        "rolling_mean = price.rolling(5, center=True).mean()\n"
        "filled = feature_frame.bfill()\n",
        encoding="utf-8",
    )

    result = scan_submission_methodology(submission_dir)

    assert result.ok
    assert {finding.rule_id for finding in result.findings} == {
        "backfill_future_imputation",
        "centered_rolling_window",
        "negative_shift_future_construction",
    }


def test_scan_target_like_feature_warning_can_fail_on_warnings(tmp_path: Path):
    submission_dir = tmp_path / "submission"
    submission_dir.mkdir()
    (submission_dir / "model.py").write_text(
        "feature_columns = ['lagged_signal', 'target']\n"
        "X = df[feature_columns]\n",
        encoding="utf-8",
    )

    result = scan_submission_methodology(submission_dir, fail_on_warnings=True)

    assert not result.ok
    assert {finding.rule_id for finding in result.findings} == {
        "target_like_feature_construction",
    }


def test_scan_writeup_does_not_trigger_code_only_methodology_rules(tmp_path: Path):
    submission_dir = tmp_path / "submission"
    submission_dir.mkdir()
    (submission_dir / "writeup.md").write_text(
        "We considered shift(-1), bfill(), and centered rolling windows as invalid.\n",
        encoding="utf-8",
    )

    result = scan_submission_methodology(submission_dir)

    assert result.ok
    assert result.findings == []


def test_scan_notebook_methodology_warning(tmp_path: Path):
    submission_dir = tmp_path / "submission"
    submission_dir.mkdir()
    write_notebook(submission_dir / "notebook.ipynb", "scores = cross_val_score(model, X, y)")

    result = scan_submission_methodology(submission_dir)

    assert result.ok
    assert len(result.findings) == 1
    assert result.findings[0].severity == "warning"


def test_artifact_validation_can_fail_on_methodology_error(tmp_path: Path):
    task_spec = load_yaml("tasks/pilot/synthetic_market_direction_v0.yaml")
    submission_dir = tmp_path / "submission"
    submission_dir.mkdir()
    write_notebook(submission_dir / "notebook.ipynb", "print('ok')")
    (submission_dir / "writeup.md").write_text("short", encoding="utf-8")
    (submission_dir / "predictions.csv").write_text(
        "row_id,prediction,probability\nrow_1,1,0.7\n",
        encoding="utf-8",
    )
    (submission_dir / "bad_model.py").write_text(
        "from sklearn.model_selection import train_test_split\n"
        "train_test_split(X, y, shuffle=True)\n",
        encoding="utf-8",
    )

    result = validate_submission_artifacts(
        task_spec=task_spec,
        submission_dir=submission_dir,
        execute=False,
        scan_methodology=True,
    )

    assert not result.ok
    assert any("methodology_scan_failed" in error for error in result.errors)
    assert result.methodology_findings
