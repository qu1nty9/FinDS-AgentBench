from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from finds_agentbench.artifacts import validate_submission_artifacts
from finds_agentbench.baselines import write_momentum_submission_artifacts
from finds_agentbench.io import load_yaml
from finds_agentbench.reports import load_result_rows, write_results_csv, write_results_markdown
from finds_agentbench.runs import build_run_manifest, utc_now, write_run_manifest
from finds_agentbench.scoring import score_synthetic_market_submission
from finds_agentbench.synthetic import write_synthetic_market_direction_task


@dataclass(frozen=True)
class PipelineResult:
    run_dir: Path
    score_path: Path
    validation_path: Path
    manifest_path: Path
    report_csv_path: Path
    report_markdown_path: Path
    status: str


def write_json(path: Path, value: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def run_synthetic_market_momentum_pipeline(
    *,
    seed: int = 11,
    task_path: str | Path = "tasks/pilot/synthetic_market_direction_v0.yaml",
    data_output_dir: str | Path = "data/raw/synthetic_market_direction_v0",
    private_dir: str | Path = "data/private/synthetic_market_direction_v0",
    run_dir: str | Path = "runs/synthetic_market_direction_v0/momentum_baseline",
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    execute_notebook: bool = False,
    command: str = "run_synthetic_market_momentum_pipeline",
) -> PipelineResult:
    data_paths = write_synthetic_market_direction_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        seed=seed,
    )
    run_path = Path(run_dir)
    write_momentum_submission_artifacts(data_paths.private_holdout_features, run_path)

    score = score_synthetic_market_submission(
        submission_path=run_path / "predictions.csv",
        answer_key_path=data_paths.answer_key,
    )
    score_dict = score.as_dict()
    score_path = write_json(run_path / "score.json", score_dict)

    task_spec = load_yaml(task_path)
    validation = validate_submission_artifacts(
        task_spec=task_spec,
        submission_dir=run_path,
        execute=execute_notebook,
        scan_leakage=True,
    )
    validation_dict = validation.as_dict()
    validation_path = write_json(run_path / "artifact_validation.json", validation_dict)

    failures = list(score.failures)
    failures.extend(validation.errors)
    if not score.execution_success:
        status = "failed_format"
    elif not validation.ok:
        status = "failed_validity_gate"
    else:
        status = "completed"

    command_started_at = utc_now()
    command_completed_at = utc_now()
    manifest = build_run_manifest(
        task_id="synthetic_market_direction_v0",
        agent_id="momentum_baseline",
        agent_version="0.1.0",
        submission_dir=run_path,
        run_type="baseline",
        status=status,
        tool_permissions=["filesystem:read", "filesystem:write"],
        commands=[
            {
                "command": command,
                "started_at": command_started_at,
                "completed_at": command_completed_at,
                "exit_code": 0 if status == "completed" else 1,
            }
        ],
        validations={"artifact_validation": validation_dict},
        scores=score_dict,
        failures=failures,
        trace={"seed": seed},
    )
    manifest_path = write_run_manifest(manifest, run_path / "run_manifest.json")

    rows = load_result_rows(run_path.parent.parent)
    csv_path = write_results_csv(rows, report_csv_path)
    markdown_path = write_results_markdown(rows, report_markdown_path)

    return PipelineResult(
        run_dir=run_path,
        score_path=score_path,
        validation_path=validation_path,
        manifest_path=manifest_path,
        report_csv_path=csv_path,
        report_markdown_path=markdown_path,
        status=status,
    )
