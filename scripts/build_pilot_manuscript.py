#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from finds_agentbench.pilot_manuscript import (
    DEFAULT_AGENT_VS_BASELINE_TABLE_PATH,
    DEFAULT_MANIFEST_PATH,
    DEFAULT_MANUAL_AUDIT_SUBSET_PATH,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PROTOCOL_TABLE_PATH,
    DEFAULT_REFERENCE_RESULTS_PATH,
    DEFAULT_STATISTICAL_COMPARISON_PATH,
    DEFAULT_STATISTICAL_METHODS_TEX_PATH,
    DEFAULT_SUMMARY_UNCERTAINTY_TABLE_PATH,
    build_pilot_manuscript,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the FinDS-AgentBench arXiv/workshop pilot manuscript scaffold."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--reference-results", type=Path, default=DEFAULT_REFERENCE_RESULTS_PATH)
    parser.add_argument("--manual-audit-subset", type=Path, default=DEFAULT_MANUAL_AUDIT_SUBSET_PATH)
    parser.add_argument(
        "--statistical-comparison",
        type=Path,
        default=DEFAULT_STATISTICAL_COMPARISON_PATH,
    )
    parser.add_argument(
        "--statistical-methods-tex",
        type=Path,
        default=DEFAULT_STATISTICAL_METHODS_TEX_PATH,
    )
    parser.add_argument(
        "--summary-uncertainty-table",
        type=Path,
        default=DEFAULT_SUMMARY_UNCERTAINTY_TABLE_PATH,
    )
    parser.add_argument(
        "--agent-vs-baseline-table",
        type=Path,
        default=DEFAULT_AGENT_VS_BASELINE_TABLE_PATH,
    )
    parser.add_argument("--protocol-table", type=Path, default=DEFAULT_PROTOCOL_TABLE_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    result = build_pilot_manuscript(
        manifest_path=args.manifest,
        reference_results_path=args.reference_results,
        manual_audit_subset_path=args.manual_audit_subset,
        statistical_comparison_path=args.statistical_comparison,
        statistical_methods_tex_path=args.statistical_methods_tex,
        summary_uncertainty_table_path=args.summary_uncertainty_table,
        agent_vs_baseline_table_path=args.agent_vs_baseline_table,
        protocol_table_path=args.protocol_table,
        output_dir=args.output_dir,
    )
    print(f"main_tex: {result.main_tex_path}")
    print(f"related_work_tex: {result.related_work_tex_path}")
    print(f"references_bib: {result.references_bib_path}")
    print(f"audit_failure_examples_tex: {result.audit_failure_examples_tex_path}")
    print(f"audit_failure_examples_markdown: {result.audit_failure_examples_markdown_path}")
    print(f"audit_failure_examples_json: {result.audit_failure_examples_json_path}")
    print(f"readme: {result.readme_path}")
    print(f"checklist: {result.checklist_path}")
    print(f"metadata: {result.metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
