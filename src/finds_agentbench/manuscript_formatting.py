from __future__ import annotations

import json
import re
import shutil
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_MAIN_TEX_PATH = Path("papers/workshop_pilot/main.tex")
DEFAULT_FORMATTING_CHECK_JSON_PATH = Path("papers/workshop_pilot/formatting_check.json")
DEFAULT_FORMATTING_CHECK_MARKDOWN_PATH = Path("papers/workshop_pilot/formatting_check.md")
LATEX_ENGINE_CANDIDATES = ("latexmk", "tectonic", "pdflatex", "xelatex", "lualatex")

INPUT_PATTERN = re.compile(r"\\input\{([^}]+)\}")
BIBLIOGRAPHY_PATTERN = re.compile(r"\\bibliography\{([^}]+)\}")
BIB_ENTRY_PATTERN = re.compile(r"@\w+\{([^,\s]+),")
CITE_PATTERN = re.compile(r"\\cite\w*(?:\[[^\]]*\]){0,2}\{([^}]+)\}")
LABEL_PATTERN = re.compile(r"\\label\{([^}]+)\}")
REF_PATTERN = re.compile(r"\\(?:autoref|cref|Cref|ref|pageref)\{([^}]+)\}")
BEGIN_ENV_PATTERN = re.compile(r"\\begin\{([^}]+)\}")
END_ENV_PATTERN = re.compile(r"\\end\{([^}]+)\}")
TABLE_PATTERN = re.compile(r"\\begin\{table\}.*?\\end\{table\}", re.DOTALL)
TABULAR_PATTERN = re.compile(r"\\begin\{tabular\}\{([^}]+)\}")


@dataclass(frozen=True)
class ManuscriptFormattingBuildResult:
    json_path: Path
    markdown_path: Path
    report: dict[str, Any]


def workspace_relative(path: Path, *, workspace_root: Path) -> str:
    try:
        return path.resolve().relative_to(workspace_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def resolve_latex_path(raw_path: str, *, source_path: Path) -> Path:
    cleaned = raw_path.strip()
    candidate = source_path.parent / cleaned
    if candidate.suffix:
        return candidate
    tex_candidate = candidate.with_suffix(".tex")
    return tex_candidate if tex_candidate.exists() else candidate


def extract_comma_keys(payload: str) -> list[str]:
    return [item.strip() for item in payload.split(",") if item.strip()]


def discover_latex_engine() -> dict[str, Any]:
    for candidate in LATEX_ENGINE_CANDIDATES:
        resolved = shutil.which(candidate)
        if resolved:
            return {"available": True, "engine": candidate, "path": resolved}
    return {"available": False, "engine": None, "path": None}


def collect_tex_files(
    main_tex_path: str | Path,
    *,
    workspace_root: str | Path = ".",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[Path, str]]:
    root = Path(workspace_root)
    main_path = Path(main_tex_path)
    stack = [main_path]
    visited: set[Path] = set()
    files: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    contents: dict[Path, str] = {}
    while stack:
        path = stack.pop()
        normalized = path.resolve()
        if normalized in visited:
            continue
        visited.add(normalized)
        if not path.exists():
            errors.append(
                {
                    "kind": "missing_tex_input",
                    "path": workspace_relative(path, workspace_root=root),
                }
            )
            continue
        text = path.read_text(encoding="utf-8")
        contents[path] = text
        raw_inputs = INPUT_PATTERN.findall(text)
        resolved_inputs = [resolve_latex_path(raw_input, source_path=path) for raw_input in raw_inputs]
        files.append(
            {
                "path": workspace_relative(path, workspace_root=root),
                "input_count": len(resolved_inputs),
                "line_count": len(text.splitlines()),
                "size_bytes": path.stat().st_size,
            }
        )
        stack.extend(reversed(resolved_inputs))
    files.sort(key=lambda entry: entry["path"])
    return files, errors, contents


def collect_bibliographies(
    tex_contents: dict[Path, str],
    *,
    workspace_root: str | Path = ".",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], set[str]]:
    root = Path(workspace_root)
    bibliography_paths: dict[str, Path] = {}
    for source_path, text in tex_contents.items():
        for raw_payload in BIBLIOGRAPHY_PATTERN.findall(text):
            for raw_path in extract_comma_keys(raw_payload):
                candidate = source_path.parent / raw_path
                if candidate.suffix != ".bib":
                    candidate = candidate.with_suffix(".bib")
                bibliography_paths[workspace_relative(candidate, workspace_root=root)] = candidate

    bibliographies: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    bib_keys: set[str] = set()
    for relative_path, path in sorted(bibliography_paths.items()):
        if not path.exists():
            errors.append({"kind": "missing_bibliography", "path": relative_path})
            continue
        text = path.read_text(encoding="utf-8")
        keys = set(BIB_ENTRY_PATTERN.findall(text))
        bib_keys.update(keys)
        bibliographies.append(
            {
                "path": relative_path,
                "entry_count": len(keys),
                "size_bytes": path.stat().st_size,
            }
        )
    return bibliographies, errors, bib_keys


def count_tabular_columns(spec: str) -> int:
    cleaned = re.sub(r"@\{[^}]*\}", "", spec)
    cleaned = cleaned.replace("|", "").replace(" ", "")
    return sum(1 for char in cleaned if char in {"l", "c", "r", "p", "m", "b", "X", "S"})


def analyze_tables(
    tex_contents: dict[Path, str],
    *,
    input_placements: dict[Path, str] | None = None,
    workspace_root: str | Path = ".",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    root = Path(workspace_root)
    placements = input_placements or {}
    tables: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    for path, text in tex_contents.items():
        relative_path = workspace_relative(path, workspace_root=root)
        placement = placements.get(path.resolve(), "main")
        for index, match in enumerate(TABLE_PATTERN.finditer(text), start=1):
            block = match.group(0)
            label_match = LABEL_PATTERN.search(block)
            caption_present = "\\caption{" in block
            width_mitigation = "resizebox" if "\\resizebox" in block else None
            tabular_specs = TABULAR_PATTERN.findall(block)
            column_counts = [count_tabular_columns(spec) for spec in tabular_specs]
            row_lines = [line for line in block.splitlines() if " & " in line]
            max_row_length = max((len(line) for line in row_lines), default=0)
            table = {
                "path": relative_path,
                "table_index": index,
                "label": label_match.group(1) if label_match else None,
                "caption_present": caption_present,
                "tabular_count": len(tabular_specs),
                "max_column_count": max(column_counts, default=0),
                "row_count": len(row_lines),
                "max_row_length": max_row_length,
                "placement": placement,
                "width_mitigation": width_mitigation,
            }
            tables.append(table)
            if not label_match:
                errors.append(
                    {
                        "kind": "table_missing_label",
                        "path": relative_path,
                        "table_index": index,
                    }
                )
            if not caption_present:
                errors.append(
                    {
                        "kind": "table_missing_caption",
                        "path": relative_path,
                        "table_index": index,
                    }
                )
            if (table["max_column_count"] >= 7 or max_row_length >= 320) and not width_mitigation:
                warnings.append(
                    {
                        "kind": "wide_table_candidate",
                        "path": relative_path,
                        "label": table["label"],
                        "max_column_count": table["max_column_count"],
                        "max_row_length": max_row_length,
                    }
                )
            if table["row_count"] >= 30 and placement != "appendix":
                warnings.append(
                    {
                        "kind": "long_table_candidate",
                        "path": relative_path,
                        "label": table["label"],
                        "row_count": table["row_count"],
                    }
                )
    return tables, errors, warnings


def collect_unresolved_citations(tex_contents: dict[Path, str], bib_keys: set[str]) -> list[str]:
    cite_keys: set[str] = set()
    for text in tex_contents.values():
        for payload in CITE_PATTERN.findall(text):
            cite_keys.update(extract_comma_keys(payload))
    return sorted(key for key in cite_keys if key not in bib_keys)


def collect_input_placements(main_tex_path: str | Path) -> dict[Path, str]:
    main_path = Path(main_tex_path)
    if not main_path.exists():
        return {}
    text = main_path.read_text(encoding="utf-8")
    appendix_index = text.find("\\appendix")
    placements = {main_path.resolve(): "main"}
    for match in INPUT_PATTERN.finditer(text):
        input_path = resolve_latex_path(match.group(1), source_path=main_path)
        placement = "appendix" if appendix_index != -1 and match.start() > appendix_index else "main"
        placements[input_path.resolve()] = placement
    return placements


def collect_label_findings(tex_contents: dict[Path, str]) -> dict[str, Any]:
    labels: list[str] = []
    references: set[str] = set()
    for text in tex_contents.values():
        labels.extend(LABEL_PATTERN.findall(text))
        for payload in REF_PATTERN.findall(text):
            references.update(extract_comma_keys(payload))
    label_counts = Counter(labels)
    duplicate_labels = sorted(label for label, count in label_counts.items() if count > 1)
    missing_references = sorted(reference for reference in references if reference not in label_counts)
    return {
        "label_count": len(labels),
        "reference_count": len(references),
        "duplicate_labels": duplicate_labels,
        "missing_references": missing_references,
    }


def collect_environment_findings(tex_contents: dict[Path, str]) -> dict[str, Any]:
    begin_counts: Counter[str] = Counter()
    end_counts: Counter[str] = Counter()
    for text in tex_contents.values():
        begin_counts.update(BEGIN_ENV_PATTERN.findall(text))
        end_counts.update(END_ENV_PATTERN.findall(text))
    mismatches = [
        {
            "environment": environment,
            "begin_count": begin_counts[environment],
            "end_count": end_counts[environment],
        }
        for environment in sorted(set(begin_counts) | set(end_counts))
        if begin_counts[environment] != end_counts[environment]
    ]
    return {
        "environment_counts": {
            environment: {
                "begin_count": begin_counts[environment],
                "end_count": end_counts[environment],
            }
            for environment in sorted(set(begin_counts) | set(end_counts))
        },
        "mismatches": mismatches,
    }


def build_manuscript_formatting_report(
    *,
    main_tex_path: str | Path = DEFAULT_MAIN_TEX_PATH,
    workspace_root: str | Path = ".",
) -> dict[str, Any]:
    root = Path(workspace_root)
    tex_files, tex_errors, tex_contents = collect_tex_files(main_tex_path, workspace_root=root)
    input_placements = collect_input_placements(main_tex_path)
    bibliographies, bibliography_errors, bib_keys = collect_bibliographies(
        tex_contents,
        workspace_root=root,
    )
    tables, table_errors, table_warnings = analyze_tables(
        tex_contents,
        input_placements=input_placements,
        workspace_root=root,
    )
    unresolved_citations = collect_unresolved_citations(tex_contents, bib_keys)
    label_findings = collect_label_findings(tex_contents)
    environment_findings = collect_environment_findings(tex_contents)
    latex_engine = discover_latex_engine()

    hard_errors = [*tex_errors, *bibliography_errors, *table_errors]
    hard_errors.extend(
        {"kind": "unresolved_citation", "citation_key": key} for key in unresolved_citations
    )
    hard_errors.extend(
        {"kind": "duplicate_label", "label": label}
        for label in label_findings["duplicate_labels"]
    )
    hard_errors.extend(
        {"kind": "missing_label_reference", "label": label}
        for label in label_findings["missing_references"]
    )
    hard_errors.extend(
        {"kind": "environment_mismatch", **entry}
        for entry in environment_findings["mismatches"]
    )

    warnings = list(table_warnings)
    if not latex_engine["available"]:
        warnings.append(
            {
                "kind": "latex_engine_unavailable",
                "message": "Install latexmk, tectonic, pdflatex, xelatex, or lualatex before PDF compilation.",
            }
        )

    if hard_errors:
        status = "failed_static_checks"
    elif latex_engine["available"]:
        status = "static_checks_passed_pdf_compile_ready"
    else:
        status = "static_checks_passed_pdf_compile_pending"

    return {
        "status": status,
        "main_tex_path": workspace_relative(Path(main_tex_path), workspace_root=root),
        "ready_for_static_formatting_claims": not hard_errors,
        "ready_for_pdf_formatting_claims": False,
        "pdf_compile_status": (
            "not_run_engine_available"
            if latex_engine["available"]
            else "not_run_no_latex_engine"
        ),
        "latex_engine": latex_engine,
        "hard_error_count": len(hard_errors),
        "warning_count": len(warnings),
        "hard_errors": hard_errors,
        "warnings": warnings,
        "tex_file_count": len(tex_files),
        "tex_files": tex_files,
        "bibliography_count": len(bibliographies),
        "bibliographies": bibliographies,
        "citation_count": len(
            {
                key
                for text in tex_contents.values()
                for payload in CITE_PATTERN.findall(text)
                for key in extract_comma_keys(payload)
            }
        ),
        "bib_entry_count": len(bib_keys),
        "table_count": len(tables),
        "mitigated_table_count": sum(
            1
            for table in tables
            if table.get("placement") == "appendix" or table.get("width_mitigation")
        ),
        "tables": tables,
        "label_count": label_findings["label_count"],
        "reference_count": label_findings["reference_count"],
        "environment_counts": environment_findings["environment_counts"],
        "next_actions": build_next_actions(hard_errors=hard_errors, warnings=warnings),
    }


def build_next_actions(
    *,
    hard_errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> list[str]:
    if hard_errors:
        return [
            "Fix hard manuscript structure errors before treating the LaTeX scaffold as publication-ready.",
            "Re-run PYTHONPATH=src python scripts/check_pilot_manuscript_formatting.py.",
        ]
    actions = [
        "Run a real LaTeX engine and inspect the generated PDF before final submission.",
    ]
    if any(warning["kind"] == "wide_table_candidate" for warning in warnings):
        actions.append("Inspect wide-table candidates in the compiled PDF and resize or split if needed.")
    if any(warning["kind"] == "long_table_candidate" for warning in warnings):
        actions.append("Inspect long appendix tables and move them to appendix or supplementary material if needed.")
    if any(warning["kind"] == "latex_engine_unavailable" for warning in warnings):
        actions.append("Install latexmk, tectonic, pdflatex, xelatex, or lualatex for PDF compilation.")
    return actions


def render_manuscript_formatting_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Manuscript Formatting Check",
        "",
        "Static LaTeX readiness report for the workshop manuscript scaffold.",
        "",
        "## Summary",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Status | `{report['status']}` |",
        f"| Main TeX | `{report['main_tex_path']}` |",
        f"| Static formatting claims ready | {'yes' if report['ready_for_static_formatting_claims'] else 'no'} |",
        f"| PDF formatting claims ready | {'yes' if report['ready_for_pdf_formatting_claims'] else 'no'} |",
        f"| PDF compile status | `{report['pdf_compile_status']}` |",
        f"| LaTeX engine | `{report['latex_engine']['engine'] or 'unavailable'}` |",
        f"| TeX files checked | {report['tex_file_count']} |",
        f"| Bibliographies checked | {report['bibliography_count']} |",
        f"| Citations | {report['citation_count']} |",
        f"| Bib entries | {report['bib_entry_count']} |",
        f"| Tables | {report['table_count']} |",
        f"| Tables with placement/width mitigation | {report['mitigated_table_count']} |",
        f"| Hard errors | {report['hard_error_count']} |",
        f"| Warnings | {report['warning_count']} |",
        "",
        "## Hard Errors",
        "",
    ]
    if report["hard_errors"]:
        lines.extend(f"- {format_issue(entry)}" for entry in report["hard_errors"])
    else:
        lines.append("- None.")
    lines.extend(["", "## Warnings", ""])
    if report["warnings"]:
        lines.extend(f"- {format_issue(entry)}" for entry in report["warnings"])
    else:
        lines.append("- None.")
    lines.extend(["", "## Table Inventory", ""])
    lines.extend(
        [
            "| Path | Label | Columns | Rows | Max Row Length | Placement | Width Mitigation |",
            "| --- | --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for table in report["tables"]:
        lines.append(
            " | ".join(
                [
                    f"| `{table['path']}`",
                    f"`{table['label'] or ''}`",
                    str(table["max_column_count"]),
                    str(table["row_count"]),
                    str(table["max_row_length"]),
                    table["placement"],
                    f"{table['width_mitigation'] or ''} |",
                ]
            )
        )
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {action}" for action in report["next_actions"])
    lines.append("")
    return "\n".join(lines)


def format_issue(entry: dict[str, Any]) -> str:
    kind = entry["kind"]
    if kind == "missing_tex_input":
        return f"`missing_tex_input`: `{entry['path']}` does not exist."
    if kind == "missing_bibliography":
        return f"`missing_bibliography`: `{entry['path']}` does not exist."
    if kind == "unresolved_citation":
        return f"`unresolved_citation`: `{entry['citation_key']}` is cited but absent from BibTeX."
    if kind == "duplicate_label":
        return f"`duplicate_label`: `{entry['label']}` appears more than once."
    if kind == "missing_label_reference":
        return f"`missing_label_reference`: `\\ref{{{entry['label']}}}` has no matching label."
    if kind == "environment_mismatch":
        return (
            f"`environment_mismatch`: `{entry['environment']}` has "
            f"{entry['begin_count']} begin blocks and {entry['end_count']} end blocks."
        )
    if kind == "table_missing_label":
        return f"`table_missing_label`: table {entry['table_index']} in `{entry['path']}` has no label."
    if kind == "table_missing_caption":
        return f"`table_missing_caption`: table {entry['table_index']} in `{entry['path']}` has no caption."
    if kind == "wide_table_candidate":
        return (
            f"`wide_table_candidate`: `{entry['label']}` in `{entry['path']}` has "
            f"{entry['max_column_count']} columns and max row length {entry['max_row_length']}."
        )
    if kind == "long_table_candidate":
        return (
            f"`long_table_candidate`: `{entry['label']}` in `{entry['path']}` has "
            f"{entry['row_count']} rows."
        )
    if kind == "latex_engine_unavailable":
        return f"`latex_engine_unavailable`: {entry['message']}"
    return f"`{kind}`: `{entry}`"


def write_manuscript_formatting_artifacts(
    *,
    main_tex_path: str | Path = DEFAULT_MAIN_TEX_PATH,
    output_json_path: str | Path = DEFAULT_FORMATTING_CHECK_JSON_PATH,
    output_markdown_path: str | Path = DEFAULT_FORMATTING_CHECK_MARKDOWN_PATH,
    workspace_root: str | Path = ".",
) -> ManuscriptFormattingBuildResult:
    report = build_manuscript_formatting_report(
        main_tex_path=main_tex_path,
        workspace_root=workspace_root,
    )
    json_path = Path(output_json_path)
    markdown_path = Path(output_markdown_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_manuscript_formatting_markdown(report), encoding="utf-8")
    return ManuscriptFormattingBuildResult(
        json_path=json_path,
        markdown_path=markdown_path,
        report=report,
    )
