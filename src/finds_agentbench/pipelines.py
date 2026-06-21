from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from finds_agentbench.agent_runner import run_agent_command
from finds_agentbench.artifacts import validate_submission_artifacts
from finds_agentbench.baselines import (
    write_event_rule_submission_artifacts,
    write_logistic_submission_artifacts,
    write_momentum_submission_artifacts,
)
from finds_agentbench.io import load_yaml
from finds_agentbench.reports import (
    aggregate_result_rows,
    load_result_rows,
    write_results_csv,
    write_results_markdown,
    write_summary_csv,
    write_summary_markdown,
)
from finds_agentbench.runs import build_run_manifest, slugify, utc_now, write_run_manifest
from finds_agentbench.scoring import (
    score_synthetic_event_response_submission,
    score_synthetic_market_submission,
)
from finds_agentbench.synthetic import (
    SyntheticEventPaths,
    SyntheticMarketPaths,
    write_synthetic_event_response_task,
    write_synthetic_market_direction_task,
)

SYNTHETIC_MARKET_TASK_ID = "synthetic_market_direction_v0"
SYNTHETIC_EVENT_TASK_ID = "synthetic_event_response_v0"
MOMENTUM_BASELINE_ID = "momentum_baseline"
LOGISTIC_BASELINE_ID = "logistic_regression_baseline"
EVENT_RULE_BASELINE_ID = "event_rule_baseline"
DEFAULT_SYNTHETIC_MARKET_BASELINES = (MOMENTUM_BASELINE_ID, LOGISTIC_BASELINE_ID)
DEFAULT_SYNTHETIC_MARKET_SUITE_RUNS_ROOT = "runs/suites/synthetic_market_direction_v0_pilot"
DEFAULT_SYNTHETIC_MARKET_AGENT_SUITE_RUNS_ROOT = "runs/suites/synthetic_market_direction_v0_agents"
DEFAULT_SYNTHETIC_EVENT_AGENT_SUITE_RUNS_ROOT = "runs/suites/synthetic_event_response_v0_agents"


@dataclass(frozen=True)
class PipelineResult:
    run_dir: Path
    score_path: Path
    validation_path: Path
    manifest_path: Path
    report_csv_path: Path
    report_markdown_path: Path
    summary_csv_path: Path
    summary_markdown_path: Path
    status: str


@dataclass(frozen=True)
class BaselineSuiteResult:
    results: list[PipelineResult]

    @property
    def status(self) -> str:
        if all(result.status == "completed" for result in self.results):
            return "completed"
        return "failed"

    @property
    def report_csv_path(self) -> Path | None:
        return self.results[-1].report_csv_path if self.results else None

    @property
    def report_markdown_path(self) -> Path | None:
        return self.results[-1].report_markdown_path if self.results else None

    @property
    def summary_csv_path(self) -> Path | None:
        return self.results[-1].summary_csv_path if self.results else None

    @property
    def summary_markdown_path(self) -> Path | None:
        return self.results[-1].summary_markdown_path if self.results else None


@dataclass(frozen=True)
class AgentSuiteResult:
    results: list[PipelineResult]

    @property
    def status(self) -> str:
        if all(result.status == "completed" for result in self.results):
            return "completed"
        return "failed"

    @property
    def report_csv_path(self) -> Path | None:
        return self.results[-1].report_csv_path if self.results else None

    @property
    def report_markdown_path(self) -> Path | None:
        return self.results[-1].report_markdown_path if self.results else None

    @property
    def summary_csv_path(self) -> Path | None:
        return self.results[-1].summary_csv_path if self.results else None

    @property
    def summary_markdown_path(self) -> Path | None:
        return self.results[-1].summary_markdown_path if self.results else None


def predictive_task_agent_env(
    *,
    task_id: str,
    seed: int,
    task_path: str | Path,
    data_paths: SyntheticMarketPaths | SyntheticEventPaths,
    submission_dir: str | Path,
) -> dict[str, str]:
    return {
        "FINDS_TASK_ID": task_id,
        "FINDS_RUN_SEED": str(seed),
        "FINDS_TASK_SPEC_PATH": str(Path(task_path)),
        "FINDS_PUBLIC_DATA_DIR": str(data_paths.train_public.parent),
        "FINDS_TRAIN_PUBLIC_PATH": str(data_paths.train_public),
        "FINDS_HOLDOUT_FEATURES_PATH": str(data_paths.private_holdout_features),
        "FINDS_PRIVATE_HOLDOUT_FEATURES_PATH": str(data_paths.private_holdout_features),
        "FINDS_SAMPLE_SUBMISSION_PATH": str(data_paths.sample_submission),
        "FINDS_METADATA_PATH": str(data_paths.metadata),
        "FINDS_SUBMISSION_DIR": str(Path(submission_dir)),
    }


def synthetic_market_agent_env(
    *,
    seed: int,
    task_path: str | Path,
    data_paths: SyntheticMarketPaths,
    submission_dir: str | Path,
) -> dict[str, str]:
    return predictive_task_agent_env(
        task_id=SYNTHETIC_MARKET_TASK_ID,
        seed=seed,
        task_path=task_path,
        data_paths=data_paths,
        submission_dir=submission_dir,
    )


def synthetic_event_agent_env(
    *,
    seed: int,
    task_path: str | Path,
    data_paths: SyntheticEventPaths,
    submission_dir: str | Path,
) -> dict[str, str]:
    return predictive_task_agent_env(
        task_id=SYNTHETIC_EVENT_TASK_ID,
        seed=seed,
        task_path=task_path,
        data_paths=data_paths,
        submission_dir=submission_dir,
    )


def write_json(path: Path, value: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def resolve_run_path(run_dir: str | Path, run_label: str | None = None) -> Path:
    base_path = Path(run_dir)
    if run_label is None:
        return base_path
    return base_path / slugify(run_label)


def infer_runs_root(run_path: Path) -> Path:
    if "runs" in run_path.parts:
        index = len(run_path.parts) - 1 - list(reversed(run_path.parts)).index("runs")
        return Path(*run_path.parts[: index + 1])
    if len(run_path.parents) >= 2:
        return run_path.parent.parent
    return run_path.parent


def build_trace(
    *,
    seed: int,
    run_label: str | None,
    repeat_index: int | None,
    repeat_count: int | None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    trace: dict[str, Any] = {"seed": seed}
    if run_label is not None:
        trace["run_label"] = run_label
        trace["run_label_slug"] = slugify(run_label)
    if repeat_index is not None:
        trace["repeat_index"] = repeat_index
    if repeat_count is not None:
        trace["repeat_count"] = repeat_count
    if extra:
        trace.update(extra)
    return trace


def write_benchmark_reports(
    *,
    runs_root: str | Path,
    report_csv_path: str | Path,
    report_markdown_path: str | Path,
    summary_csv_path: str | Path,
    summary_markdown_path: str | Path,
) -> tuple[Path, Path, Path, Path]:
    rows = load_result_rows(runs_root)
    csv_path = write_results_csv(rows, report_csv_path)
    markdown_path = write_results_markdown(rows, report_markdown_path)
    summary_rows = aggregate_result_rows(rows)
    summary_csv = write_summary_csv(summary_rows, summary_csv_path)
    summary_markdown = write_summary_markdown(summary_rows, summary_markdown_path)
    return csv_path, markdown_path, summary_csv, summary_markdown


def run_synthetic_market_momentum_pipeline(
    *,
    seed: int = 11,
    task_path: str | Path = "tasks/pilot/synthetic_market_direction_v0.yaml",
    data_output_dir: str | Path = "data/raw/synthetic_market_direction_v0",
    private_dir: str | Path = "data/private/synthetic_market_direction_v0",
    run_dir: str | Path = "runs/synthetic_market_direction_v0/momentum_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_synthetic_market_momentum_pipeline",
) -> PipelineResult:
    data_paths = write_synthetic_market_direction_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        seed=seed,
    )
    run_path = resolve_run_path(run_dir, run_label)
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
        scan_methodology=True,
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
        task_id=SYNTHETIC_MARKET_TASK_ID,
        agent_id=MOMENTUM_BASELINE_ID,
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
        trace=build_trace(
            seed=seed,
            run_label=run_label,
            repeat_index=repeat_index,
            repeat_count=repeat_count,
        ),
    )
    manifest_path = write_run_manifest(manifest, run_path / "run_manifest.json")

    report_root = Path(runs_root) if runs_root is not None else infer_runs_root(run_path)
    csv_path, markdown_path, summary_csv, summary_markdown = write_benchmark_reports(
        runs_root=report_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
    )

    return PipelineResult(
        run_dir=run_path,
        score_path=score_path,
        validation_path=validation_path,
        manifest_path=manifest_path,
        report_csv_path=csv_path,
        report_markdown_path=markdown_path,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_markdown,
        status=status,
    )


def run_synthetic_market_logistic_pipeline(
    *,
    seed: int = 11,
    task_path: str | Path = "tasks/pilot/synthetic_market_direction_v0.yaml",
    data_output_dir: str | Path = "data/raw/synthetic_market_direction_v0",
    private_dir: str | Path = "data/private/synthetic_market_direction_v0",
    run_dir: str | Path = "runs/synthetic_market_direction_v0/logistic_regression_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_synthetic_market_logistic_pipeline",
) -> PipelineResult:
    data_paths = write_synthetic_market_direction_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        seed=seed,
    )
    run_path = resolve_run_path(run_dir, run_label)
    baseline_metadata = write_logistic_submission_artifacts(
        train_public_path=data_paths.train_public,
        holdout_features_path=data_paths.private_holdout_features,
        output_dir=run_path,
        random_state=seed,
    )

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
        scan_methodology=True,
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
        task_id=SYNTHETIC_MARKET_TASK_ID,
        agent_id=LOGISTIC_BASELINE_ID,
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
        trace=build_trace(
            seed=seed,
            run_label=run_label,
            repeat_index=repeat_index,
            repeat_count=repeat_count,
            extra={"baseline_metadata": baseline_metadata},
        ),
    )
    manifest_path = write_run_manifest(manifest, run_path / "run_manifest.json")

    report_root = Path(runs_root) if runs_root is not None else infer_runs_root(run_path)
    csv_path, markdown_path, summary_csv, summary_markdown = write_benchmark_reports(
        runs_root=report_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
    )

    return PipelineResult(
        run_dir=run_path,
        score_path=score_path,
        validation_path=validation_path,
        manifest_path=manifest_path,
        report_csv_path=csv_path,
        report_markdown_path=markdown_path,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_markdown,
        status=status,
    )


def run_synthetic_event_response_rule_pipeline(
    *,
    seed: int = 23,
    task_path: str | Path = "tasks/pilot/synthetic_event_response_v0.yaml",
    data_output_dir: str | Path = "data/raw/synthetic_event_response_v0",
    private_dir: str | Path = "data/private/synthetic_event_response_v0",
    run_dir: str | Path = "runs/synthetic_event_response_v0/event_rule_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_synthetic_event_response_rule_pipeline",
) -> PipelineResult:
    data_paths = write_synthetic_event_response_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        seed=seed,
    )
    run_path = resolve_run_path(run_dir, run_label)
    write_event_rule_submission_artifacts(data_paths.private_holdout_features, run_path)

    score = score_synthetic_event_response_submission(
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
        scan_methodology=True,
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
        task_id=SYNTHETIC_EVENT_TASK_ID,
        agent_id=EVENT_RULE_BASELINE_ID,
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
        trace=build_trace(
            seed=seed,
            run_label=run_label,
            repeat_index=repeat_index,
            repeat_count=repeat_count,
        ),
    )
    manifest_path = write_run_manifest(manifest, run_path / "run_manifest.json")

    report_root = Path(runs_root) if runs_root is not None else infer_runs_root(run_path)
    csv_path, markdown_path, summary_csv, summary_markdown = write_benchmark_reports(
        runs_root=report_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
    )

    return PipelineResult(
        run_dir=run_path,
        score_path=score_path,
        validation_path=validation_path,
        manifest_path=manifest_path,
        report_csv_path=csv_path,
        report_markdown_path=markdown_path,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_markdown,
        status=status,
    )


def run_synthetic_market_agent_command(
    *,
    agent_id: str,
    agent_version: str,
    agent_command: str | list[str] | tuple[str, ...],
    seed: int = 11,
    task_path: str | Path = "tasks/pilot/synthetic_market_direction_v0.yaml",
    data_output_dir: str | Path = "data/raw/synthetic_market_direction_v0",
    private_dir: str | Path = "data/private/synthetic_market_direction_v0",
    run_dir: str | Path | None = None,
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command_timeout_seconds: int = 1800,
    cwd: str | Path | None = None,
) -> PipelineResult:
    data_paths = write_synthetic_market_direction_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        seed=seed,
    )
    base_run_dir = run_dir or Path("runs") / SYNTHETIC_MARKET_TASK_ID / agent_id
    run_path = resolve_run_path(base_run_dir, run_label)
    run_path.mkdir(parents=True, exist_ok=True)

    command_result = run_agent_command(
        command=agent_command,
        env=synthetic_market_agent_env(
            seed=seed,
            task_path=task_path,
            data_paths=data_paths,
            submission_dir=run_path,
        ),
        cwd=cwd,
        log_dir=run_path / "logs",
        timeout_seconds=command_timeout_seconds,
    )

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
        scan_methodology=True,
    )
    validation_dict = validation.as_dict()
    validation_path = write_json(run_path / "artifact_validation.json", validation_dict)

    failures = list(score.failures)
    failures.extend(validation.errors)
    if command_result.timed_out:
        failures.append("agent_command_timed_out")
        status = "timed_out"
    elif command_result.exit_code != 0:
        failures.append(f"agent_command_exit_code={command_result.exit_code}")
        status = "failed_runtime"
    elif not score.execution_success:
        status = "failed_format"
    elif not validation.ok:
        status = "failed_validity_gate"
    else:
        status = "completed"

    manifest = build_run_manifest(
        task_id=SYNTHETIC_MARKET_TASK_ID,
        agent_id=agent_id,
        agent_version=agent_version,
        submission_dir=run_path,
        run_type="agent",
        status=status,
        started_at=command_result.started_at,
        completed_at=command_result.completed_at,
        tool_permissions=["filesystem:read_public_data", "filesystem:write_submission"],
        commands=[command_result.as_manifest_command()],
        validations={"artifact_validation": validation_dict},
        scores=score_dict,
        failures=failures,
        trace=build_trace(
            seed=seed,
            run_label=run_label,
            repeat_index=repeat_index,
            repeat_count=repeat_count,
            extra={
                "command_timeout_seconds": command_timeout_seconds,
                "public_data_dir": str(data_paths.train_public.parent),
            },
        ),
    )
    manifest_path = write_run_manifest(manifest, run_path / "run_manifest.json")

    report_root = Path(runs_root) if runs_root is not None else infer_runs_root(run_path)
    csv_path, markdown_path, summary_csv, summary_markdown = write_benchmark_reports(
        runs_root=report_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
    )

    return PipelineResult(
        run_dir=run_path,
        score_path=score_path,
        validation_path=validation_path,
        manifest_path=manifest_path,
        report_csv_path=csv_path,
        report_markdown_path=markdown_path,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_markdown,
        status=status,
    )


def run_synthetic_market_agent_command_suite(
    *,
    agent_id: str,
    agent_version: str,
    agent_command: str | list[str] | tuple[str, ...],
    seed: int = 11,
    repeat: int = 3,
    run_label_prefix: str = "agent",
    task_path: str | Path = "tasks/pilot/synthetic_market_direction_v0.yaml",
    data_output_dir: str | Path = "data/raw/synthetic_market_direction_v0",
    private_dir: str | Path = "data/private/synthetic_market_direction_v0",
    runs_root: str | Path = DEFAULT_SYNTHETIC_MARKET_AGENT_SUITE_RUNS_ROOT,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command_timeout_seconds: int = 1800,
    cwd: str | Path | None = None,
) -> AgentSuiteResult:
    if repeat < 1:
        raise ValueError("repeat must be at least 1")

    root = Path(runs_root)
    task_run_root = root / SYNTHETIC_MARKET_TASK_ID
    results: list[PipelineResult] = []
    for repeat_offset in range(repeat):
        current_seed = seed + repeat_offset
        run_label = f"{run_label_prefix}_{repeat_offset + 1:03d}_seed_{current_seed}"
        results.append(
            run_synthetic_market_agent_command(
                agent_id=agent_id,
                agent_version=agent_version,
                agent_command=agent_command,
                seed=current_seed,
                task_path=task_path,
                data_output_dir=Path(data_output_dir) / run_label,
                private_dir=Path(private_dir) / run_label,
                run_dir=task_run_root / agent_id,
                run_label=run_label,
                repeat_index=repeat_offset + 1,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command_timeout_seconds=command_timeout_seconds,
                cwd=cwd,
            )
        )

    return AgentSuiteResult(results=results)


def run_synthetic_event_response_agent_command(
    *,
    agent_id: str,
    agent_version: str,
    agent_command: str | list[str] | tuple[str, ...],
    seed: int = 23,
    task_path: str | Path = "tasks/pilot/synthetic_event_response_v0.yaml",
    data_output_dir: str | Path = "data/raw/synthetic_event_response_v0",
    private_dir: str | Path = "data/private/synthetic_event_response_v0",
    run_dir: str | Path | None = None,
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command_timeout_seconds: int = 1800,
    cwd: str | Path | None = None,
) -> PipelineResult:
    data_paths = write_synthetic_event_response_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        seed=seed,
    )
    base_run_dir = run_dir or Path("runs") / SYNTHETIC_EVENT_TASK_ID / agent_id
    run_path = resolve_run_path(base_run_dir, run_label)
    run_path.mkdir(parents=True, exist_ok=True)

    command_result = run_agent_command(
        command=agent_command,
        env=synthetic_event_agent_env(
            seed=seed,
            task_path=task_path,
            data_paths=data_paths,
            submission_dir=run_path,
        ),
        cwd=cwd,
        log_dir=run_path / "logs",
        timeout_seconds=command_timeout_seconds,
    )

    score = score_synthetic_event_response_submission(
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
        scan_methodology=True,
    )
    validation_dict = validation.as_dict()
    validation_path = write_json(run_path / "artifact_validation.json", validation_dict)

    failures = list(score.failures)
    failures.extend(validation.errors)
    if command_result.timed_out:
        failures.append("agent_command_timed_out")
        status = "timed_out"
    elif command_result.exit_code != 0:
        failures.append(f"agent_command_exit_code={command_result.exit_code}")
        status = "failed_runtime"
    elif not score.execution_success:
        status = "failed_format"
    elif not validation.ok:
        status = "failed_validity_gate"
    else:
        status = "completed"

    manifest = build_run_manifest(
        task_id=SYNTHETIC_EVENT_TASK_ID,
        agent_id=agent_id,
        agent_version=agent_version,
        submission_dir=run_path,
        run_type="agent",
        status=status,
        started_at=command_result.started_at,
        completed_at=command_result.completed_at,
        tool_permissions=["filesystem:read_public_data", "filesystem:write_submission"],
        commands=[command_result.as_manifest_command()],
        validations={"artifact_validation": validation_dict},
        scores=score_dict,
        failures=failures,
        trace=build_trace(
            seed=seed,
            run_label=run_label,
            repeat_index=repeat_index,
            repeat_count=repeat_count,
            extra={
                "command_timeout_seconds": command_timeout_seconds,
                "public_data_dir": str(data_paths.train_public.parent),
            },
        ),
    )
    manifest_path = write_run_manifest(manifest, run_path / "run_manifest.json")

    report_root = Path(runs_root) if runs_root is not None else infer_runs_root(run_path)
    csv_path, markdown_path, summary_csv, summary_markdown = write_benchmark_reports(
        runs_root=report_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
    )

    return PipelineResult(
        run_dir=run_path,
        score_path=score_path,
        validation_path=validation_path,
        manifest_path=manifest_path,
        report_csv_path=csv_path,
        report_markdown_path=markdown_path,
        summary_csv_path=summary_csv,
        summary_markdown_path=summary_markdown,
        status=status,
    )


def run_synthetic_event_response_agent_command_suite(
    *,
    agent_id: str,
    agent_version: str,
    agent_command: str | list[str] | tuple[str, ...],
    seed: int = 23,
    repeat: int = 3,
    run_label_prefix: str = "agent",
    task_path: str | Path = "tasks/pilot/synthetic_event_response_v0.yaml",
    data_output_dir: str | Path = "data/raw/synthetic_event_response_v0",
    private_dir: str | Path = "data/private/synthetic_event_response_v0",
    runs_root: str | Path = DEFAULT_SYNTHETIC_EVENT_AGENT_SUITE_RUNS_ROOT,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command_timeout_seconds: int = 1800,
    cwd: str | Path | None = None,
) -> AgentSuiteResult:
    if repeat < 1:
        raise ValueError("repeat must be at least 1")

    root = Path(runs_root)
    task_run_root = root / SYNTHETIC_EVENT_TASK_ID
    results: list[PipelineResult] = []
    for repeat_offset in range(repeat):
        current_seed = seed + repeat_offset
        run_label = f"{run_label_prefix}_{repeat_offset + 1:03d}_seed_{current_seed}"
        results.append(
            run_synthetic_event_response_agent_command(
                agent_id=agent_id,
                agent_version=agent_version,
                agent_command=agent_command,
                seed=current_seed,
                task_path=task_path,
                data_output_dir=Path(data_output_dir) / run_label,
                private_dir=Path(private_dir) / run_label,
                run_dir=task_run_root / agent_id,
                run_label=run_label,
                repeat_index=repeat_offset + 1,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command_timeout_seconds=command_timeout_seconds,
                cwd=cwd,
            )
        )

    return AgentSuiteResult(results=results)


def run_synthetic_market_baseline_suite(
    *,
    seed: int = 11,
    repeat: int = 3,
    baselines: list[str] | tuple[str, ...] | None = None,
    run_label_prefix: str = "pilot",
    task_path: str | Path = "tasks/pilot/synthetic_market_direction_v0.yaml",
    data_output_dir: str | Path = "data/raw/synthetic_market_direction_v0",
    private_dir: str | Path = "data/private/synthetic_market_direction_v0",
    runs_root: str | Path = DEFAULT_SYNTHETIC_MARKET_SUITE_RUNS_ROOT,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_synthetic_market_baseline_suite",
) -> BaselineSuiteResult:
    if repeat < 1:
        raise ValueError("repeat must be at least 1")

    selected_baselines = tuple(baselines or DEFAULT_SYNTHETIC_MARKET_BASELINES)
    unknown_baselines = sorted(set(selected_baselines) - set(DEFAULT_SYNTHETIC_MARKET_BASELINES))
    if unknown_baselines:
        raise ValueError(f"Unknown baselines: {unknown_baselines}")

    root = Path(runs_root)
    task_run_root = root / SYNTHETIC_MARKET_TASK_ID
    results: list[PipelineResult] = []
    for repeat_offset in range(repeat):
        current_seed = seed + repeat_offset
        run_label = f"{run_label_prefix}_{repeat_offset + 1:03d}_seed_{current_seed}"
        repeat_data_dir = Path(data_output_dir) / run_label
        repeat_private_dir = Path(private_dir) / run_label

        if MOMENTUM_BASELINE_ID in selected_baselines:
            results.append(
                run_synthetic_market_momentum_pipeline(
                    seed=current_seed,
                    task_path=task_path,
                    data_output_dir=repeat_data_dir,
                    private_dir=repeat_private_dir,
                    run_dir=task_run_root / MOMENTUM_BASELINE_ID,
                    run_label=run_label,
                    repeat_index=repeat_offset + 1,
                    repeat_count=repeat,
                    runs_root=root,
                    report_csv_path=report_csv_path,
                    report_markdown_path=report_markdown_path,
                    summary_csv_path=summary_csv_path,
                    summary_markdown_path=summary_markdown_path,
                    execute_notebook=execute_notebook,
                    command=command,
                )
            )

        if LOGISTIC_BASELINE_ID in selected_baselines:
            results.append(
                run_synthetic_market_logistic_pipeline(
                    seed=current_seed,
                    task_path=task_path,
                    data_output_dir=repeat_data_dir,
                    private_dir=repeat_private_dir,
                    run_dir=task_run_root / LOGISTIC_BASELINE_ID,
                    run_label=run_label,
                    repeat_index=repeat_offset + 1,
                    repeat_count=repeat,
                    runs_root=root,
                    report_csv_path=report_csv_path,
                    report_markdown_path=report_markdown_path,
                    summary_csv_path=summary_csv_path,
                    summary_markdown_path=summary_markdown_path,
                    execute_notebook=execute_notebook,
                    command=command,
                )
            )

    return BaselineSuiteResult(results=results)
