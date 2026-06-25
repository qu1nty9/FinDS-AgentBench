#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from finds_agentbench.manuscript_formatting import (
    DEFAULT_FORMATTING_CHECK_JSON_PATH,
    DEFAULT_FORMATTING_CHECK_MARKDOWN_PATH,
    DEFAULT_MAIN_TEX_PATH,
    write_manuscript_formatting_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check static LaTeX readiness for the workshop manuscript scaffold."
    )
    parser.add_argument("--main-tex", type=Path, default=DEFAULT_MAIN_TEX_PATH)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_FORMATTING_CHECK_JSON_PATH)
    parser.add_argument(
        "--output-markdown",
        type=Path,
        default=DEFAULT_FORMATTING_CHECK_MARKDOWN_PATH,
    )
    parser.add_argument(
        "--require-latex-engine",
        action="store_true",
        help="Return non-zero when no local LaTeX engine is available.",
    )
    args = parser.parse_args()

    result = write_manuscript_formatting_artifacts(
        main_tex_path=args.main_tex,
        output_json_path=args.output_json,
        output_markdown_path=args.output_markdown,
    )
    print(f"formatting_check_json: {result.json_path}")
    print(f"formatting_check_markdown: {result.markdown_path}")
    print(f"formatting_status: {result.report['status']}")
    print(f"hard_error_count: {result.report['hard_error_count']}")
    print(f"warning_count: {result.report['warning_count']}")
    if result.report["hard_error_count"] > 0:
        return 1
    if args.require_latex_engine and not result.report["latex_engine"]["available"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
