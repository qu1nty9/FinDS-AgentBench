#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from finds_agentbench.task_cards import build_task_cards


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build task cards, evaluation cards, and a registry from benchmark YAML specs."
    )
    parser.add_argument("--tasks-root", type=Path, default=Path("tasks/pilot"))
    parser.add_argument("--output-root", type=Path, default=Path("docs/cards"))
    args = parser.parse_args()

    result = build_task_cards(
        tasks_root=args.tasks_root,
        output_root=args.output_root,
    )

    print(f"task_specs: {len(result.task_specs)}")
    print(f"task_cards: {len(result.task_card_paths)}")
    print(f"evaluation_cards: {len(result.evaluation_card_paths)}")
    print(f"registry_json: {result.registry_json_path}")
    print(f"registry_csv: {result.registry_csv_path}")
    print(f"index: {result.index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
