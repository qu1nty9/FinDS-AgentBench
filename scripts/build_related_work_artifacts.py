#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from finds_agentbench.related_work import build_related_work_artifacts


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build related-work matrix, manuscript section, and BibTeX scaffold."
    )
    parser.add_argument("--markdown", type=Path, default=Path("docs/related_work_matrix.md"))
    parser.add_argument("--tex", type=Path, default=Path("papers/workshop_pilot/related_work.tex"))
    parser.add_argument("--bib", type=Path, default=Path("papers/workshop_pilot/references.bib"))
    args = parser.parse_args()

    written = build_related_work_artifacts(
        markdown_path=args.markdown,
        tex_path=args.tex,
        bib_path=args.bib,
    )
    for key, path in sorted(written.items()):
        print(f"{key}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
