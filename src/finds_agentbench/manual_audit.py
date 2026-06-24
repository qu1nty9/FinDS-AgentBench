from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

from finds_agentbench.io import load_yaml


DEFAULT_MANUAL_AUDIT_RUBRIC_PATH = Path("audits/pilot_v0/manual_audit_rubric.yaml")
DEFAULT_MANUAL_AUDIT_SUBSET_PATH = Path("audits/pilot_v0/adjudicated_subset.json")
DEFAULT_MANUAL_AUDIT_REVIEWS_DIR = Path("audits/pilot_v0/reviews")
DEFAULT_MANUAL_AUDIT_REPORTS_DIR = Path("audits/pilot_v0/reports")
DEFAULT_MANUAL_AUDIT_REVIEWS_README_PATH = DEFAULT_MANUAL_AUDIT_REVIEWS_DIR / "README.md"
DEFAULT_MANUAL_AUDIT_REVIEWER_1_SEED_PATH = DEFAULT_MANUAL_AUDIT_REVIEWS_DIR / "reviewer_1_seed.csv"
DEFAULT_MANUAL_AUDIT_REVIEWER_2_TEMPLATE_PATH = (
    DEFAULT_MANUAL_AUDIT_REVIEWS_DIR / "reviewer_2_blank_template.csv"
)
DEFAULT_MANUAL_AUDIT_REVIEWER_2_SHADOW_PATH = (
    DEFAULT_MANUAL_AUDIT_REVIEWS_DIR / "reviewer_2_shadow_demo.csv"
)
DEFAULT_MANUAL_AUDIT_AGREEMENT_JSON_PATH = (
    DEFAULT_MANUAL_AUDIT_REPORTS_DIR / "agreement_summary.json"
)
DEFAULT_MANUAL_AUDIT_AGREEMENT_MARKDOWN_PATH = (
    DEFAULT_MANUAL_AUDIT_REPORTS_DIR / "agreement_summary.md"
)
DEFAULT_MANUAL_AUDIT_ADJUDICATION_JSON_PATH = (
    DEFAULT_MANUAL_AUDIT_REPORTS_DIR / "adjudication_queue.json"
)
DEFAULT_MANUAL_AUDIT_ADJUDICATION_MARKDOWN_PATH = (
    DEFAULT_MANUAL_AUDIT_REPORTS_DIR / "adjudication_queue.md"
)
DEFAULT_MANUAL_AUDIT_REVIEWER_READINESS_JSON_PATH = (
    DEFAULT_MANUAL_AUDIT_REPORTS_DIR / "reviewer_readiness.json"
)
DEFAULT_MANUAL_AUDIT_REVIEWER_READINESS_MARKDOWN_PATH = (
    DEFAULT_MANUAL_AUDIT_REPORTS_DIR / "reviewer_readiness.md"
)


@dataclass(frozen=True)
class ManualAuditBundle:
    rubric_path: Path
    subset_path: Path
    rubric: dict[str, Any]
    subset: dict[str, Any]
    summary: dict[str, Any]


def load_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {path}, got {type(data).__name__}.")
    return data


def rubric_dimension_ids(rubric: dict[str, Any]) -> list[str]:
    dimensions = rubric.get("dimensions", [])
    return [
        str(dimension["dimension_id"])
        for dimension in dimensions
        if isinstance(dimension, dict) and str(dimension.get("dimension_id", "")).strip()
    ]


def dimension_total(case: dict[str, Any]) -> int:
    rubric_scores = case.get("rubric_scores", {})
    total = 0
    for item in rubric_scores.values():
        if isinstance(item, dict):
            total += int(item.get("score", 0))
    return total


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _relative_path_string(path: Path, *, workspace_root: Path) -> str:
    try:
        return str(path.relative_to(workspace_root))
    except ValueError:
        return str(path)


def render_markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    body_lines = [
        "| " + " | ".join(str(value) for value in row) + " |"
        for row in rows
    ]
    return "\n".join([header_line, separator_line, *body_lines])


def validate_manual_audit_bundle(
    *,
    rubric: dict[str, Any],
    subset: dict[str, Any],
    rubric_path: str | Path,
    subset_path: str | Path,
    workspace_root: str | Path = ".",
) -> list[str]:
    errors: list[str] = []
    workspace = Path(workspace_root).resolve()
    rubric_file = Path(rubric_path)
    subset_file = Path(subset_path)

    rubric_id = str(rubric.get("rubric_id", "")).strip()
    if not rubric_id:
        errors.append("rubric.rubric_id must be non-empty")

    dimensions = rubric.get("dimensions")
    dimension_ids: list[str] = []
    if not isinstance(dimensions, list) or not dimensions:
        errors.append("rubric.dimensions must be a non-empty list")
    else:
        for idx, dimension in enumerate(dimensions):
            context = f"rubric.dimensions[{idx}]"
            if not isinstance(dimension, dict):
                errors.append(f"{context} must be an object")
                continue
            dimension_id = str(dimension.get("dimension_id", "")).strip()
            if not dimension_id:
                errors.append(f"{context}.dimension_id must be non-empty")
                continue
            if dimension_id in dimension_ids:
                errors.append(f"duplicate rubric dimension_id: {dimension_id}")
                continue
            dimension_ids.append(dimension_id)
            anchors = dimension.get("anchors")
            if not isinstance(anchors, dict):
                errors.append(f"{context}.anchors must be an object")
                continue
            anchor_scores = {_safe_int(key) for key in anchors.keys()}
            if None in anchor_scores or {0, 1, 2} - {score for score in anchor_scores if score is not None}:
                errors.append(f"{context}.anchors must define scores 0, 1, and 2")

    declared_rubric_path = str(subset.get("rubric_path", "")).strip()
    if declared_rubric_path and Path(declared_rubric_path) != rubric_file:
        errors.append(
            "subset.rubric_path must match the rubric file used for validation: "
            f"{declared_rubric_path!r} != {str(rubric_file)!r}"
        )

    cases = subset.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("subset.cases must be a non-empty list")
        return errors

    for idx, case in enumerate(cases):
        context = f"subset.cases[{idx}]"
        if not isinstance(case, dict):
            errors.append(f"{context} must be an object")
            continue
        for key in ("case_id", "task_id", "run_type", "agent_id", "artifact_root", "overall_label"):
            if not str(case.get(key, "")).strip():
                errors.append(f"{context}.{key} must be non-empty")

        artifact_root = workspace / str(case.get("artifact_root", ""))
        if not artifact_root.exists():
            errors.append(
                f"{context}.artifact_root does not exist: "
                f"{_relative_path_string(artifact_root, workspace_root=workspace)}"
            )

        source_paths = case.get("source_paths")
        if not isinstance(source_paths, dict) or not source_paths:
            errors.append(f"{context}.source_paths must be a non-empty object")
        else:
            for key, value in source_paths.items():
                target = workspace / str(value)
                if not target.exists():
                    errors.append(
                        f"{context}.source_paths.{key} does not exist: "
                        f"{_relative_path_string(target, workspace_root=workspace)}"
                    )

        rubric_scores = case.get("rubric_scores")
        if not isinstance(rubric_scores, dict):
            errors.append(f"{context}.rubric_scores must be an object")
            continue
        if set(rubric_scores) != set(dimension_ids):
            errors.append(
                f"{context}.rubric_scores keys must match rubric dimensions: "
                f"{sorted(rubric_scores)} != {sorted(dimension_ids)}"
            )
            continue

        total_score = 0
        for dimension_id in dimension_ids:
            score_entry = rubric_scores.get(dimension_id)
            score_context = f"{context}.rubric_scores.{dimension_id}"
            if not isinstance(score_entry, dict):
                errors.append(f"{score_context} must be an object")
                continue
            score = _safe_int(score_entry.get("score"))
            if score is None:
                errors.append(f"{score_context}.score must be an integer")
                continue
            if score not in {0, 1, 2}:
                errors.append(f"{score_context}.score must be one of 0, 1, 2")
            if not str(score_entry.get("evidence", "")).strip():
                errors.append(f"{score_context}.evidence must be non-empty")
            total_score += score

        declared_total = _safe_int(case.get("total_score"))
        if declared_total != total_score:
            errors.append(
                f"{context}.total_score must equal the sum of rubric dimension scores: "
                f"{case.get('total_score')} != {total_score}"
            )

    declared_subset_id = str(subset.get("subset_id", "")).strip()
    if not declared_subset_id:
        errors.append("subset.subset_id must be non-empty")

    if not str(subset.get("status", "")).strip():
        errors.append("subset.status must be non-empty")

    if not subset_file.exists():
        errors.append(f"subset file does not exist: {subset_file}")

    return errors


def summarize_manual_audit_bundle(rubric: dict[str, Any], subset: dict[str, Any]) -> dict[str, Any]:
    dimension_ids = rubric_dimension_ids(rubric)
    cases = subset.get("cases", [])

    per_dimension_means: list[dict[str, Any]] = []
    for dimension_id in dimension_ids:
        values = [
            int(case["rubric_scores"][dimension_id]["score"])
            for case in cases
            if isinstance(case, dict)
            and isinstance(case.get("rubric_scores"), dict)
            and dimension_id in case["rubric_scores"]
        ]
        mean_score = round(sum(values) / len(values), 3) if values else 0.0
        per_dimension_means.append(
            {
                "dimension_id": dimension_id,
                "mean_score": mean_score,
                "case_count": len(values),
            }
        )

    return {
        "status": str(subset.get("status", "")).strip(),
        "subset_id": str(subset.get("subset_id", "")).strip(),
        "rubric_id": str(rubric.get("rubric_id", "")).strip(),
        "dimension_count": len(dimension_ids),
        "dimension_ids": dimension_ids,
        "case_count": len(cases),
        "reviewed_task_count": len(
            {
                str(case.get("task_id", "")).strip()
                for case in cases
                if isinstance(case, dict) and str(case.get("task_id", "")).strip()
            }
        ),
        "task_ids": sorted(
            {
                str(case.get("task_id", "")).strip()
                for case in cases
                if isinstance(case, dict) and str(case.get("task_id", "")).strip()
            }
        ),
        "run_types": sorted(
            {
                str(case.get("run_type", "")).strip()
                for case in cases
                if isinstance(case, dict) and str(case.get("run_type", "")).strip()
            }
        ),
        "per_dimension_means": per_dimension_means,
        "score_range": {
            "min_total_score": min((dimension_total(case) for case in cases), default=0),
            "max_total_score": max((dimension_total(case) for case in cases), default=0),
        },
    }


def overall_label_for_total_score(rubric: dict[str, Any], total_score: int) -> str:
    interpretation_bands = rubric.get("scoring", {}).get("interpretation_bands", [])
    for band in interpretation_bands:
        if not isinstance(band, dict):
            continue
        minimum = _safe_int(band.get("min_total_score"))
        maximum = _safe_int(band.get("max_total_score"))
        if minimum is None or maximum is None:
            continue
        if minimum <= total_score <= maximum:
            return str(band.get("label", "")).strip() or "unclassified"
    return "unclassified"


def review_packet_total_score(row: dict[str, str], rubric: dict[str, Any]) -> int:
    return sum(
        int(row[f"{dimension_id}_score"])
        for dimension_id in rubric_dimension_ids(rubric)
        if _safe_int(row.get(f"{dimension_id}_score")) is not None
    )


def review_packet_fieldnames(rubric: dict[str, Any]) -> list[str]:
    headers = [
        "case_id",
        "task_id",
        "track",
        "run_type",
        "agent_id",
        "run_label",
        "artifact_root",
        "benchmark_overall_score",
        "benchmark_balanced_accuracy",
        "benchmark_roc_auc",
        "benchmark_log_loss",
        "reviewer_id",
        "reviewer_role",
        "review_status",
        "review_source",
    ]
    for dimension_id in rubric_dimension_ids(rubric):
        headers.extend([f"{dimension_id}_score", f"{dimension_id}_evidence"])
    headers.extend(
        [
            "overall_label",
            "primary_manual_findings",
            "general_notes",
            "total_score",
        ]
    )
    return headers


def build_review_packet_rows(
    bundle: ManualAuditBundle,
    *,
    reviewer_id: str,
    reviewer_role: str,
    blank: bool = False,
    review_status: str | None = None,
    review_source: str | None = None,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    dimension_ids = rubric_dimension_ids(bundle.rubric)
    status_value = review_status or ("template" if blank else "complete")
    source_value = review_source or ("blank_template" if blank else "seed_subset_projection")

    for case in bundle.subset.get("cases", []):
        benchmark_scores = case.get("benchmark_scores", {})
        row: dict[str, str] = {
            "case_id": str(case.get("case_id", "")),
            "task_id": str(case.get("task_id", "")),
            "track": str(case.get("track", "")),
            "run_type": str(case.get("run_type", "")),
            "agent_id": str(case.get("agent_id", "")),
            "run_label": str(case.get("run_label", "")),
            "artifact_root": str(case.get("artifact_root", "")),
            "benchmark_overall_score": str(benchmark_scores.get("overall_score", "")),
            "benchmark_balanced_accuracy": str(benchmark_scores.get("balanced_accuracy", "")),
            "benchmark_roc_auc": str(benchmark_scores.get("roc_auc", "")),
            "benchmark_log_loss": str(benchmark_scores.get("log_loss", "")),
            "reviewer_id": reviewer_id,
            "reviewer_role": reviewer_role,
            "review_status": status_value,
            "review_source": source_value,
        }
        total_score = 0
        rubric_scores = case.get("rubric_scores", {})
        for dimension_id in dimension_ids:
            score_entry = rubric_scores.get(dimension_id, {})
            if blank:
                row[f"{dimension_id}_score"] = ""
                row[f"{dimension_id}_evidence"] = ""
                continue
            score = int(score_entry.get("score", 0))
            row[f"{dimension_id}_score"] = str(score)
            row[f"{dimension_id}_evidence"] = str(score_entry.get("evidence", ""))
            total_score += score
        row["overall_label"] = "" if blank else str(case.get("overall_label", ""))
        row["primary_manual_findings"] = (
            ""
            if blank
            else " | ".join(str(item) for item in case.get("primary_manual_findings", []))
        )
        row["general_notes"] = "" if blank else str(case.get("adjudication_note", ""))
        row["total_score"] = "" if blank else str(total_score)
        rows.append(row)

    return rows


def build_shadow_review_packet_rows(bundle: ManualAuditBundle) -> list[dict[str, str]]:
    rows = build_review_packet_rows(
        bundle,
        reviewer_id="reviewer_2_shadow_demo",
        reviewer_role="synthetic_shadow_reviewer",
        blank=False,
        review_status="demo_complete",
        review_source="synthetic_shadow_demo",
    )
    adjustments = {
        "pilot_market_momentum_baseline_release_001": {
            "quantitative_evidence_use": (
                1,
                "Shadow demo reviewer gives partial credit because the writeup states a thresholded rule, even though no explicit validation metrics appear.",
            ),
        },
        "pilot_market_logistic_baseline_release_001": {
            "baseline_comparison_or_counterfactual_context": (
                1,
                "Shadow demo reviewer treats the implicit contrast with the momentum rule as partial comparison context, but still not a full quantified baseline analysis.",
            ),
        },
        "pilot_event_rule_baseline_release_001": {
            "temporal_protocol_correctness": (
                2,
                "Shadow demo reviewer interprets the explicit label-free holdout description as sufficient temporal protocol evidence for this synthetic event setup.",
            ),
        },
        "pilot_event_rule_env_agent_protocol_001": {
            "reproducibility_trace_completeness": (
                1,
                "Shadow demo reviewer discounts trace completeness because the writeup remains thin even though command logs are present.",
            ),
        },
        "pilot_treasury_previous_day_baseline_release_001": {
            "claim_discipline": (
                1,
                "Shadow demo reviewer marks a minor overstatement risk because the narrative implies stability from a single simple heuristic without explicit caveat.",
            ),
        },
        "pilot_treasury_logistic_baseline_release_001": {
            "quantitative_evidence_use": (
                1,
                "Shadow demo reviewer gives only partial credit because public-validation evidence is present but no holdout-side caution or error analysis appears in the writeup.",
            ),
            "baseline_comparison_or_counterfactual_context": (
                1,
                "Shadow demo reviewer gives partial comparison credit because the benchmark suite exposes simpler comparators even though the writeup does not discuss them directly.",
            ),
        },
    }

    for row in rows:
        case_adjustments = adjustments.get(row["case_id"], {})
        for dimension_id, (score, evidence) in case_adjustments.items():
            row[f"{dimension_id}_score"] = str(score)
            row[f"{dimension_id}_evidence"] = evidence
        total_score = review_packet_total_score(row, bundle.rubric)
        row["total_score"] = str(total_score)
        row["overall_label"] = overall_label_for_total_score(bundle.rubric, total_score)
        existing_findings = [item.strip() for item in row.get("primary_manual_findings", "").split("|") if item.strip()]
        existing_findings.append("Synthetic shadow reviewer packet for dry-run adjudication only.")
        row["primary_manual_findings"] = " | ".join(existing_findings)
        row["general_notes"] = (
            "Synthetic shadow reviewer packet generated to exercise disagreement and adjudication reporting. "
            "Not eligible for official benchmark agreement claims."
        )
    return rows


def write_review_packet_csv(rows: list[dict[str, str]], rubric: dict[str, Any], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = review_packet_fieldnames(rubric)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return path


def load_review_packet_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [{key: str(value or "") for key, value in row.items()} for row in reader]


def is_complete_review_row(row: dict[str, str], rubric: dict[str, Any]) -> bool:
    if not str(row.get("overall_label", "")).strip():
        return False
    for dimension_id in rubric_dimension_ids(rubric):
        if _safe_int(row.get(f"{dimension_id}_score")) not in {0, 1, 2}:
            return False
        if not str(row.get(f"{dimension_id}_evidence", "")).strip():
            return False
    return True


def validate_review_packet_rows(
    rows: list[dict[str, str]],
    rubric: dict[str, Any],
    *,
    path: str | Path | None = None,
) -> list[str]:
    errors: list[str] = []
    context_prefix = f"{path}: " if path is not None else ""
    if not rows:
        return [f"{context_prefix}review packet has no rows"]

    seen_case_ids: set[str] = set()
    reviewer_ids: set[str] = set()
    reviewer_roles: set[str] = set()
    dimension_ids = rubric_dimension_ids(rubric)

    for idx, row in enumerate(rows):
        context = f"{context_prefix}row {idx + 1}"
        case_id = str(row.get("case_id", "")).strip()
        if not case_id:
            errors.append(f"{context} missing case_id")
        elif case_id in seen_case_ids:
            errors.append(f"{context} duplicate case_id: {case_id}")
        else:
            seen_case_ids.add(case_id)

        reviewer_id = str(row.get("reviewer_id", "")).strip()
        reviewer_role = str(row.get("reviewer_role", "")).strip()
        if not reviewer_id:
            errors.append(f"{context} missing reviewer_id")
        else:
            reviewer_ids.add(reviewer_id)
        if not reviewer_role:
            errors.append(f"{context} missing reviewer_role")
        else:
            reviewer_roles.add(reviewer_role)

        review_status = str(row.get("review_status", "")).strip()
        if not review_status:
            errors.append(f"{context} missing review_status")

        row_complete = is_complete_review_row(row, rubric)
        total_from_dimensions = 0
        for dimension_id in dimension_ids:
            score_key = f"{dimension_id}_score"
            evidence_key = f"{dimension_id}_evidence"
            score = _safe_int(row.get(score_key))
            evidence = str(row.get(evidence_key, "")).strip()
            if score is None:
                if evidence:
                    errors.append(f"{context} has evidence without a valid score for {dimension_id}")
                continue
            if score not in {0, 1, 2}:
                errors.append(f"{context} invalid score for {dimension_id}: {score}")
            if row_complete and not evidence:
                errors.append(f"{context} missing evidence for {dimension_id}")
            total_from_dimensions += score

        total_score = str(row.get("total_score", "")).strip()
        if total_score:
            declared_total = _safe_int(total_score)
            if declared_total is None:
                errors.append(f"{context} total_score must be an integer when provided")
            elif row_complete and declared_total != total_from_dimensions:
                errors.append(
                    f"{context} total_score must equal summed dimension scores: "
                    f"{declared_total} != {total_from_dimensions}"
                )

    if len(reviewer_ids) > 1:
        errors.append(
            f"{context_prefix}review packet must contain exactly one reviewer_id, got {sorted(reviewer_ids)}"
        )
    if len(reviewer_roles) > 1:
        errors.append(
            f"{context_prefix}review packet must contain exactly one reviewer_role, got {sorted(reviewer_roles)}"
        )

    return errors


def summarize_review_packet(path: str | Path, rows: list[dict[str, str]], rubric: dict[str, Any]) -> dict[str, Any]:
    packet_path = Path(path)
    errors = validate_review_packet_rows(rows, rubric, path=packet_path)
    reviewer_ids = sorted({str(row.get("reviewer_id", "")).strip() for row in rows if str(row.get("reviewer_id", "")).strip()})
    reviewer_roles = sorted(
        {str(row.get("reviewer_role", "")).strip() for row in rows if str(row.get("reviewer_role", "")).strip()}
    )
    review_statuses = sorted(
        {str(row.get("review_status", "")).strip() for row in rows if str(row.get("review_status", "")).strip()}
    )
    review_sources = sorted(
        {str(row.get("review_source", "")).strip() for row in rows if str(row.get("review_source", "")).strip()}
    )
    completed_case_count = sum(1 for row in rows if is_complete_review_row(row, rubric))
    exploratory_eligible = not errors and completed_case_count > 0 and len(reviewer_ids) == 1
    official_eligible = exploratory_eligible and "synthetic_shadow_reviewer" not in reviewer_roles
    packet_status = (
        "invalid"
        if errors
        else "template"
        if review_statuses == ["template"]
        else "complete"
        if completed_case_count == len(rows)
        else "partial"
    )
    return {
        "path": str(packet_path),
        "filename": packet_path.name,
        "reviewer_ids": reviewer_ids,
        "reviewer_roles": reviewer_roles,
        "review_statuses": review_statuses,
        "review_sources": review_sources,
        "row_count": len(rows),
        "completed_case_count": completed_case_count,
        "eligible_for_agreement": official_eligible,
        "exploratory_eligible_for_agreement": exploratory_eligible,
        "packet_status": packet_status,
        "errors": errors,
        "rows": rows,
    }


def load_review_packets(reviews_dir: str | Path, rubric: dict[str, Any]) -> list[dict[str, Any]]:
    root = Path(reviews_dir)
    if not root.exists():
        return []
    packets: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.csv")):
        packets.append(summarize_review_packet(path, load_review_packet_csv(path), rubric))
    return packets


def _cohen_kappa(
    values_a: list[Any],
    values_b: list[Any],
    *,
    categories: list[Any],
    weighted: bool,
) -> float | None:
    if not values_a or len(values_a) != len(values_b):
        return None
    if len(categories) <= 1:
        return 1.0

    category_index = {category: idx for idx, category in enumerate(categories)}
    size = len(categories)
    counts = [[0 for _ in range(size)] for _ in range(size)]
    for left, right in zip(values_a, values_b, strict=True):
        counts[category_index[left]][category_index[right]] += 1

    total = len(values_a)
    row_marginals = [sum(row) / total for row in counts]
    col_marginals = [sum(counts[row][col] for row in range(size)) / total for col in range(size)]

    def disagreement_weight(i: int, j: int) -> float:
        if not weighted:
            return 0.0 if i == j else 1.0
        return ((i - j) ** 2) / ((size - 1) ** 2)

    observed_disagreement = sum(
        disagreement_weight(i, j) * (counts[i][j] / total)
        for i in range(size)
        for j in range(size)
    )
    expected_disagreement = sum(
        disagreement_weight(i, j) * row_marginals[i] * col_marginals[j]
        for i in range(size)
        for j in range(size)
    )
    if expected_disagreement == 0:
        return 1.0 if observed_disagreement == 0 else 0.0
    return round(1.0 - (observed_disagreement / expected_disagreement), 6)


def _completed_case_map(packet: dict[str, Any], rubric: dict[str, Any]) -> dict[str, dict[str, Any]]:
    case_map: dict[str, dict[str, Any]] = {}
    for row in packet["rows"]:
        if not is_complete_review_row(row, rubric):
            continue
        scores = {
            dimension_id: int(row[f"{dimension_id}_score"])
            for dimension_id in rubric_dimension_ids(rubric)
        }
        case_map[row["case_id"]] = {
            "scores": scores,
            "overall_label": str(row["overall_label"]),
            "total_score": sum(scores.values()),
        }
    return case_map


def compute_pairwise_review_packet_agreement(
    packet_a: dict[str, Any],
    packet_b: dict[str, Any],
    rubric: dict[str, Any],
) -> dict[str, Any]:
    dimension_ids = rubric_dimension_ids(rubric)
    reviewer_a = packet_a["reviewer_ids"][0]
    reviewer_b = packet_b["reviewer_ids"][0]
    case_map_a = _completed_case_map(packet_a, rubric)
    case_map_b = _completed_case_map(packet_b, rubric)
    overlap_case_ids = sorted(set(case_map_a) & set(case_map_b))

    if not overlap_case_ids:
        return {
            "reviewer_pair": [reviewer_a, reviewer_b],
            "packet_paths": [packet_a["path"], packet_b["path"]],
            "overlap_case_count": 0,
            "status": "no_shared_completed_cases",
            "per_dimension": [],
            "cases_with_any_disagreement": 0,
            "overall_label_exact_agreement": None,
            "overall_label_kappa": None,
            "exact_total_score_match_rate": None,
            "mean_abs_total_score_diff": None,
        }

    per_dimension: list[dict[str, Any]] = []
    disagreement_case_ids: list[str] = []
    total_score_matches = 0
    total_score_abs_diffs: list[int] = []
    label_matches = 0

    for case_id in overlap_case_ids:
        left = case_map_a[case_id]
        right = case_map_b[case_id]
        if left["overall_label"] == right["overall_label"]:
            label_matches += 1
        if left["total_score"] == right["total_score"]:
            total_score_matches += 1
        total_score_abs_diffs.append(abs(left["total_score"] - right["total_score"]))
        if any(left["scores"][dimension_id] != right["scores"][dimension_id] for dimension_id in dimension_ids):
            disagreement_case_ids.append(case_id)
        elif left["overall_label"] != right["overall_label"]:
            disagreement_case_ids.append(case_id)

    for dimension_id in dimension_ids:
        values_a = [case_map_a[case_id]["scores"][dimension_id] for case_id in overlap_case_ids]
        values_b = [case_map_b[case_id]["scores"][dimension_id] for case_id in overlap_case_ids]
        exact_matches = sum(1 for left, right in zip(values_a, values_b, strict=True) if left == right)
        per_dimension.append(
            {
                "dimension_id": dimension_id,
                "exact_agreement_rate": round(exact_matches / len(overlap_case_ids), 6),
                "quadratic_weighted_kappa": _cohen_kappa(
                    values_a,
                    values_b,
                    categories=[0, 1, 2],
                    weighted=True,
                ),
            }
        )

    label_values_a = [case_map_a[case_id]["overall_label"] for case_id in overlap_case_ids]
    label_values_b = [case_map_b[case_id]["overall_label"] for case_id in overlap_case_ids]
    label_categories = sorted(set(label_values_a) | set(label_values_b))

    return {
        "reviewer_pair": [reviewer_a, reviewer_b],
        "packet_paths": [packet_a["path"], packet_b["path"]],
        "overlap_case_count": len(overlap_case_ids),
        "status": "pairwise_agreement_available",
        "per_dimension": per_dimension,
        "cases_with_any_disagreement": len(disagreement_case_ids),
        "disagreement_case_ids": disagreement_case_ids,
        "overall_label_exact_agreement": round(label_matches / len(overlap_case_ids), 6),
        "overall_label_kappa": _cohen_kappa(
            label_values_a,
            label_values_b,
            categories=label_categories,
            weighted=False,
        ),
        "exact_total_score_match_rate": round(total_score_matches / len(overlap_case_ids), 6),
        "mean_abs_total_score_diff": round(sum(total_score_abs_diffs) / len(total_score_abs_diffs), 6),
    }


def summarize_manual_audit_review_workflow(
    bundle: ManualAuditBundle,
    review_packets: list[dict[str, Any]],
) -> dict[str, Any]:
    official_packets = [packet for packet in review_packets if packet["eligible_for_agreement"]]
    exploratory_packets = [
        packet for packet in review_packets if packet["exploratory_eligible_for_agreement"]
    ]
    official_pairwise_agreement = [
        compute_pairwise_review_packet_agreement(left, right, bundle.rubric)
        for left, right in combinations(official_packets, 2)
    ]
    exploratory_pairwise_agreement = [
        compute_pairwise_review_packet_agreement(left, right, bundle.rubric)
        for left, right in combinations(exploratory_packets, 2)
    ]

    if len(official_packets) < 2:
        official_status = "insufficient_independent_overlap"
    elif not official_pairwise_agreement or all(
        item["status"] == "no_shared_completed_cases" for item in official_pairwise_agreement
    ):
        official_status = "no_shared_completed_cases"
    else:
        official_status = "pairwise_agreement_available"

    if len(exploratory_packets) < 2:
        exploratory_status = "insufficient_overlap"
    elif not exploratory_pairwise_agreement or all(
        item["status"] == "no_shared_completed_cases" for item in exploratory_pairwise_agreement
    ):
        exploratory_status = "no_shared_completed_cases"
    else:
        exploratory_status = "pairwise_agreement_available"

    return {
        "status": official_status,
        "official_status": official_status,
        "exploratory_status": exploratory_status,
        "packet_inventory": [
            {
                "path": packet["path"],
                "filename": packet["filename"],
                "reviewer_ids": packet["reviewer_ids"],
                "reviewer_roles": packet["reviewer_roles"],
                "review_statuses": packet["review_statuses"],
                "review_sources": packet["review_sources"],
                "row_count": packet["row_count"],
                "completed_case_count": packet["completed_case_count"],
                "eligible_for_agreement": packet["eligible_for_agreement"],
                "exploratory_eligible_for_agreement": packet["exploratory_eligible_for_agreement"],
                "packet_status": packet["packet_status"],
                "error_count": len(packet["errors"]),
                "errors": packet["errors"],
            }
            for packet in review_packets
        ],
        "eligible_reviewer_packet_count": len(official_packets),
        "exploratory_eligible_reviewer_packet_count": len(exploratory_packets),
        "pairwise_agreement": official_pairwise_agreement,
        "exploratory_pairwise_agreement": exploratory_pairwise_agreement,
    }


def build_adjudication_queue(
    bundle: ManualAuditBundle,
    review_packets: list[dict[str, Any]],
) -> dict[str, Any]:
    dimension_ids = rubric_dimension_ids(bundle.rubric)
    queue_entries: list[dict[str, Any]] = []
    exploratory_packets = [
        packet for packet in review_packets if packet["exploratory_eligible_for_agreement"]
    ]
    for left, right in combinations(exploratory_packets, 2):
        left_map = _completed_case_map(left, bundle.rubric)
        right_map = _completed_case_map(right, bundle.rubric)
        overlap_case_ids = sorted(set(left_map) & set(right_map))
        for case_id in overlap_case_ids:
            left_case = left_map[case_id]
            right_case = right_map[case_id]
            differing_dimensions = [
                dimension_id
                for dimension_id in dimension_ids
                if left_case["scores"][dimension_id] != right_case["scores"][dimension_id]
            ]
            label_disagreement = left_case["overall_label"] != right_case["overall_label"]
            if not differing_dimensions and not label_disagreement:
                continue
            queue_entries.append(
                {
                    "case_id": case_id,
                    "reviewer_pair": [left["reviewer_ids"][0], right["reviewer_ids"][0]],
                    "reviewer_roles": [left["reviewer_roles"][0], right["reviewer_roles"][0]],
                    "differing_dimensions": differing_dimensions,
                    "label_disagreement": label_disagreement,
                    "left_total_score": left_case["total_score"],
                    "right_total_score": right_case["total_score"],
                    "left_overall_label": left_case["overall_label"],
                    "right_overall_label": right_case["overall_label"],
                }
            )

    status = "adjudication_queue_ready" if queue_entries else "no_disagreements_detected"
    return {
        "status": status,
        "entry_count": len(queue_entries),
        "entries": queue_entries,
    }


def render_reviews_readme(bundle: ManualAuditBundle) -> str:
    return "\n".join(
        [
            "# Manual Audit Review Packets",
            "",
            "This directory holds flat reviewer packets for the pilot manual-audit workflow.",
            "",
            "## Files",
            "",
            "- `reviewer_1_seed.csv`: projection of the current seed adjudicated subset into one-row-per-case reviewer format.",
            "- `reviewer_2_blank_template.csv`: blank packet for an independent second reviewer.",
            "- `reviewer_2_shadow_demo.csv`: synthetic dry-run second reviewer packet for exercising agreement and adjudication code paths. This file is not eligible for official benchmark agreement claims.",
            "",
            "## Workflow",
            "",
            "1. Copy `reviewer_2_blank_template.csv` to a reviewer-specific filename.",
            "2. Fill one row per case, including all rubric scores, evidence snippets, and the overall label.",
            "3. Rebuild the audit workflow artifacts to refresh the agreement and adjudication reports.",
            "4. Once two complete official reviewer packets exist, adjudicate disagreements into the canonical subset.",
            "",
            "The shadow demo packet exists only to prove the pipeline works end to end before a real second reviewer is available.",
            "",
            "## Covered Cases",
            "",
            f"- Case count: `{bundle.summary['case_count']}`",
            f"- Task IDs: `{', '.join(bundle.summary['task_ids'])}`",
            f"- Dimension IDs: `{', '.join(bundle.summary['dimension_ids'])}`",
            "",
        ]
    ) + "\n"


def render_manual_audit_agreement_markdown(
    bundle: ManualAuditBundle,
    summary: dict[str, Any],
    *,
    workspace_root: str | Path = ".",
) -> str:
    workspace = Path(workspace_root).resolve()
    packet_rows = [
        [
            _relative_path_string(Path(packet["path"]), workspace_root=workspace),
            ", ".join(packet["reviewer_ids"]) or "n/a",
            ", ".join(packet["reviewer_roles"]) or "n/a",
            packet["packet_status"],
            packet["completed_case_count"],
            "yes" if packet["eligible_for_agreement"] else "no",
            "yes" if packet["exploratory_eligible_for_agreement"] else "no",
            packet["error_count"],
        ]
        for packet in summary["packet_inventory"]
    ]

    lines = [
        "# Manual Audit Agreement Summary",
        "",
        "Agreement reporting for the pilot manual-audit workflow.",
        "",
        "## Status",
        "",
        f"- Official agreement status: `{summary['official_status']}`",
        f"- Exploratory dry-run status: `{summary['exploratory_status']}`",
        f"- Official eligible completed reviewer packets: `{summary['eligible_reviewer_packet_count']}`",
        f"- Exploratory eligible completed reviewer packets: `{summary['exploratory_eligible_reviewer_packet_count']}`",
        f"- Seed subset cases: `{bundle.summary['case_count']}`",
        "",
        "## Packet Inventory",
        "",
        render_markdown_table(
            [
                "Packet",
                "Reviewer",
                "Role",
                "Status",
                "Completed Cases",
                "Official Eligible",
                "Exploratory Eligible",
                "Errors",
            ],
            packet_rows or [["(none)", "n/a", "n/a", "missing", 0, "no", "no", 1]],
        ),
        "",
        "## Official Pairwise Agreement",
        "",
    ]

    if not summary["pairwise_agreement"]:
        lines.extend(
            [
                "No official reviewer pair is available yet.",
                "",
                "Next action: collect at least one independent second reviewer packet with complete scores and evidence for every case.",
                "",
            ]
        )
    else:
        for item in summary["pairwise_agreement"]:
            pair_label = " vs ".join(item["reviewer_pair"])
            lines.extend(
                [
                    f"### {pair_label}",
                    "",
                    f"- Status: `{item['status']}`",
                    f"- Overlap case count: `{item['overlap_case_count']}`",
                ]
            )
            if item["status"] != "pairwise_agreement_available":
                lines.extend(["", "No shared completed cases were found.", ""])
                continue
            lines.extend(
                [
                    f"- Overall-label exact agreement: `{item['overall_label_exact_agreement']}`",
                    f"- Overall-label kappa: `{item['overall_label_kappa']}`",
                    f"- Exact total-score match rate: `{item['exact_total_score_match_rate']}`",
                    f"- Mean absolute total-score difference: `{item['mean_abs_total_score_diff']}`",
                    f"- Cases with any disagreement: `{item['cases_with_any_disagreement']}`",
                    "",
                    render_markdown_table(
                        ["Dimension", "Exact Agreement", "Quadratic Weighted Kappa"],
                        [
                            [
                                detail["dimension_id"],
                                detail["exact_agreement_rate"],
                                detail["quadratic_weighted_kappa"],
                            ]
                            for detail in item["per_dimension"]
                        ],
                    ),
                    "",
                ]
            )

    lines.extend(["## Exploratory Dry Run", ""])

    if not summary["exploratory_pairwise_agreement"]:
        lines.extend(["No exploratory reviewer pair is available.", ""])
        return "\n".join(lines)

    for item in summary["exploratory_pairwise_agreement"]:
        pair_label = " vs ".join(item["reviewer_pair"])
        lines.extend(
            [
                f"### {pair_label}",
                "",
                f"- Status: `{item['status']}`",
                f"- Overlap case count: `{item['overlap_case_count']}`",
            ]
        )
        if item["status"] != "pairwise_agreement_available":
            lines.extend(["", "No shared completed cases were found.", ""])
            continue
        lines.extend(
            [
                f"- Overall-label exact agreement: `{item['overall_label_exact_agreement']}`",
                f"- Overall-label kappa: `{item['overall_label_kappa']}`",
                f"- Exact total-score match rate: `{item['exact_total_score_match_rate']}`",
                f"- Mean absolute total-score difference: `{item['mean_abs_total_score_diff']}`",
                f"- Cases with any disagreement: `{item['cases_with_any_disagreement']}`",
                "",
                render_markdown_table(
                    ["Dimension", "Exact Agreement", "Quadratic Weighted Kappa"],
                    [
                        [
                            detail["dimension_id"],
                            detail["exact_agreement_rate"],
                            detail["quadratic_weighted_kappa"],
                        ]
                        for detail in item["per_dimension"]
                    ],
                ),
                "",
            ]
        )

    return "\n".join(lines)


def render_manual_audit_adjudication_markdown(queue: dict[str, Any]) -> str:
    lines = [
        "# Manual Audit Adjudication Queue",
        "",
        f"- Queue status: `{queue['status']}`",
        f"- Disagreement entry count: `{queue['entry_count']}`",
        "",
    ]
    if not queue["entries"]:
        lines.append("No disagreements are queued for adjudication.")
        return "\n".join(lines)

    lines.extend(
        [
            render_markdown_table(
                [
                    "Case ID",
                    "Reviewer Pair",
                    "Reviewer Roles",
                    "Differing Dimensions",
                    "Label Disagreement",
                    "Total Scores",
                ],
                [
                    [
                        entry["case_id"],
                        " vs ".join(entry["reviewer_pair"]),
                        " vs ".join(entry["reviewer_roles"]),
                        ", ".join(entry["differing_dimensions"]) or "(label only)",
                        "yes" if entry["label_disagreement"] else "no",
                        f"{entry['left_total_score']} vs {entry['right_total_score']}",
                    ]
                    for entry in queue["entries"]
                ],
            ),
            "",
        ]
    )
    return "\n".join(lines)


def _packet_is_seed(packet: dict[str, Any]) -> bool:
    roles = set(packet.get("reviewer_roles", []))
    sources = set(packet.get("review_sources", []))
    return "benchmark_author_seed_reviewer" in roles or "seed_subset_projection" in sources


def _packet_is_synthetic_shadow(packet: dict[str, Any]) -> bool:
    roles = set(packet.get("reviewer_roles", []))
    sources = set(packet.get("review_sources", []))
    return "synthetic_shadow_reviewer" in roles or "synthetic_shadow_demo" in sources


def _packet_is_template(packet: dict[str, Any]) -> bool:
    statuses = set(packet.get("review_statuses", []))
    sources = set(packet.get("review_sources", []))
    return packet.get("packet_status") == "template" or "template" in statuses or "blank_template" in sources


def _packet_path_list(review_packets: list[dict[str, Any]]) -> list[str]:
    return [str(packet["path"]) for packet in review_packets]


def build_reviewer_readiness_report(
    bundle: ManualAuditBundle,
    review_packets: list[dict[str, Any]],
    agreement_summary: dict[str, Any],
    *,
    required_independent_completed_reviewers: int = 1,
) -> dict[str, Any]:
    official_packets = [packet for packet in review_packets if packet["eligible_for_agreement"]]
    seed_packets = [
        packet
        for packet in official_packets
        if _packet_is_seed(packet) and packet["completed_case_count"] == bundle.summary["case_count"]
    ]
    independent_packets = [
        packet
        for packet in official_packets
        if not _packet_is_seed(packet)
        and not _packet_is_synthetic_shadow(packet)
        and packet["completed_case_count"] == bundle.summary["case_count"]
    ]
    template_packets = [packet for packet in review_packets if _packet_is_template(packet)]
    shadow_packets = [packet for packet in review_packets if _packet_is_synthetic_shadow(packet)]
    official_pairwise_available = any(
        item["status"] == "pairwise_agreement_available"
        for item in agreement_summary["pairwise_agreement"]
    )

    blocking_items: list[str] = []
    if not template_packets:
        blocking_items.append(
            "Regenerate reviewer_2_blank_template.csv so an independent reviewer has a canonical packet."
        )
    if not seed_packets:
        blocking_items.append(
            "Regenerate reviewer_1_seed.csv; the seed adjudication packet is missing or incomplete."
        )
    if len(independent_packets) < required_independent_completed_reviewers:
        blocking_items.append(
            "Complete at least one independent reviewer packet copied from reviewer_2_blank_template.csv."
        )
    if not official_pairwise_available:
        blocking_items.append(
            "Rebuild official agreement reporting after an independent completed packet is available."
        )

    ready = not blocking_items
    if ready:
        status = "ready_for_submission_claims"
    elif seed_packets and not independent_packets:
        status = "not_ready_seed_only"
    elif not seed_packets:
        status = "not_ready_missing_seed_packet"
    else:
        status = "not_ready_missing_official_agreement"

    return {
        "status": status,
        "ready_for_submission_claims": ready,
        "required_independent_completed_reviewers": required_independent_completed_reviewers,
        "case_count": bundle.summary["case_count"],
        "seed_completed_reviewer_packet_count": len(seed_packets),
        "independent_completed_reviewer_packet_count": len(independent_packets),
        "official_eligible_completed_reviewer_packet_count": len(official_packets),
        "exploratory_eligible_completed_reviewer_packet_count": agreement_summary[
            "exploratory_eligible_reviewer_packet_count"
        ],
        "official_agreement_status": agreement_summary["official_status"],
        "exploratory_dry_run_status": agreement_summary["exploratory_status"],
        "official_pairwise_agreement_available": official_pairwise_available,
        "official_pairwise_agreement_count": len(agreement_summary["pairwise_agreement"]),
        "exploratory_pairwise_agreement_count": len(
            agreement_summary["exploratory_pairwise_agreement"]
        ),
        "seed_reviewer_packet_paths": _packet_path_list(seed_packets),
        "independent_completed_reviewer_packet_paths": _packet_path_list(independent_packets),
        "official_eligible_reviewer_packet_paths": _packet_path_list(official_packets),
        "blank_template_packet_paths": _packet_path_list(template_packets),
        "synthetic_shadow_packet_paths": _packet_path_list(shadow_packets),
        "blocking_items": blocking_items,
        "non_blocking_cautions": [
            "reviewer_2_shadow_demo.csv is exploratory dry-run evidence only and must not be cited as official inter-rater agreement."
        ]
        if shadow_packets
        else [],
        "claim_boundary": {
            "allowed_current_claim": (
                "Seed manual-audit rubric, adjudicated subset, and reviewer workflow are present."
                if not ready
                else "Independent reviewer agreement artifacts are available for submission-strength audit claims."
            ),
            "disallowed_current_claim": (
                "Independent inter-rater reliability or official second-reviewer agreement."
                if not ready
                else ""
            ),
        },
        "next_actions": [
            "Copy reviewer_2_blank_template.csv to a reviewer-specific CSV.",
            "Fill every case with rubric scores, evidence, overall labels, and review_status=complete.",
            "Rebuild manual-audit workflow artifacts and adjudicate any official disagreements.",
        ]
        if not ready
        else [
            "Inspect pairwise agreement and adjudication queue before making final submission claims."
        ],
    }


def render_reviewer_readiness_markdown(
    readiness: dict[str, Any],
    *,
    workspace_root: str | Path = ".",
) -> str:
    workspace = Path(workspace_root).resolve()
    summary_rows = [
        ["Status", f"`{readiness['status']}`"],
        ["Ready for submission claims", "yes" if readiness["ready_for_submission_claims"] else "no"],
        [
            "Independent completed reviewers",
            (
                f"{readiness['independent_completed_reviewer_packet_count']} / "
                f"{readiness['required_independent_completed_reviewers']}"
            ),
        ],
        ["Official agreement status", f"`{readiness['official_agreement_status']}`"],
        ["Exploratory dry-run status", f"`{readiness['exploratory_dry_run_status']}`"],
        ["Seed completed packets", readiness["seed_completed_reviewer_packet_count"]],
        ["Official eligible packets", readiness["official_eligible_completed_reviewer_packet_count"]],
        ["Case count", readiness["case_count"]],
    ]
    packet_rows = []
    for field_name, label in [
        ("seed_reviewer_packet_paths", "Seed"),
        ("independent_completed_reviewer_packet_paths", "Independent complete"),
        ("blank_template_packet_paths", "Blank template"),
        ("synthetic_shadow_packet_paths", "Synthetic shadow"),
    ]:
        paths = readiness[field_name]
        if not paths:
            packet_rows.append([label, "(none)"])
            continue
        for path in paths:
            packet_rows.append(
                [
                    label,
                    f"`{_relative_path_string(Path(path), workspace_root=workspace)}`",
                ]
            )

    lines = [
        "# Manual Audit Reviewer Readiness",
        "",
        "This report gates manuscript claims about independent manual-audit agreement.",
        "",
        "## Status",
        "",
        render_markdown_table(["Field", "Value"], summary_rows),
        "",
        "## Claim Boundary",
        "",
        f"- Allowed current claim: {readiness['claim_boundary']['allowed_current_claim']}",
        f"- Disallowed current claim: {readiness['claim_boundary']['disallowed_current_claim'] or 'n/a'}",
        "",
        "## Blocking Items",
        "",
    ]
    if readiness["blocking_items"]:
        lines.extend(f"- {item}" for item in readiness["blocking_items"])
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Packet Roles",
            "",
            render_markdown_table(["Role", "Packet"], packet_rows or [["n/a", "(none)"]]),
            "",
            "## Non-Blocking Cautions",
            "",
        ]
    )
    if readiness["non_blocking_cautions"]:
        lines.extend(f"- {item}" for item in readiness["non_blocking_cautions"])
    else:
        lines.append("- None.")
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {item}" for item in readiness["next_actions"])
    return "\n".join(lines)


def build_manual_audit_workflow_artifacts(
    *,
    bundle: ManualAuditBundle | None = None,
    rubric_path: str | Path = DEFAULT_MANUAL_AUDIT_RUBRIC_PATH,
    subset_path: str | Path = DEFAULT_MANUAL_AUDIT_SUBSET_PATH,
    workspace_root: str | Path = ".",
    reviews_dir: str | Path = DEFAULT_MANUAL_AUDIT_REVIEWS_DIR,
    reports_dir: str | Path = DEFAULT_MANUAL_AUDIT_REPORTS_DIR,
    reviews_readme_path: str | Path | None = None,
    reviewer_1_seed_path: str | Path | None = None,
    reviewer_2_template_path: str | Path | None = None,
    reviewer_2_shadow_path: str | Path | None = None,
    agreement_json_path: str | Path | None = None,
    agreement_markdown_path: str | Path | None = None,
    adjudication_json_path: str | Path | None = None,
    adjudication_markdown_path: str | Path | None = None,
    reviewer_readiness_json_path: str | Path | None = None,
    reviewer_readiness_markdown_path: str | Path | None = None,
) -> dict[str, Any]:
    audit_bundle = bundle or load_manual_audit_bundle(
        rubric_path=rubric_path,
        subset_path=subset_path,
        workspace_root=workspace_root,
    )
    reviews_root = Path(reviews_dir)
    reports_root = Path(reports_dir)
    reviews_root.mkdir(parents=True, exist_ok=True)
    reports_root.mkdir(parents=True, exist_ok=True)

    reviews_readme = (
        Path(reviews_readme_path)
        if reviews_readme_path is not None
        else reviews_root / "README.md"
    )
    reviews_readme.parent.mkdir(parents=True, exist_ok=True)
    reviews_readme.write_text(render_reviews_readme(audit_bundle), encoding="utf-8")
    reviewer_1_seed_output = (
        Path(reviewer_1_seed_path)
        if reviewer_1_seed_path is not None
        else reviews_root / "reviewer_1_seed.csv"
    )
    reviewer_2_template_output = (
        Path(reviewer_2_template_path)
        if reviewer_2_template_path is not None
        else reviews_root / "reviewer_2_blank_template.csv"
    )
    reviewer_2_shadow_output = (
        Path(reviewer_2_shadow_path)
        if reviewer_2_shadow_path is not None
        else reviews_root / "reviewer_2_shadow_demo.csv"
    )

    reviewer_1_rows = build_review_packet_rows(
        audit_bundle,
        reviewer_id="reviewer_1_seed",
        reviewer_role="benchmark_author_seed_reviewer",
        blank=False,
    )
    reviewer_2_template_rows = build_review_packet_rows(
        audit_bundle,
        reviewer_id="reviewer_2",
        reviewer_role="independent_reviewer",
        blank=True,
    )
    reviewer_2_shadow_rows = build_shadow_review_packet_rows(audit_bundle)

    reviewer_1_seed_csv = write_review_packet_csv(
        reviewer_1_rows,
        audit_bundle.rubric,
        reviewer_1_seed_output,
    )
    reviewer_2_template_csv = write_review_packet_csv(
        reviewer_2_template_rows,
        audit_bundle.rubric,
        reviewer_2_template_output,
    )
    reviewer_2_shadow_csv = write_review_packet_csv(
        reviewer_2_shadow_rows,
        audit_bundle.rubric,
        reviewer_2_shadow_output,
    )

    review_packets = load_review_packets(reviews_root, audit_bundle.rubric)
    agreement_summary = summarize_manual_audit_review_workflow(audit_bundle, review_packets)
    adjudication_queue = build_adjudication_queue(audit_bundle, review_packets)
    reviewer_readiness = build_reviewer_readiness_report(
        audit_bundle,
        review_packets,
        agreement_summary,
    )

    agreement_json = (
        Path(agreement_json_path)
        if agreement_json_path is not None
        else reports_root / "agreement_summary.json"
    )
    agreement_json.parent.mkdir(parents=True, exist_ok=True)
    agreement_json.write_text(
        json.dumps(agreement_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    agreement_markdown = (
        Path(agreement_markdown_path)
        if agreement_markdown_path is not None
        else reports_root / "agreement_summary.md"
    )
    agreement_markdown.parent.mkdir(parents=True, exist_ok=True)
    agreement_markdown.write_text(
        render_manual_audit_agreement_markdown(
            audit_bundle,
            agreement_summary,
            workspace_root=workspace_root,
        )
        + "\n",
        encoding="utf-8",
    )

    adjudication_json = (
        Path(adjudication_json_path)
        if adjudication_json_path is not None
        else reports_root / "adjudication_queue.json"
    )
    adjudication_json.parent.mkdir(parents=True, exist_ok=True)
    adjudication_json.write_text(
        json.dumps(adjudication_queue, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    adjudication_markdown = (
        Path(adjudication_markdown_path)
        if adjudication_markdown_path is not None
        else reports_root / "adjudication_queue.md"
    )
    adjudication_markdown.parent.mkdir(parents=True, exist_ok=True)
    adjudication_markdown.write_text(
        render_manual_audit_adjudication_markdown(adjudication_queue) + "\n",
        encoding="utf-8",
    )

    readiness_json = (
        Path(reviewer_readiness_json_path)
        if reviewer_readiness_json_path is not None
        else reports_root / "reviewer_readiness.json"
    )
    readiness_json.parent.mkdir(parents=True, exist_ok=True)
    readiness_json.write_text(
        json.dumps(reviewer_readiness, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    readiness_markdown = (
        Path(reviewer_readiness_markdown_path)
        if reviewer_readiness_markdown_path is not None
        else reports_root / "reviewer_readiness.md"
    )
    readiness_markdown.parent.mkdir(parents=True, exist_ok=True)
    readiness_markdown.write_text(
        render_reviewer_readiness_markdown(
            reviewer_readiness,
            workspace_root=workspace_root,
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "reviews_readme_path": reviews_readme,
        "reviewer_1_seed_path": reviewer_1_seed_csv,
        "reviewer_2_template_path": reviewer_2_template_csv,
        "reviewer_2_shadow_path": reviewer_2_shadow_csv,
        "agreement_json_path": agreement_json,
        "agreement_markdown_path": agreement_markdown,
        "agreement_summary": agreement_summary,
        "adjudication_json_path": adjudication_json,
        "adjudication_markdown_path": adjudication_markdown,
        "adjudication_queue": adjudication_queue,
        "reviewer_readiness_json_path": readiness_json,
        "reviewer_readiness_markdown_path": readiness_markdown,
        "reviewer_readiness": reviewer_readiness,
    }


def load_manual_audit_bundle(
    *,
    rubric_path: str | Path = DEFAULT_MANUAL_AUDIT_RUBRIC_PATH,
    subset_path: str | Path = DEFAULT_MANUAL_AUDIT_SUBSET_PATH,
    workspace_root: str | Path = ".",
) -> ManualAuditBundle:
    rubric = load_yaml(rubric_path)
    subset = load_json(subset_path)
    errors = validate_manual_audit_bundle(
        rubric=rubric,
        subset=subset,
        rubric_path=rubric_path,
        subset_path=subset_path,
        workspace_root=workspace_root,
    )
    if errors:
        message = "\n".join(f"- {error}" for error in errors)
        raise ValueError(f"Manual audit bundle validation failed:\n{message}")
    summary = summarize_manual_audit_bundle(rubric, subset)
    return ManualAuditBundle(
        rubric_path=Path(rubric_path),
        subset_path=Path(subset_path),
        rubric=rubric,
        subset=subset,
        summary=summary,
    )
