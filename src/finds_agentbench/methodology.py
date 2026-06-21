from __future__ import annotations

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
)


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
        normalized = line.lower()
        for rule in rules:
            for term in rule.terms_any:
                if term.lower() in normalized:
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

