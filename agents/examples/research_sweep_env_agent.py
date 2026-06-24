#!/usr/bin/env python
from __future__ import annotations

import os
from pathlib import Path

from finds_agentbench.research_agent import run_research_sweep_agent


def main() -> int:
    if "FINDS_ANSWER_KEY_PATH" in os.environ:
        raise RuntimeError("Private answer-key paths must not be exposed to agents.")

    metadata = run_research_sweep_agent(
        task_id=os.environ["FINDS_TASK_ID"],
        seed=int(os.environ["FINDS_RUN_SEED"]),
        train_public_path=Path(os.environ["FINDS_TRAIN_PUBLIC_PATH"]),
        holdout_features_path=Path(os.environ["FINDS_HOLDOUT_FEATURES_PATH"]),
        submission_dir=Path(os.environ["FINDS_SUBMISSION_DIR"]),
    )
    print(
        "selected "
        f"{metadata['selected_candidate_id']} "
        f"(public_validation_balanced_accuracy="
        f"{metadata['selected_public_validation_balanced_accuracy']:.6f})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
