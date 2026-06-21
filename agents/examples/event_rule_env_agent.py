#!/usr/bin/env python
from __future__ import annotations

import os
from pathlib import Path

from finds_agentbench.baselines import write_event_rule_submission_artifacts


def main() -> int:
    if "FINDS_ANSWER_KEY_PATH" in os.environ:
        raise RuntimeError("Private answer-key paths must not be exposed to agents.")

    features_path = Path(os.environ["FINDS_HOLDOUT_FEATURES_PATH"])
    submission_dir = Path(os.environ["FINDS_SUBMISSION_DIR"])
    write_event_rule_submission_artifacts(features_path, submission_dir)
    print(f"wrote event-rule env-agent artifacts: {submission_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
