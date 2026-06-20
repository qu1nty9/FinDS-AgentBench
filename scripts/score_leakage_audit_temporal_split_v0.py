#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from finds_agentbench.scoring import score_leakage_audit_submission


def main() -> int:
    parser = argparse.ArgumentParser(description="Score leakage_audit_temporal_split_v0.")
    parser.add_argument("--submission-dir", type=Path, required=True)
    parser.add_argument(
        "--answer-key",
        type=Path,
        default=Path("data/private/leakage_audit_temporal_split_v0/answer_key.json"),
    )
    args = parser.parse_args()

    score = score_leakage_audit_submission(
        submission_dir=args.submission_dir,
        answer_key_path=args.answer_key,
    )
    print(json.dumps(score.as_dict(), indent=2))
    return 0 if score.execution_success else 1


if __name__ == "__main__":
    raise SystemExit(main())

