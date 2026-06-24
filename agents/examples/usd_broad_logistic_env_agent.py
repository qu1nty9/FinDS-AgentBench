#!/usr/bin/env python
from __future__ import annotations

import os
from pathlib import Path

from finds_agentbench.usd_broad import write_usd_broad_logistic_submission_artifacts


def main() -> int:
    if "FINDS_ANSWER_KEY_PATH" in os.environ:
        raise RuntimeError("Private answer-key paths must not be exposed to agents.")

    train_public_path = Path(os.environ["FINDS_TRAIN_PUBLIC_PATH"])
    holdout_features_path = Path(os.environ["FINDS_HOLDOUT_FEATURES_PATH"])
    submission_dir = Path(os.environ["FINDS_SUBMISSION_DIR"])
    write_usd_broad_logistic_submission_artifacts(
        train_public_path=train_public_path,
        holdout_features_path=holdout_features_path,
        output_dir=submission_dir,
    )
    print(f"wrote usd broad logistic env-agent artifacts: {submission_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
