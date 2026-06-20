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


@dataclass(frozen=True)
class PredictiveScore:
    task_id: str
    overall_score: float
    balanced_accuracy: float | None
    roc_auc: float | None
    log_loss: float | None
    long_flat_mean_return: float | None
    max_drawdown: float | None
    turnover: float | None
    rows_scored: int
    execution_success: float
    failures: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "overall_score": self.overall_score,
            "balanced_accuracy": self.balanced_accuracy,
            "roc_auc": self.roc_auc,
            "log_loss": self.log_loss,
            "long_flat_mean_return": self.long_flat_mean_return,
            "max_drawdown": self.max_drawdown,
            "turnover": self.turnover,
            "rows_scored": self.rows_scored,
            "execution_success": self.execution_success,
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


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def balanced_accuracy(y_true: list[int], y_pred: list[int]) -> float:
    positives = [idx for idx, value in enumerate(y_true) if value == 1]
    negatives = [idx for idx, value in enumerate(y_true) if value == 0]
    if not positives or not negatives:
        return 0.0
    tpr = sum(1 for idx in positives if y_pred[idx] == 1) / len(positives)
    tnr = sum(1 for idx in negatives if y_pred[idx] == 0) / len(negatives)
    return (tpr + tnr) / 2.0


def roc_auc_score(y_true: list[int], scores: list[float]) -> float | None:
    positives = sum(y_true)
    negatives = len(y_true) - positives
    if positives == 0 or negatives == 0:
        return None

    sorted_pairs = sorted(enumerate(scores), key=lambda item: item[1])
    ranks = [0.0] * len(scores)
    rank = 1
    idx = 0
    while idx < len(sorted_pairs):
        end = idx + 1
        while end < len(sorted_pairs) and sorted_pairs[end][1] == sorted_pairs[idx][1]:
            end += 1
        average_rank = (rank + rank + (end - idx) - 1) / 2.0
        for pair_idx in range(idx, end):
            original_idx = sorted_pairs[pair_idx][0]
            ranks[original_idx] = average_rank
        rank += end - idx
        idx = end

    positive_rank_sum = sum(rank_value for rank_value, label in zip(ranks, y_true) if label == 1)
    auc = (positive_rank_sum - positives * (positives + 1) / 2.0) / (positives * negatives)
    return auc


def binary_log_loss(y_true: list[int], probabilities: list[float]) -> float:
    import math

    eps = 1e-15
    total = 0.0
    for label, probability in zip(y_true, probabilities):
        clipped = min(max(probability, eps), 1.0 - eps)
        total += label * math.log(clipped) + (1 - label) * math.log(1.0 - clipped)
    return -total / len(y_true)


def max_drawdown(returns: list[float]) -> float:
    equity = 1.0
    peak = 1.0
    worst = 0.0
    for value in returns:
        equity *= 1.0 + value
        peak = max(peak, equity)
        drawdown = equity / peak - 1.0
        worst = min(worst, drawdown)
    return worst


def turnover_by_asset(answer_rows: list[dict[str, str]], predictions: dict[str, int]) -> float:
    grouped: dict[str, list[tuple[str, int]]] = {}
    for row in answer_rows:
        row_id = row["row_id"]
        grouped.setdefault(row["asset_id"], []).append((row["date"], predictions[row_id]))

    changes = 0
    comparisons = 0
    for values in grouped.values():
        ordered = sorted(values)
        for previous, current in zip(ordered, ordered[1:]):
            comparisons += 1
            if previous[1] != current[1]:
                changes += 1
    return changes / comparisons if comparisons else 0.0


def score_synthetic_market_submission(
    *,
    submission_path: str | Path,
    answer_key_path: str | Path,
) -> PredictiveScore:
    failures: list[str] = []
    answer_rows = read_csv_rows(answer_key_path)
    answer_by_id = {row["row_id"]: row for row in answer_rows}

    try:
        submission_rows = read_csv_rows(submission_path)
    except FileNotFoundError:
        return PredictiveScore(
            task_id="synthetic_market_direction_v0",
            overall_score=0.0,
            balanced_accuracy=None,
            roc_auc=None,
            log_loss=None,
            long_flat_mean_return=None,
            max_drawdown=None,
            turnover=None,
            rows_scored=0,
            execution_success=0.0,
            failures=["missing_predictions_file"],
        )

    required_columns = {"row_id", "prediction", "probability"}
    if submission_rows:
        available_columns = set(submission_rows[0].keys())
    else:
        available_columns = set()
    if not required_columns.issubset(available_columns):
        failures.append(f"predictions.csv must contain columns: {sorted(required_columns)}")

    submitted_ids = [row.get("row_id", "") for row in submission_rows]
    expected_ids = set(answer_by_id)
    submitted_id_set = set(submitted_ids)
    missing = sorted(expected_ids - submitted_id_set)
    extra = sorted(submitted_id_set - expected_ids)
    if missing:
        failures.append(f"missing {len(missing)} holdout row ids")
    if extra:
        failures.append(f"found {len(extra)} unknown row ids")
    if len(submitted_ids) != len(submitted_id_set):
        failures.append("duplicate row_id values in submission")

    y_true: list[int] = []
    y_pred: list[int] = []
    probabilities: list[float] = []
    strategy_returns: list[float] = []
    prediction_by_id: dict[str, int] = {}

    if not failures:
        for row_id in sorted(expected_ids):
            submission = next(row for row in submission_rows if row["row_id"] == row_id)
            try:
                prediction = int(submission["prediction"])
                probability = float(submission["probability"])
            except ValueError:
                failures.append(f"invalid prediction/probability for row_id={row_id}")
                break
            if prediction not in {0, 1}:
                failures.append(f"prediction must be 0 or 1 for row_id={row_id}")
                break
            if not 0.0 <= probability <= 1.0:
                failures.append(f"probability must be in [0, 1] for row_id={row_id}")
                break

            answer = answer_by_id[row_id]
            label = int(answer["next_day_positive_return"])
            next_return = float(answer["next_day_return"])
            y_true.append(label)
            y_pred.append(prediction)
            probabilities.append(probability)
            prediction_by_id[row_id] = prediction
            strategy_returns.append(next_return if prediction == 1 else 0.0)

    if failures:
        return PredictiveScore(
            task_id="synthetic_market_direction_v0",
            overall_score=0.0,
            balanced_accuracy=None,
            roc_auc=None,
            log_loss=None,
            long_flat_mean_return=None,
            max_drawdown=None,
            turnover=None,
            rows_scored=0,
            execution_success=0.0,
            failures=failures,
        )

    ba = balanced_accuracy(y_true, y_pred)
    auc = roc_auc_score(y_true, probabilities)
    loss = binary_log_loss(y_true, probabilities)
    mean_return = sum(strategy_returns) / len(strategy_returns)
    drawdown = max_drawdown(strategy_returns)
    turnover = turnover_by_asset(answer_rows, prediction_by_id)

    return PredictiveScore(
        task_id="synthetic_market_direction_v0",
        overall_score=round(ba, 6),
        balanced_accuracy=round(ba, 6),
        roc_auc=round(auc, 6) if auc is not None else None,
        log_loss=round(loss, 6),
        long_flat_mean_return=round(mean_return, 8),
        max_drawdown=round(drawdown, 8),
        turnover=round(turnover, 6),
        rows_scored=len(y_true),
        execution_success=1.0,
        failures=[],
    )

