from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AuditScore:
    task_id: str
    overall_score: float
    leakage_identification: float
    validation_correction: float
    before_after_quantification: float
    execution_success: float
    findings: dict[str, bool]
    failures: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "overall_score": self.overall_score,
            "leakage_identification": self.leakage_identification,
            "validation_correction": self.validation_correction,
            "before_after_quantification": self.before_after_quantification,
            "execution_success": self.execution_success,
            "findings": self.findings,
            "failures": self.failures,
        }


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}.")
    return data


def score_required_findings(note_text: str, required_findings: list[dict[str, Any]]) -> dict[str, bool]:
    normalized = note_text.lower()
    results: dict[str, bool] = {}

    for finding in required_findings:
        finding_id = str(finding["id"])
        required_terms = [str(term).lower() for term in finding.get("required_terms", [])]
        support_terms = [str(term).lower() for term in finding.get("support_terms_any", [])]

        has_required = all(term in normalized for term in required_terms)
        has_support = not support_terms or any(term in normalized for term in support_terms)
        results[finding_id] = has_required and has_support

    return results


def read_metrics(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required_columns = {"metric", "flawed_value", "corrected_value"}
        if reader.fieldnames is None or not required_columns.issubset(reader.fieldnames):
            raise ValueError(f"{path} must contain columns: {sorted(required_columns)}")
        return list(reader)


def score_before_after_metrics(rows: list[dict[str, str]], expected_direction: dict[str, Any]) -> float:
    metric_terms = [str(term).lower() for term in expected_direction.get("metric_any_of", [])]
    threshold = float(expected_direction.get("flawed_should_exceed_corrected_by_at_least", 0.0))

    for row in rows:
        metric = row["metric"].lower()
        if metric_terms and not any(term in metric for term in metric_terms):
            continue
        try:
            flawed = float(row["flawed_value"])
            corrected = float(row["corrected_value"])
        except ValueError:
            continue
        if flawed - corrected >= threshold:
            return 1.0

    return 0.0


def score_leakage_audit_submission(
    *,
    submission_dir: str | Path,
    answer_key_path: str | Path,
) -> AuditScore:
    submission_path = Path(submission_dir)
    answer = load_json(answer_key_path)
    failures: list[str] = []

    audit_note_path = submission_path / "audit_note.md"
    metrics_path = submission_path / "before_after_metrics.csv"

    if not audit_note_path.exists():
        failures.append("missing_audit_note")
        note_text = ""
    else:
        note_text = audit_note_path.read_text(encoding="utf-8")

    if not metrics_path.exists():
        failures.append("missing_before_after_metrics")
        metrics_rows: list[dict[str, str]] = []
    else:
        try:
            metrics_rows = read_metrics(metrics_path)
        except ValueError as exc:
            failures.append(f"invalid_before_after_metrics: {exc}")
            metrics_rows = []

    findings = score_required_findings(note_text, answer.get("required_findings", []))
    leakage_identification = (
        sum(1 for value in findings.values() if value) / len(findings) if findings else 0.0
    )
    validation_correction = 1.0 if findings.get("random_temporal_split", False) else 0.0
    before_after = score_before_after_metrics(
        metrics_rows,
        answer.get("expected_metric_direction", {}),
    )
    execution_success = 1.0 if not failures else 0.0

    overall = round(
        0.45 * leakage_identification
        + 0.25 * validation_correction
        + 0.20 * before_after
        + 0.10 * execution_success,
        6,
    )

    return AuditScore(
        task_id=str(answer.get("task_id", "unknown")),
        overall_score=overall,
        leakage_identification=round(leakage_identification, 6),
        validation_correction=validation_correction,
        before_after_quantification=before_after,
        execution_success=execution_success,
        findings=findings,
        failures=failures,
    )

