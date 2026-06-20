from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


DEFAULT_FORBIDDEN_TERMS = (
    "data/private",
    "answer_key",
    "private_answer",
    "private_holdout_labels",
)

DEFAULT_TEXT_SUFFIXES = {
    ".ipynb",
    ".py",
    ".md",
    ".txt",
    ".log",
    ".json",
    ".yaml",
    ".yml",
    ".sh",
}


@dataclass(frozen=True)
class LeakageFinding:
    file: str
    location: str
    term: str
    context: str

    def as_dict(self) -> dict[str, str]:
        return {
            "file": self.file,
            "location": self.location,
            "term": self.term,
            "context": self.context,
        }


@dataclass(frozen=True)
class LeakageScanResult:
    ok: bool
    findings: list[LeakageFinding]
    scanned_files: int
    skipped_files: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "findings": [finding.as_dict() for finding in self.findings],
            "scanned_files": self.scanned_files,
            "skipped_files": self.skipped_files,
        }


def iter_submission_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file():
            yield path


def iter_text_lines(path: Path) -> Iterable[tuple[str, str]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    for line_no, line in enumerate(text.splitlines(), start=1):
        yield (f"line:{line_no}", line)


def iter_notebook_source_lines(path: Path) -> Iterable[tuple[str, str]]:
    try:
        import nbformat

        notebook = nbformat.read(path, as_version=4)
    except Exception:
        yield from iter_text_lines(path)
        return

    for cell_idx, cell in enumerate(notebook.cells, start=1):
        source = cell.get("source", "")
        for line_no, line in enumerate(str(source).splitlines(), start=1):
            yield (f"cell:{cell_idx}:line:{line_no}", line)


def scan_file_for_terms(
    path: Path,
    *,
    root: Path,
    forbidden_terms: tuple[str, ...],
) -> list[LeakageFinding]:
    relative = str(path.relative_to(root))
    findings: list[LeakageFinding] = []
    normalized_path = relative.lower()

    for term in forbidden_terms:
        if term.lower() in normalized_path:
            findings.append(
                LeakageFinding(
                    file=relative,
                    location="path",
                    term=term,
                    context=relative,
                )
            )

    line_iter = iter_notebook_source_lines(path) if path.suffix == ".ipynb" else iter_text_lines(path)
    for location, line in line_iter:
        normalized = line.lower()
        for term in forbidden_terms:
            if term.lower() in normalized:
                findings.append(
                    LeakageFinding(
                        file=relative,
                        location=location,
                        term=term,
                        context=line.strip()[:240],
                    )
                )

    return findings


def scan_submission_for_leakage(
    submission_dir: str | Path,
    *,
    forbidden_terms: list[str] | tuple[str, ...] | None = None,
    suffixes: set[str] | None = None,
) -> LeakageScanResult:
    root = Path(submission_dir)
    terms = tuple(forbidden_terms or DEFAULT_FORBIDDEN_TERMS)
    allowed_suffixes = suffixes or DEFAULT_TEXT_SUFFIXES
    findings: list[LeakageFinding] = []
    scanned_files = 0
    skipped_files = 0

    for path in iter_submission_files(root):
        if path.suffix not in allowed_suffixes:
            skipped_files += 1
            continue
        scanned_files += 1
        findings.extend(scan_file_for_terms(path, root=root, forbidden_terms=terms))

    return LeakageScanResult(
        ok=not findings,
        findings=findings,
        scanned_files=scanned_files,
        skipped_files=skipped_files,
    )

