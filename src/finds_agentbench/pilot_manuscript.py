from __future__ import annotations

import json
import os
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from finds_agentbench.manuscript_formatting import write_manuscript_formatting_artifacts
from finds_agentbench.paper_artifacts import latex_escape
from finds_agentbench.related_work import render_bibtex, render_related_work_tex


DEFAULT_MANIFEST_PATH = Path("docs/releases/pilot_v0/manifest.json")
DEFAULT_REFERENCE_RESULTS_PATH = Path("docs/releases/pilot_v0/reference_results.json")
DEFAULT_MANUAL_AUDIT_SUBSET_PATH = Path("audits/pilot_v0/adjudicated_subset.json")
DEFAULT_STATISTICAL_COMPARISON_PATH = Path(
    "docs/releases/pilot_v0/statistical_artifacts/agent_vs_best_baseline.json"
)
DEFAULT_STATISTICAL_METHODS_TEX_PATH = Path(
    "docs/releases/pilot_v0/statistical_artifacts/methods/statistical_methods.tex"
)
DEFAULT_SUMMARY_UNCERTAINTY_TABLE_PATH = Path(
    "docs/releases/pilot_v0/statistical_artifacts/tables/summary_uncertainty_overall_score.tex"
)
DEFAULT_AGENT_VS_BASELINE_TABLE_PATH = Path(
    "docs/releases/pilot_v0/statistical_artifacts/tables/agent_vs_best_baseline_overall_score.tex"
)
DEFAULT_PROTOCOL_TABLE_PATH = Path(
    "docs/releases/pilot_v0/paper_artifacts/tables/pilot_protocol.tex"
)
DEFAULT_OUTPUT_DIR = Path("papers/workshop_pilot")


@dataclass(frozen=True)
class PilotManuscriptBuildResult:
    output_dir: Path
    main_tex_path: Path
    related_work_tex_path: Path
    references_bib_path: Path
    audit_failure_examples_tex_path: Path
    audit_failure_examples_markdown_path: Path
    audit_failure_examples_json_path: Path
    formatting_check_json_path: Path
    formatting_check_markdown_path: Path
    readme_path: Path
    checklist_path: Path
    metadata_path: Path


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def require_existing_paths(paths: dict[str, Path]) -> None:
    missing = [f"{name}={path}" for name, path in sorted(paths.items()) if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing expected manuscript inputs: " + ", ".join(missing))


def relative_latex_path(path: str | Path, *, output_dir: str | Path) -> str:
    return Path(os.path.relpath(Path(path), Path(output_dir))).as_posix()


def reference_section(reference_results: dict[str, Any], section_id: str) -> dict[str, Any]:
    for section in reference_results.get("sections", []):
        if section.get("section_id") == section_id:
            return section
    raise KeyError(f"Reference-results section not found: {section_id}")


def pilot_protocol(manifest: dict[str, Any]) -> dict[str, Any]:
    for protocol in manifest.get("protocols", []):
        if protocol.get("protocol_id") == "pilot_protocol":
            return protocol
    raise KeyError("pilot_protocol is missing from manifest")


def format_count_phrase(count: int, singular: str, plural: str | None = None) -> str:
    return f"{count} {singular if count == 1 else plural or singular + 's'}"


def summarize_reference_results(
    *,
    manifest: dict[str, Any],
    reference_results: dict[str, Any],
    statistical_comparison: dict[str, Any],
) -> dict[str, Any]:
    protocol = pilot_protocol(manifest)
    protocol_section = reference_section(reference_results, "pilot_protocol")
    protocol_rows = protocol_section["rows"]
    overall_comparisons = [
        row
        for row in statistical_comparison["rows"]
        if row.get("metric") == "score.overall_score"
    ]
    direction_counts = Counter(str(row.get("direction", "")) for row in overall_comparisons)
    run_counts = sorted({int(row["run_count"]) for row in protocol_rows if row.get("run_count") is not None})
    completed_counts = sorted(
        {int(row["completed_count"]) for row in protocol_rows if row.get("completed_count") is not None}
    )
    manual_audit = manifest["manual_audit"]
    external_agents = manifest.get("external_agents", {})
    submission_readiness = manifest.get("submission_readiness", {})
    return {
        "benchmark_id": manifest["benchmark_id"],
        "benchmark_version": manifest["benchmark_version"],
        "release_stage": manifest["release_stage"],
        "task_count": int(manifest["task_count"]),
        "runnable_task_count": int(manifest["runnable_task_count"]),
        "track_count": len(manifest["tracks"]),
        "track_names": [track["track"] for track in manifest["tracks"]],
        "protocol_task_count": len(protocol["task_ids"]),
        "protocol_cell_count": len(protocol_rows),
        "baseline_cell_count": sum(1 for row in protocol_rows if row.get("run_type") == "baseline"),
        "agent_cell_count": sum(1 for row in protocol_rows if row.get("run_type") == "agent"),
        "run_counts": run_counts,
        "completed_counts": completed_counts,
        "overall_comparison_count": len(overall_comparisons),
        "overall_agent_higher_count": direction_counts["agent_higher"],
        "overall_baseline_higher_count": direction_counts["baseline_higher"],
        "overall_tie_count": direction_counts["tie"],
        "manual_audit_case_count": manual_audit["case_count"],
        "manual_audit_reviewed_task_count": manual_audit["reviewed_task_count"],
        "manual_audit_status": manual_audit["status"],
        "reviewer_readiness_status": manual_audit.get("reviewer_readiness_status", "unknown"),
        "ready_for_submission_claims": bool(manual_audit.get("ready_for_submission_claims", False)),
        "independent_completed_reviewer_packet_count": int(
            manual_audit.get("independent_completed_reviewer_packet_count", 0)
        ),
        "reviewer_readiness_blocking_items": manual_audit.get(
            "reviewer_readiness_blocking_items",
            [],
        ),
        "reviewer_readiness_markdown_path": manual_audit.get(
            "reviewer_readiness_markdown_path",
            "",
        ),
        "external_agent_readiness_status": external_agents.get(
            "readiness_status",
            "unknown",
        ),
        "ready_for_external_agent_claims": bool(
            external_agents.get("ready_for_external_agent_claims", False)
        ),
        "external_agent_configuration_count": int(
            external_agents.get("external_agent_configuration_count", 0)
        ),
        "completed_external_agent_configuration_count": int(
            external_agents.get("completed_external_agent_configuration_count", 0)
        ),
        "external_agent_blocking_items": external_agents.get("blocking_items", []),
        "submission_readiness_status": submission_readiness.get("status", "unknown"),
        "ready_for_workshop_submission": bool(
            submission_readiness.get("ready_for_workshop_submission", False)
        ),
        "submission_ready_gate_count": int(submission_readiness.get("ready_gate_count", 0)),
        "submission_gate_count": int(submission_readiness.get("gate_count", 0)),
        "submission_blocking_gate_count": int(submission_readiness.get("blocking_gate_count", 0)),
        "agreement_status": manual_audit["agreement_status"],
        "exploratory_agreement_status": manual_audit["exploratory_agreement_status"],
        "release_build_command": manifest["release_build_command"],
    }


def case_sort_key(case: dict[str, Any]) -> tuple[int, str]:
    return int(case.get("total_score", 999)), str(case.get("case_id", ""))


def case_low_dimension_ids(case: dict[str, Any]) -> list[str]:
    rubric_scores = case.get("rubric_scores", {})
    low_dimensions: list[str] = []
    if not isinstance(rubric_scores, dict):
        return low_dimensions
    for dimension_id, entry in rubric_scores.items():
        if isinstance(entry, dict) and int(entry.get("score", 0)) < 2:
            low_dimensions.append(str(dimension_id))
    return low_dimensions


def case_primary_evidence(case: dict[str, Any]) -> str:
    rubric_scores = case.get("rubric_scores", {})
    if not isinstance(rubric_scores, dict):
        return ""
    scored_entries = [
        (int(entry.get("score", 0)), str(dimension_id), str(entry.get("evidence", "")))
        for dimension_id, entry in rubric_scores.items()
        if isinstance(entry, dict)
    ]
    if not scored_entries:
        return ""
    _, _, evidence = sorted(scored_entries)[0]
    return evidence


def select_audit_failure_examples(
    manual_audit_subset: dict[str, Any],
    *,
    limit: int = 4,
) -> list[dict[str, Any]]:
    cases = manual_audit_subset.get("cases", [])
    if not isinstance(cases, list):
        return []
    selected: list[dict[str, Any]] = []
    for case in sorted((case for case in cases if isinstance(case, dict)), key=case_sort_key):
        low_dimensions = case_low_dimension_ids(case)
        if not low_dimensions:
            continue
        selected.append(
            {
                "case_id": case["case_id"],
                "task_id": case["task_id"],
                "run_type": case["run_type"],
                "agent_id": case["agent_id"],
                "run_label": case["run_label"],
                "artifact_root": case["artifact_root"],
                "writeup_path": case.get("source_paths", {}).get("writeup", ""),
                "overall_label": case["overall_label"],
                "total_score": case["total_score"],
                "low_dimension_ids": low_dimensions,
                "primary_manual_findings": case.get("primary_manual_findings", []),
                "primary_evidence": case_primary_evidence(case),
                "adjudication_note": case.get("adjudication_note", ""),
            }
        )
        if len(selected) >= limit:
            break
    return selected


def render_audit_failure_examples_tex(examples: list[dict[str, Any]]) -> str:
    lines = [
        "\\section{Qualitative Failure Examples}",
        (
            "The manual audit illustrates why predictive scores and automatic artifact validators are "
            "insufficient for financial research-agent evaluation. The examples below are generated from "
            "the seed adjudicated audit subset and preserve task, run, and artifact references."
        ),
        "",
        "\\begin{description}[leftmargin=*]",
    ]
    for example in examples:
        findings = format_sentence_list(example["primary_manual_findings"])
        low_dimensions = ", ".join(str(item).replace("_", "\\_") for item in example["low_dimension_ids"])
        lines.extend(
            [
                (
                    "\\item["
                    f"{latex_escape(str(example['case_id']))}] "
                    f"\\textbf{{Task/system:}} \\texttt{{{latex_escape(str(example['task_id']))}}} / "
                    f"\\texttt{{{latex_escape(str(example['agent_id']))}}} "
                    f"({latex_escape(str(example['run_type']))}, run label "
                    f"\\texttt{{{latex_escape(str(example['run_label']))}}}). "
                    f"\\textbf{{Audit label:}} \\texttt{{{latex_escape(str(example['overall_label']))}}}, "
                    f"total score {example['total_score']}."
                ),
                (
                    f"\\textbf{{Low-scoring dimensions:}} {low_dimensions}. "
                    f"\\textbf{{Primary findings:}} {latex_escape(findings)} "
                    f"\\textbf{{Evidence:}} {latex_escape(str(example['primary_evidence']))}"
                ),
                (
                    "\\textbf{Artifact reference:} "
                    f"\\texttt{{{latex_escape(str(example['writeup_path']))}}}."
                ),
                "",
            ]
        )
    lines.extend(["\\end{description}", ""])
    return "\n".join(lines)


def render_audit_failure_examples_markdown(examples: list[dict[str, Any]]) -> str:
    lines = [
        "# Qualitative Failure Examples",
        "",
        "Generated from `audits/pilot_v0/adjudicated_subset.json` for use in the workshop manuscript.",
        "",
    ]
    for example in examples:
        findings = format_sentence_list(example["primary_manual_findings"])
        low_dimensions = ", ".join(str(item) for item in example["low_dimension_ids"])
        lines.extend(
            [
                f"## {example['case_id']}",
                "",
                f"- Task: `{example['task_id']}`",
                f"- System: `{example['agent_id']}` (`{example['run_type']}`)",
                f"- Run label: `{example['run_label']}`",
                f"- Audit label: `{example['overall_label']}`",
                f"- Total score: `{example['total_score']}`",
                f"- Low-scoring dimensions: `{low_dimensions}`",
                f"- Primary findings: {findings}",
                f"- Evidence: {example['primary_evidence']}",
                f"- Writeup reference: `{example['writeup_path']}`",
                "",
            ]
        )
    return "\n".join(lines)


def format_sentence_list(items: list[Any]) -> str:
    cleaned = [str(item).strip().rstrip(".") for item in items if str(item).strip()]
    if not cleaned:
        return ""
    return "; ".join(cleaned) + "."


def render_main_tex(
    *,
    summary: dict[str, Any],
    statistical_methods_tex_path: str,
    related_work_tex_path: str,
    audit_failure_examples_tex_path: str,
    summary_uncertainty_table_path: str,
    agent_vs_baseline_table_path: str,
    protocol_table_path: str,
) -> str:
    run_count_text = ", ".join(str(value) for value in summary["run_counts"])
    track_text = ", ".join(str(track) for track in summary["track_names"])
    return "\n".join(
        [
            "\\documentclass[11pt]{article}",
            "\\usepackage[margin=1in]{geometry}",
            "\\usepackage{booktabs}",
            "\\usepackage{graphicx}",
            "\\usepackage{hyperref}",
            "\\usepackage{microtype}",
            "\\usepackage{enumitem}",
            "\\title{FinDS-AgentBench: A Pilot Benchmark for Financial Data-Science Agents}",
            "\\author{FinDS-AgentBench Contributors}",
            "\\date{}",
            "",
            "\\begin{document}",
            "\\maketitle",
            "",
            "\\begin{abstract}",
            (
                "We introduce FinDS-AgentBench, a benchmark for evaluating AI agents that "
                "perform end-to-end financial data-science research under temporal, leakage, "
                "reproducibility, and decision-quality constraints. The current pilot release "
                f"contains {summary['task_count']} tasks, {summary['runnable_task_count']} runnable "
                f"tasks, and {summary['track_count']} tracks. The repeated-run protocol covers "
                f"{summary['protocol_task_count']} tasks and {summary['protocol_cell_count']} "
                "task-system cells with fixed seeds and release-owned artifacts. In the pilot "
                "overall-score paired comparison against the best baseline per task, agents are "
                f"higher in {summary['overall_agent_higher_count']} cases, baselines are higher in "
                f"{summary['overall_baseline_higher_count']} cases, and {summary['overall_tie_count']} "
                "cases are ties. The release ships task cards, data manifests, reference results, "
                "uncertainty tables, manual-audit artifacts, and a deterministic release "
                "reproducibility check."
            ),
            "\\end{abstract}",
            "",
            "\\section{Introduction}",
            (
                "Financial machine-learning research is unusually sensitive to timestamp discipline, "
                "point-in-time data availability, target leakage, validation design, transaction costs, "
                "and narrative overclaiming. Generic data-science and tool-use benchmarks do not isolate "
                "these failure modes. FinDS-AgentBench is designed to evaluate whether agents can produce "
                "auditable financial research artifacts rather than merely plausible notebooks."
            ),
            "",
            "\\paragraph{Contributions.}",
            "\\begin{enumerate}[leftmargin=*]",
            "\\item A pilot benchmark release with task specifications, public data manifests, task cards, and evaluation cards.",
            "\\item A command-based agent and baseline protocol with repeated runs, fixed seeds, clean release builds, and manifest validation.",
            "\\item Publication-facing reference results, uncertainty estimates, paired agent-vs-baseline comparisons, and paper-ready tables.",
            "\\item A manual-audit workflow covering temporal protocol correctness, leakage awareness, evidence use, claim discipline, and reproducibility trace completeness.",
            "\\end{enumerate}",
            "",
            f"\\input{{{related_work_tex_path}}}",
            "",
            "\\section{Benchmark Design}",
            (
                f"The pilot release spans {latex_escape(track_text)}. Each task specification identifies "
                "the prediction timestamp, allowed public information, target horizon, temporal split, "
                "required submission artifacts, primary metric, and leakage constraints. The benchmark "
                "separates predictive performance from artifact validity so that a high private-holdout "
                "score does not erase reproducibility, leakage, or methodology failures."
            ),
            "",
            "\\section{Pilot Release}",
            (
                f"The release manifest records {summary['task_count']} tasks and "
                f"{summary['runnable_task_count']} runnable tasks. The repeated-run pilot protocol covers "
                f"{summary['protocol_task_count']} tasks, excluding the leakage-audit task from the "
                "predictive baseline/agent sweep because it uses an audit-style scoring surface rather "
                "than a standard prediction holdout."
            ),
            "",
            "\\section{Evaluation Protocol}",
            (
                f"The combined pilot protocol evaluates {summary['baseline_cell_count']} baseline "
                f"task-system cells and {summary['agent_cell_count']} agent task-system cells. Observed "
                f"run counts per cell are {latex_escape(run_count_text)}. Baselines include naive and "
                "classical models; the bundled example agents are environment-wrapped systems that select "
                "among public candidate strategies before writing holdout predictions and research artifacts. "
                f"The external-agent readiness gate is \\texttt{{{latex_escape(summary['external_agent_readiness_status'])}}} "
                f"with {summary['completed_external_agent_configuration_count']} completed external "
                "agent configurations."
            ),
            "",
            f"\\input{{{statistical_methods_tex_path}}}",
            "",
            "\\section{Results}",
            (
                "Table~\\ref{tab:pilot-agent-vs-best-baseline-score-overall-score} summarizes the "
                "paired overall-score comparison between each agent and the best completed-run baseline "
                "for the same task. Appendix Table~\\ref{tab:pilot-uncertainty-score-overall-score} "
                "reports overall-score repeated-run uncertainty for all task-system cells."
            ),
            "",
            f"\\input{{{agent_vs_baseline_table_path}}}",
            "",
            "\\section{Manual Audit and Validity Checks}",
            (
                f"The pilot manual-audit bundle currently includes {summary['manual_audit_case_count']} "
                f"cases across {summary['manual_audit_reviewed_task_count']} reviewed tasks. Its official "
                f"status is \\texttt{{{latex_escape(summary['manual_audit_status'])}}}; independent-overlap "
                f"agreement status is \\texttt{{{latex_escape(summary['agreement_status'])}}}, with "
                f"exploratory status \\texttt{{{latex_escape(summary['exploratory_agreement_status'])}}}. "
                f"The reviewer-readiness gate is \\texttt{{{latex_escape(summary['reviewer_readiness_status'])}}} "
                f"with {summary['independent_completed_reviewer_packet_count']} completed independent "
                "reviewer packets. "
                "This makes the current audit layer suitable as a seed adjudication workflow, while a "
                "submission-ready paper should add an independent second-reviewer packet."
            ),
            "",
            f"\\input{{{audit_failure_examples_tex_path}}}",
            "",
            "\\section{Reproducibility and Release Artifacts}",
            (
                "The release build is intentionally scriptable. It rebuilds suite reports, reference "
                "results, statistical artifacts, paper artifacts, task cards, data manifests, and the "
                "canonical release manifest. A separate smoke check builds the pilot release twice in "
                "isolated roots and compares deterministic publication-facing outputs by content digest."
            ),
            "",
            "\\begin{verbatim}",
            summary["release_build_command"],
            "\\end{verbatim}",
            "",
            "\\section{Limitations}",
            "\\begin{itemize}[leftmargin=*]",
            "\\item The current pilot uses a small repeated-run count, so uncertainty artifacts should be read as transparency and regression checks rather than definitive significance claims.",
            "\\item Bundled agents are controlled example wrappers, not a broad external-agent leaderboard.",
            "\\item The manual-audit layer still needs independent second-reviewer completion before submission-strength claims.",
            "\\item The task set is strong enough for a workshop pilot, but a top benchmark/dataset venue version should scale to a larger frozen suite with hidden temporal holdouts.",
            "\\end{itemize}",
            "",
            "\\section{Conclusion}",
            (
                "FinDS-AgentBench frames financial data-science agent evaluation as a joint test of "
                "predictive performance, temporal validity, leakage resistance, reproducibility, and "
                "claim discipline. The pilot release provides the first reproducible scaffold for this "
                "evaluation and establishes the artifacts needed for an arXiv/workshop submission."
            ),
            "",
            "\\appendix",
            "\\section{Full Repeated-Run Uncertainty Table}",
            f"\\input{{{summary_uncertainty_table_path}}}",
            "",
            "\\section{Full Pilot Protocol Reference Table}",
            f"\\input{{{protocol_table_path}}}",
            "",
            "\\bibliographystyle{plain}",
            "\\bibliography{references}",
            "",
            "\\end{document}",
            "",
        ]
    )


def render_readme(summary: dict[str, Any], *, formatting_report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Workshop Pilot Manuscript",
            "",
            "Generated manuscript scaffold for the FinDS-AgentBench arXiv/workshop pilot paper.",
            "",
            "## Files",
            "",
            "| File | Purpose |",
            "| --- | --- |",
            "| `main.tex` | Main LaTeX manuscript scaffold with release-artifact inputs. |",
            "| `related_work.tex` | Generated related-work positioning section. |",
            "| `references.bib` | Generated BibTeX scaffold for adjacent benchmark citations. |",
            "| `audit_failure_examples.tex` | Generated qualitative examples from the seed manual-audit subset. |",
            "| `audit_failure_examples.md` | Markdown copy of the generated qualitative examples. |",
            "| `audit_failure_examples.json` | Machine-readable selected qualitative examples. |",
            "| `formatting_check.md` | Static LaTeX readiness and PDF-risk report. |",
            "| `formatting_check.json` | Machine-readable static formatting report. |",
            "| `submission_readiness_checklist.md` | Remaining work before a credible arXiv/workshop submission. |",
            "| `metadata.json` | Machine-readable manuscript summary derived from release artifacts. |",
            "",
            "## Snapshot",
            "",
            "| Field | Value |",
            "| --- | ---: |",
            f"| Tasks | {summary['task_count']} |",
            f"| Runnable Tasks | {summary['runnable_task_count']} |",
            f"| Protocol Tasks | {summary['protocol_task_count']} |",
            f"| Protocol Task-System Cells | {summary['protocol_cell_count']} |",
            f"| Overall Agent Higher Cases | {summary['overall_agent_higher_count']} |",
            f"| Overall Baseline Higher Cases | {summary['overall_baseline_higher_count']} |",
            f"| Overall Tie Cases | {summary['overall_tie_count']} |",
            f"| Reviewer Readiness | {summary['reviewer_readiness_status']} |",
            f"| External Agent Readiness | {summary['external_agent_readiness_status']} |",
            f"| Submission Readiness | {summary['submission_readiness_status']} |",
            f"| Formatting Check | {formatting_report['status']} |",
            "",
            "## Build",
            "",
            "The manuscript is generated from release artifacts:",
            "",
            "```bash",
            "PYTHONPATH=src python scripts/build_pilot_manuscript.py",
            "```",
            "",
            "Check static LaTeX readiness and PDF-risk warnings:",
            "",
            "```bash",
            "PYTHONPATH=src python scripts/check_pilot_manuscript_formatting.py",
            "```",
            "",
            "The generated `main.tex` inputs LaTeX tables from `docs/releases/pilot_v0/` rather than copying them, so table updates remain traceable to the release pipeline.",
            "",
        ]
    )


def render_submission_checklist(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Submission Readiness Checklist",
            "",
            "This checklist tracks work that should be complete before treating the workshop manuscript as submission-ready.",
            "",
            "## Already Present",
            "",
            "- Reproducible pilot release command.",
            "- Task cards, evaluation cards, data manifests, and release manifest.",
            "- Reference result tables and paper-ready result exports.",
            "- Statistical uncertainty and paired-comparison artifacts.",
            "- Seed manual-audit rubric and adjudication workflow.",
            "- Reviewer-readiness report that separates seed-only audit status from submission-strength agreement claims.",
            "- Independent-reviewer handoff and packet validator for second-reviewer audit collection.",
            "- Independent participant brief covering reviewer, external-agent, and optional reader roles.",
            "- External-agent protocol and readiness report that separate bundled reference agents from independent external-agent evidence.",
            "- External-agent handoff, registration template, and registry-evidence validator.",
            "- Unified submission-readiness gate for the workshop manuscript.",
            "- Generated qualitative failure examples with exact task/run/artifact references.",
            "- Audited related-work matrix with corrected venue-neighbor citations and positioning notes.",
            "- Static manuscript formatting checker covering inputs, citations, labels, table structure, and PDF-risk warnings.",
            "- Manuscript table-layout mitigations for related-work, result, uncertainty, and protocol tables.",
            "",
            "## Required Before Submission",
            "",
            "- Fill an independent second-reviewer packet and rebuild agreement/adjudication reports.",
            "- Validate the completed second-reviewer packet before using it for agreement claims.",
            "- Add at least one stronger external agent beyond environment-wrapped baseline selection.",
            "- Validate external-agent registry evidence before using it for external-agent claims.",
            "- Expand qualitative examples after independent second-reviewer adjudication.",
            "- Freeze a release tag and archive the release artifact bundle.",
            "- Install/run a LaTeX engine, compile the final PDF, and inspect table width, appendix length, and venue formatting.",
            "",
            "## Current Risk Flags",
            "",
            f"- Manual audit status: `{summary['manual_audit_status']}`.",
            f"- Reviewer readiness status: `{summary['reviewer_readiness_status']}`.",
            f"- Completed independent reviewer packets: `{summary['independent_completed_reviewer_packet_count']}`.",
            f"- Independent agreement status: `{summary['agreement_status']}`.",
            f"- External-agent readiness status: `{summary['external_agent_readiness_status']}`.",
            f"- Completed external agent configurations: `{summary['completed_external_agent_configuration_count']}`.",
            f"- Submission readiness status: `{summary['submission_readiness_status']}`.",
            (
                f"- Submission gates ready: `{summary['submission_ready_gate_count']} / "
                f"{summary['submission_gate_count']}`."
            ),
            "- Pilot repeated-run count is small; statistical claims must remain caveated.",
            "- Bundled example agents should not be framed as a comprehensive model leaderboard.",
            "",
            "## Manual-Audit Gate Blockers",
            "",
            *(
                f"- {item}"
                for item in (
                    summary["reviewer_readiness_blocking_items"]
                    or ["No reviewer-readiness blockers recorded."]
                )
            ),
            "",
            "## External-Agent Gate Blockers",
            "",
            *(
                f"- {item}"
                for item in (
                    summary["external_agent_blocking_items"]
                    or ["No external-agent readiness blockers recorded."]
                )
            ),
            "",
        ]
    )


def build_pilot_manuscript(
    *,
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    reference_results_path: str | Path = DEFAULT_REFERENCE_RESULTS_PATH,
    manual_audit_subset_path: str | Path = DEFAULT_MANUAL_AUDIT_SUBSET_PATH,
    statistical_comparison_path: str | Path = DEFAULT_STATISTICAL_COMPARISON_PATH,
    statistical_methods_tex_path: str | Path = DEFAULT_STATISTICAL_METHODS_TEX_PATH,
    summary_uncertainty_table_path: str | Path = DEFAULT_SUMMARY_UNCERTAINTY_TABLE_PATH,
    agent_vs_baseline_table_path: str | Path = DEFAULT_AGENT_VS_BASELINE_TABLE_PATH,
    protocol_table_path: str | Path = DEFAULT_PROTOCOL_TABLE_PATH,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> PilotManuscriptBuildResult:
    input_paths = {
        "manifest": Path(manifest_path),
        "reference_results": Path(reference_results_path),
        "manual_audit_subset": Path(manual_audit_subset_path),
        "statistical_comparison": Path(statistical_comparison_path),
        "statistical_methods_tex": Path(statistical_methods_tex_path),
        "summary_uncertainty_table": Path(summary_uncertainty_table_path),
        "agent_vs_baseline_table": Path(agent_vs_baseline_table_path),
        "protocol_table": Path(protocol_table_path),
    }
    require_existing_paths(input_paths)

    manifest = load_json(manifest_path)
    reference_results = load_json(reference_results_path)
    manual_audit_subset = load_json(manual_audit_subset_path)
    statistical_comparison = load_json(statistical_comparison_path)
    summary = summarize_reference_results(
        manifest=manifest,
        reference_results=reference_results,
        statistical_comparison=statistical_comparison,
    )

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    main_tex_path = output_root / "main.tex"
    related_work_tex_path = output_root / "related_work.tex"
    references_bib_path = output_root / "references.bib"
    audit_failure_examples_tex_path = output_root / "audit_failure_examples.tex"
    audit_failure_examples_markdown_path = output_root / "audit_failure_examples.md"
    audit_failure_examples_json_path = output_root / "audit_failure_examples.json"
    formatting_check_json_path = output_root / "formatting_check.json"
    formatting_check_markdown_path = output_root / "formatting_check.md"
    readme_path = output_root / "README.md"
    checklist_path = output_root / "submission_readiness_checklist.md"
    metadata_path = output_root / "metadata.json"

    related_work_tex_path.write_text(render_related_work_tex(), encoding="utf-8")
    references_bib_path.write_text(render_bibtex(), encoding="utf-8")
    audit_examples = select_audit_failure_examples(manual_audit_subset)
    audit_failure_examples_tex_path.write_text(
        render_audit_failure_examples_tex(audit_examples),
        encoding="utf-8",
    )
    audit_failure_examples_markdown_path.write_text(
        render_audit_failure_examples_markdown(audit_examples),
        encoding="utf-8",
    )
    audit_failure_examples_json_path.write_text(
        json.dumps({"examples": audit_examples}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    main_tex_path.write_text(
        render_main_tex(
            summary=summary,
            related_work_tex_path=relative_latex_path(related_work_tex_path, output_dir=output_root),
            audit_failure_examples_tex_path=relative_latex_path(
                audit_failure_examples_tex_path,
                output_dir=output_root,
            ),
            statistical_methods_tex_path=relative_latex_path(
                statistical_methods_tex_path,
                output_dir=output_root,
            ),
            summary_uncertainty_table_path=relative_latex_path(
                summary_uncertainty_table_path,
                output_dir=output_root,
            ),
            agent_vs_baseline_table_path=relative_latex_path(
                agent_vs_baseline_table_path,
                output_dir=output_root,
            ),
            protocol_table_path=relative_latex_path(protocol_table_path, output_dir=output_root),
        ),
        encoding="utf-8",
    )
    formatting_result = write_manuscript_formatting_artifacts(
        main_tex_path=main_tex_path,
        output_json_path=formatting_check_json_path,
        output_markdown_path=formatting_check_markdown_path,
    )
    readme_path.write_text(render_readme(summary, formatting_report=formatting_result.report), encoding="utf-8")
    checklist_path.write_text(render_submission_checklist(summary), encoding="utf-8")
    metadata_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return PilotManuscriptBuildResult(
        output_dir=output_root,
        main_tex_path=main_tex_path,
        related_work_tex_path=related_work_tex_path,
        references_bib_path=references_bib_path,
        audit_failure_examples_tex_path=audit_failure_examples_tex_path,
        audit_failure_examples_markdown_path=audit_failure_examples_markdown_path,
        audit_failure_examples_json_path=audit_failure_examples_json_path,
        formatting_check_json_path=formatting_check_json_path,
        formatting_check_markdown_path=formatting_check_markdown_path,
        readme_path=readme_path,
        checklist_path=checklist_path,
        metadata_path=metadata_path,
    )
