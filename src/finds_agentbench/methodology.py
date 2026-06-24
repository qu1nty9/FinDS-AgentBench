from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from finds_agentbench.leakage import (
    DEFAULT_TEXT_SUFFIXES,
    iter_notebook_source_lines,
    iter_submission_files,
    iter_text_lines,
)


@dataclass(frozen=True)
class MethodologyRule:
    rule_id: str
    severity: str
    terms_any: tuple[str, ...]
    message: str
    patterns_any: tuple[str, ...] = ()
    suffixes: tuple[str, ...] | None = None


@dataclass(frozen=True)
class MethodologyFinding:
    file: str
    location: str
    rule_id: str
    severity: str
    term: str
    message: str
    context: str

    def as_dict(self) -> dict[str, str]:
        return {
            "file": self.file,
            "location": self.location,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "term": self.term,
            "message": self.message,
            "context": self.context,
        }


@dataclass(frozen=True)
class MethodologyScanResult:
    ok: bool
    findings: list[MethodologyFinding]
    scanned_files: int
    skipped_files: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "findings": [finding.as_dict() for finding in self.findings],
            "scanned_files": self.scanned_files,
            "skipped_files": self.skipped_files,
        }


DEFAULT_METHODOLOGY_RULES = (
    MethodologyRule(
        rule_id="random_train_test_split",
        severity="error",
        terms_any=("train_test_split(",),
        message="Random train/test split is usually invalid for temporal financial tasks.",
    ),
    MethodologyRule(
        rule_id="explicit_shuffle",
        severity="error",
        terms_any=("shuffle=True", "shuffle = True"),
        message="Explicit shuffling can break temporal ordering.",
    ),
    MethodologyRule(
        rule_id="kfold_temporal_cv",
        severity="warning",
        terms_any=("KFold(", "StratifiedKFold(", "cross_val_score("),
        message="K-fold validation may leak time unless it is replaced with a temporal split.",
    ),
    MethodologyRule(
        rule_id="fit_transform_preprocessing",
        severity="warning",
        terms_any=(".fit_transform(", "fit_transform("),
        message="fit_transform can leak validation data if preprocessing is fit before splitting.",
    ),
    MethodologyRule(
        rule_id="private_holdout_protocol_reference",
        severity="warning",
        terms_any=("private_temporal_holdout", "private holdout score"),
        message="Private holdout references should be checked for possible tuning or protocol misuse.",
    ),
    MethodologyRule(
        rule_id="negative_shift_future_construction",
        severity="warning",
        terms_any=(),
        patterns_any=(r"\bshift\(\s*-\s*\d+\s*\)",),
        suffixes=(".py", ".ipynb", ".sh"),
        message=(
            "Negative shift usually pulls future information and should be limited to carefully "
            "audited label construction."
        ),
    ),
    MethodologyRule(
        rule_id="centered_rolling_window",
        severity="warning",
        terms_any=(),
        patterns_any=(r"rolling\([^)]*center\s*=\s*True",),
        suffixes=(".py", ".ipynb", ".sh"),
        message=(
            "Centered rolling windows can include future observations and should be justified explicitly."
        ),
    ),
    MethodologyRule(
        rule_id="backfill_future_imputation",
        severity="warning",
        terms_any=(),
        patterns_any=(
            r"\bbfill\(",
            r"\bbackfill\(",
            r"fillna\([^)]*method\s*=\s*[\"']bfill[\"']",
        ),
        suffixes=(".py", ".ipynb", ".sh"),
        message="Backfilling can propagate future values backward into earlier timestamps.",
    ),
    MethodologyRule(
        rule_id="target_like_feature_construction",
        severity="warning",
        terms_any=(),
        patterns_any=(
            r"\b(feature|features|feature_columns|predictors|inputs|x)\w*\s*=.*\b("
            r"target|label|next_day_return|future_return|event_reaction_positive|"
            r"next_day_positive_return"
            r")\b",
        ),
        suffixes=(".py", ".ipynb", ".sh"),
        message=(
            "Feature construction appears to reference target-like columns and should be checked "
            "for label leakage."
        ),
    ),
)

SHORT_HORIZON_HINTS = (
    "1 business day",
    "one business day",
    "next business day",
    "1 day",
    "one day",
    "next day",
    "1 period",
    "one period",
    "next period",
)

HIGH_RISK_FORBIDDEN_COLUMN_HINTS = (
    "answer_key",
    "future",
    "holdout",
    "label",
    "next_day",
    "private",
    "t_plus_1",
    "target",
)


def slugify_rule_fragment(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def task_horizon_context(task_spec: dict[str, Any]) -> str:
    target = task_spec.get("target", {})
    information_set = task_spec.get("information_set", {})
    splits = task_spec.get("splits", {})
    parts = (
        str(target.get("horizon", "")).strip(),
        str(target.get("definition", "")).strip(),
        str(target.get("label_construction", "")).strip(),
        str(information_set.get("prediction_timestamp", "")).strip(),
        str(splits.get("embargo_or_gap", "")).strip(),
    )
    return " ".join(part for part in parts if part).lower()


def task_has_short_horizon(task_spec: dict[str, Any]) -> bool:
    context = task_horizon_context(task_spec)
    return any(hint in context for hint in SHORT_HORIZON_HINTS)


def severity_for_forbidden_column(column: str) -> str:
    normalized = column.lower()
    if any(hint in normalized for hint in HIGH_RISK_FORBIDDEN_COLUMN_HINTS):
        return "error"
    return "warning"


def task_specific_methodology_rules(task_spec: dict[str, Any]) -> tuple[MethodologyRule, ...]:
    leakage_checks = task_spec.get("leakage_checks", {})
    target = task_spec.get("target", {})
    short_horizon = task_has_short_horizon(task_spec)

    candidate_columns: list[str] = []
    for value in leakage_checks.get("forbidden_columns", []):
        if isinstance(value, str) and value.strip():
            candidate_columns.append(value.strip())
    target_name = target.get("name")
    if isinstance(target_name, str) and target_name.strip():
        candidate_columns.append(target_name.strip())

    unique_columns: list[str] = []
    seen: set[str] = set()
    for column in candidate_columns:
        normalized = column.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        unique_columns.append(column)

    rules: list[MethodologyRule] = []
    for column in unique_columns:
        escaped = re.escape(column)
        rule_suffix = slugify_rule_fragment(column)
        severity = severity_for_forbidden_column(column)
        rules.append(
            MethodologyRule(
                rule_id=f"task_forbidden_feature_reference__{rule_suffix}",
                severity=severity,
                terms_any=(),
                patterns_any=(
                    rf"\b(feature|features|feature_columns|predictors|inputs|x)\w*\b[^\n]*\b{escaped}\b",
                    rf"\[\[[^\n]*\b{escaped}\b[^\n]*\]\]",
                    rf"\b(merge|join)\([^)]*\b{escaped}\b",
                ),
                suffixes=(".py", ".ipynb", ".sh"),
                message=(
                    f"Task-forbidden column `{column}` appears in feature selection, dataframe "
                    "slicing, or merge logic and should be audited for label leakage."
                ),
            )
        )

    future_join_severity = "error" if short_horizon else "warning"
    future_join_label = "short-horizon" if short_horizon else "temporally aligned"
    rules.extend(
        [
            MethodologyRule(
                rule_id="future_aligned_merge_join",
                severity=future_join_severity,
                terms_any=(),
                patterns_any=(
                    r"\b(merge|join|merge_asof)\([^)]*\b("
                    r"next_day\w*|next_business_day\w*|t_plus_1\w*|"
                    r"future_[A-Za-z0-9_]*|[A-Za-z0-9_]*_future|"
                    r"lead_[A-Za-z0-9_]*|[A-Za-z0-9_]*_lead|tomorrow\w*"
                    r")\b",
                ),
                suffixes=(".py", ".ipynb", ".sh"),
                message=(
                    f"Merge/join logic appears to reference future-aligned data for a {future_join_label} "
                    "task and should be audited for timestamp leakage."
                ),
            ),
            MethodologyRule(
                rule_id="forward_merge_asof_direction",
                severity=future_join_severity,
                terms_any=(),
                patterns_any=(
                    r"\bmerge_asof\([^)]*direction\s*=\s*[\"']forward[\"']",
                ),
                suffixes=(".py", ".ipynb", ".sh"),
                message=(
                    f"`merge_asof(..., direction=\"forward\")` can pull future rows into a {future_join_label} "
                    "prediction context and should be justified explicitly."
                ),
            ),
        ]
    )
    return tuple(rules)


def methodology_rules_for_task(task_spec: dict[str, Any]) -> tuple[MethodologyRule, ...]:
    return DEFAULT_METHODOLOGY_RULES + task_specific_methodology_rules(task_spec)


def rule_matches_line(rule: MethodologyRule, path: Path, line: str) -> str | None:
    if rule.suffixes is not None and path.suffix not in rule.suffixes:
        return None

    normalized = line.lower()
    for term in rule.terms_any:
        if term.lower() in normalized:
            return term

    for pattern in rule.patterns_any:
        match = re.search(pattern, line, flags=re.IGNORECASE)
        if match is not None:
            return match.group(0)

    return None


def scan_file_for_methodology(
    path: Path,
    *,
    root: Path,
    rules: tuple[MethodologyRule, ...],
) -> list[MethodologyFinding]:
    relative = str(path.relative_to(root))
    findings: list[MethodologyFinding] = []
    line_iter = iter_notebook_source_lines(path) if path.suffix == ".ipynb" else iter_text_lines(path)

    for location, line in line_iter:
        for rule in rules:
            term = rule_matches_line(rule, path, line)
            if term is not None:
                findings.append(
                    MethodologyFinding(
                        file=relative,
                        location=location,
                        rule_id=rule.rule_id,
                        severity=rule.severity,
                        term=term,
                        message=rule.message,
                        context=line.strip()[:240],
                    )
                )

    return findings


def scan_submission_methodology(
    submission_dir: str | Path,
    *,
    rules: tuple[MethodologyRule, ...] = DEFAULT_METHODOLOGY_RULES,
    suffixes: set[str] | None = None,
    fail_on_warnings: bool = False,
) -> MethodologyScanResult:
    root = Path(submission_dir)
    allowed_suffixes = suffixes or DEFAULT_TEXT_SUFFIXES
    findings: list[MethodologyFinding] = []
    scanned_files = 0
    skipped_files = 0

    for path in iter_submission_files(root):
        if path.suffix not in allowed_suffixes:
            skipped_files += 1
            continue
        scanned_files += 1
        findings.extend(scan_file_for_methodology(path, root=root, rules=rules))

    has_errors = any(finding.severity == "error" for finding in findings)
    has_warnings = any(finding.severity == "warning" for finding in findings)
    return MethodologyScanResult(
        ok=not has_errors and not (fail_on_warnings and has_warnings),
        findings=findings,
        scanned_files=scanned_files,
        skipped_files=skipped_files,
    )
