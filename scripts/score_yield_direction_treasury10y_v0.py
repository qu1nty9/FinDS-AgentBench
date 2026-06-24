#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from finds_agentbench.scoring import score_yield_direction_treasury10y_submission


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Score yield_direction_treasury10y_v0 predictions."
    )
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument(
        "--answer-key",
        type=Path,
        default=Path("data/private/yield_direction_treasury10y_v0/answer_key.csv"),
    )
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args()

    score = score_yield_direction_treasury10y_submission(
        submission_path=args.submission,
        answer_key_path=args.answer_key,
    )
    output = json.dumps(score.as_dict(), indent=2)
    print(output)
    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(output + "\n", encoding="utf-8")
    return 0 if score.execution_success else 1


if __name__ == "__main__":
    raise SystemExit(main())
