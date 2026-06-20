from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from finds_agentbench.leakage import scan_submission_for_leakage


@dataclass(frozen=True)
class ArtifactValidationResult:
    ok: bool
    errors: list[str]
    warnings: list[str]
    executed_notebook_path: str | None = None
    leakage_findings: list[dict[str, str]] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": self.errors,
            "warnings": self.warnings,
            "executed_notebook_path": self.executed_notebook_path,
            "leakage_findings": self.leakage_findings or [],
        }


def count_words(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    return len([token for token in text.split() if token.strip()])


def csv_columns(path: Path) -> set[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return set(reader.fieldnames or [])


def execute_notebook(
    notebook_path: Path,
    *,
    timeout: int = 120,
    output_path: Path | None = None,
    cwd: Path | None = None,
    kernel_name: str = "python3",
) -> str | None:
    try:
        import nbformat
        from nbconvert.preprocessors import CellExecutionError, ExecutePreprocessor
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "Notebook execution requires nbformat and nbconvert. "
            "Install project notebook dependencies first."
        ) from exc

    with notebook_path.open("r", encoding="utf-8") as handle:
        notebook = nbformat.read(handle, as_version=4)

    executor = ExecutePreprocessor(timeout=timeout, kernel_name=kernel_name)
    try:
        executor.preprocess(notebook, {"metadata": {"path": str(cwd or notebook_path.parent)}})
    except CellExecutionError as exc:
        raise RuntimeError(f"notebook_execution_failed: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"notebook_execution_failed: {exc}") from exc

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            nbformat.write(notebook, handle)
        return str(output_path)

    return None


def validate_submission_artifacts(
    *,
    task_spec: dict[str, Any],
    submission_dir: str | Path,
    execute: bool = True,
    timeout: int = 120,
    executed_output: str | Path | None = None,
    scan_leakage: bool = False,
    leakage_terms: list[str] | None = None,
) -> ArtifactValidationResult:
    submission_path = Path(submission_dir)
    errors: list[str] = []
    warnings: list[str] = []
    executed_notebook_path: str | None = None
    leakage_findings: list[dict[str, str]] = []

    if not submission_path.exists() or not submission_path.is_dir():
        return ArtifactValidationResult(
            ok=False,
            errors=[f"submission directory does not exist: {submission_path}"],
            warnings=[],
            leakage_findings=[],
        )

    deliverables = task_spec.get("deliverables", {})
    required_files = [str(value) for value in deliverables.get("required_files", [])]
    notebook_spec = deliverables.get("notebook", {})
    notebook_relative = str(notebook_spec.get("path", "notebook.ipynb"))
    notebook_path = submission_path / notebook_relative

    if not notebook_path.exists():
        errors.append(f"missing notebook: {notebook_relative}")
    elif execute and notebook_spec.get("must_execute_cleanly", False):
        try:
            executed_notebook_path = execute_notebook(
                notebook_path,
                timeout=timeout,
                output_path=Path(executed_output) if executed_output else None,
                cwd=submission_path,
            )
        except RuntimeError as exc:
            errors.append(str(exc))

    for relative_path in required_files:
        if not (submission_path / relative_path).exists():
            errors.append(f"missing required file: {relative_path}")

    predictions_spec = deliverables.get("predictions", {})
    predictions_relative = predictions_spec.get("path")
    if predictions_relative:
        predictions_path = submission_path / str(predictions_relative)
        if predictions_path.exists():
            required_columns = set(predictions_spec.get("required_columns", []))
            available_columns = csv_columns(predictions_path)
            missing_columns = sorted(required_columns - available_columns)
            if missing_columns:
                errors.append(
                    f"{predictions_relative} missing required columns: {missing_columns}"
                )

    writeup_spec = deliverables.get("writeup", {})
    writeup_relative = writeup_spec.get("path")
    if writeup_relative:
        writeup_path = submission_path / str(writeup_relative)
        if writeup_path.exists() and writeup_spec.get("max_words") is not None:
            max_words = int(writeup_spec["max_words"])
            word_count = count_words(writeup_path)
            if word_count > max_words:
                warnings.append(
                    f"{writeup_relative} has {word_count} words; max_words={max_words}"
                )

    if scan_leakage:
        leakage_result = scan_submission_for_leakage(
            submission_path,
            forbidden_terms=leakage_terms,
        )
        leakage_findings = [finding.as_dict() for finding in leakage_result.findings]
        if not leakage_result.ok:
            errors.append(
                f"leakage_scan_failed: {len(leakage_result.findings)} forbidden references found"
            )

    return ArtifactValidationResult(
        ok=not errors,
        errors=errors,
        warnings=warnings,
        executed_notebook_path=executed_notebook_path,
        leakage_findings=leakage_findings,
    )
