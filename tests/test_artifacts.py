from pathlib import Path

import nbformat
import pytest

from finds_agentbench.artifacts import execute_notebook, validate_submission_artifacts
from finds_agentbench.io import load_yaml


def write_notebook(path: Path, source: str) -> None:
    notebook = nbformat.v4.new_notebook()
    notebook.cells = [nbformat.v4.new_code_cell(source)]
    nbformat.write(notebook, path)


def require_kernel_execution(tmp_path: Path) -> None:
    probe = tmp_path / "probe.ipynb"
    write_notebook(probe, "value = 1 + 1")
    try:
        execute_notebook(probe, timeout=30, cwd=tmp_path)
    except RuntimeError as exc:
        pytest.skip(f"Jupyter kernel execution is unavailable in this environment: {exc}")


def test_validate_submission_executes_notebook_and_checks_artifacts(tmp_path: Path):
    require_kernel_execution(tmp_path)
    task_spec = load_yaml("tasks/pilot/synthetic_market_direction_v0.yaml")
    submission_dir = tmp_path / "submission"
    submission_dir.mkdir()
    notebook_path = submission_dir / "notebook.ipynb"
    executed_output = tmp_path / "executed.ipynb"

    write_notebook(
        notebook_path,
        "\n".join(
            [
                "from pathlib import Path",
                "Path('writeup.md').write_text('A short supported writeup.', encoding='utf-8')",
                "Path('predictions.csv').write_text(",
                "    'row_id,prediction,probability\\nrow_1,1,0.7\\n',",
                "    encoding='utf-8',",
                ")",
            ]
        ),
    )

    result = validate_submission_artifacts(
        task_spec=task_spec,
        submission_dir=submission_dir,
        execute=True,
        timeout=30,
        executed_output=executed_output,
    )

    assert result.ok, result.errors
    assert result.executed_notebook_path == str(executed_output)
    assert executed_output.exists()


def test_validate_submission_reports_notebook_execution_failure(tmp_path: Path):
    require_kernel_execution(tmp_path)
    task_spec = load_yaml("tasks/pilot/synthetic_market_direction_v0.yaml")
    submission_dir = tmp_path / "submission"
    submission_dir.mkdir()
    write_notebook(submission_dir / "notebook.ipynb", "raise RuntimeError('boom')")
    (submission_dir / "writeup.md").write_text("short", encoding="utf-8")
    (submission_dir / "predictions.csv").write_text(
        "row_id,prediction,probability\nrow_1,1,0.7\n",
        encoding="utf-8",
    )

    result = validate_submission_artifacts(
        task_spec=task_spec,
        submission_dir=submission_dir,
        execute=True,
        timeout=30,
    )

    assert not result.ok
    assert any("notebook_execution_failed" in error for error in result.errors)
