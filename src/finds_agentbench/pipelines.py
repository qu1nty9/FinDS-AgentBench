from __future__ import annotations

import json
import shutil
import sys
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
    load_result_rows_from_manifests,
    write_results_csv,
    write_results_markdown,
    write_summary_csv,
    write_summary_markdown,
)
from finds_agentbench.runs import build_run_manifest, slugify, utc_now, write_run_manifest
from finds_agentbench.scoring import (
    score_front_end_spread_widening_submission,
    score_synthetic_event_response_submission,
    score_synthetic_market_submission,
    score_usd_afe_vs_eme_relative_submission,
    score_yield_curve_10y3mo_steepening_submission,
    score_yield_curve_10y2y_steepening_submission,
    score_usd_broad_direction_submission,
    score_yield_direction_treasury10y_submission,
)
from finds_agentbench.synthetic import (
    SyntheticEventPaths,
    SyntheticMarketPaths,
    write_synthetic_event_response_task,
    write_synthetic_market_direction_task,
)
from finds_agentbench.treasury import (
    DEFAULT_REALTIME_SNAPSHOT_DATE,
    TreasuryTaskPaths,
    write_yield_direction_task,
    write_yield_extra_trees_submission_artifacts,
    write_yield_logistic_submission_artifacts,
    write_yield_previous_day_direction_submission_artifacts,
    write_yield_random_forest_submission_artifacts,
)
from finds_agentbench.yield_curve import (
    YieldCurveTaskPaths,
    write_curve_extra_trees_submission_artifacts,
    write_curve_logistic_submission_artifacts,
    write_curve_previous_day_direction_submission_artifacts,
    write_curve_random_forest_submission_artifacts,
    write_yield_curve_10y2y_steepening_task,
)
import finds_agentbench.curve_10y3mo as curve_10y3mo_module
from finds_agentbench.curve_10y3mo import (
    YieldCurveTaskPaths as YieldCurve10Y3MTaskPaths,
    write_yield_curve_10y3mo_steepening_task,
)
from finds_agentbench.front_end import (
    FrontEndSpreadTaskPaths,
    write_front_end_extra_trees_submission_artifacts,
    write_front_end_logistic_submission_artifacts,
    write_front_end_previous_day_direction_submission_artifacts,
    write_front_end_random_forest_submission_artifacts,
    write_front_end_spread_widening_task,
)
from finds_agentbench.usd_broad import (
    USDBroadTaskPaths,
    write_usd_broad_direction_task,
    write_usd_broad_extra_trees_submission_artifacts,
    write_usd_broad_logistic_submission_artifacts,
    write_usd_broad_previous_day_direction_submission_artifacts,
    write_usd_broad_random_forest_submission_artifacts,
)
from finds_agentbench.usd_relative import (
    USDRelativeTaskPaths,
    write_usd_relative_direction_task,
    write_usd_relative_extra_trees_submission_artifacts,
    write_usd_relative_logistic_submission_artifacts,
    write_usd_relative_previous_day_direction_submission_artifacts,
    write_usd_relative_random_forest_submission_artifacts,
)

SYNTHETIC_MARKET_TASK_ID = "synthetic_market_direction_v0"
SYNTHETIC_EVENT_TASK_ID = "synthetic_event_response_v0"
TREASURY_TASK_ID = "yield_direction_treasury10y_v0"
TREASURY_CURVE_TASK_ID = "yield_curve_10y2y_steepening_v0"
TREASURY_CURVE_10Y3MO_TASK_ID = "yield_curve_10y3mo_steepening_v0"
FRONT_END_TASK_ID = "front_end_spread_widening_v0"
USD_BROAD_TASK_ID = "usd_broad_direction_v0"
USD_RELATIVE_TASK_ID = "usd_afe_vs_eme_relative_direction_v0"
MOMENTUM_BASELINE_ID = "momentum_baseline"
LOGISTIC_BASELINE_ID = "logistic_regression_baseline"
EVENT_RULE_BASELINE_ID = "event_rule_baseline"
PREVIOUS_DAY_DIRECTION_BASELINE_ID = "previous_day_direction_baseline"
RANDOM_FOREST_BASELINE_ID = "random_forest_baseline"
EXTRA_TREES_BASELINE_ID = "extra_trees_baseline"
DEFAULT_SYNTHETIC_MARKET_BASELINES = (MOMENTUM_BASELINE_ID, LOGISTIC_BASELINE_ID)
DEFAULT_TREASURY_BASELINES = (
    PREVIOUS_DAY_DIRECTION_BASELINE_ID,
    LOGISTIC_BASELINE_ID,
    RANDOM_FOREST_BASELINE_ID,
    EXTRA_TREES_BASELINE_ID,
)
DEFAULT_SYNTHETIC_MARKET_SUITE_RUNS_ROOT = "runs/suites/synthetic_market_direction_v0_pilot"
DEFAULT_TREASURY_SUITE_RUNS_ROOT = "runs/suites/yield_direction_treasury10y_v0_pilot"
DEFAULT_TREASURY_CURVE_SUITE_RUNS_ROOT = "runs/suites/yield_curve_10y2y_steepening_v0_pilot"
DEFAULT_TREASURY_CURVE_10Y3MO_SUITE_RUNS_ROOT = "runs/suites/yield_curve_10y3mo_steepening_v0_pilot"
DEFAULT_FRONT_END_SUITE_RUNS_ROOT = "runs/suites/front_end_spread_widening_v0_pilot"
DEFAULT_USD_BROAD_SUITE_RUNS_ROOT = "runs/suites/usd_broad_direction_v0_pilot"
DEFAULT_USD_RELATIVE_SUITE_RUNS_ROOT = "runs/suites/usd_afe_vs_eme_relative_direction_v0_pilot"
DEFAULT_SYNTHETIC_MARKET_AGENT_SUITE_RUNS_ROOT = "runs/suites/synthetic_market_direction_v0_agents"
DEFAULT_SYNTHETIC_EVENT_AGENT_SUITE_RUNS_ROOT = "runs/suites/synthetic_event_response_v0_agents"
DEFAULT_TREASURY_AGENT_SUITE_RUNS_ROOT = "runs/suites/yield_direction_treasury10y_v0_agents"
DEFAULT_TREASURY_CURVE_AGENT_SUITE_RUNS_ROOT = "runs/suites/yield_curve_10y2y_steepening_v0_agents"
DEFAULT_TREASURY_CURVE_10Y3MO_AGENT_SUITE_RUNS_ROOT = "runs/suites/yield_curve_10y3mo_steepening_v0_agents"
DEFAULT_FRONT_END_AGENT_SUITE_RUNS_ROOT = "runs/suites/front_end_spread_widening_v0_agents"
DEFAULT_USD_BROAD_AGENT_SUITE_RUNS_ROOT = "runs/suites/usd_broad_direction_v0_agents"
DEFAULT_USD_RELATIVE_AGENT_SUITE_RUNS_ROOT = "runs/suites/usd_afe_vs_eme_relative_direction_v0_agents"
DEFAULT_PILOT_BASELINE_SUITE_RUNS_ROOT = "runs/suites/pilot_baselines_v0"
DEFAULT_PILOT_AGENT_SUITE_RUNS_ROOT = "runs/suites/pilot_agents_v0"
DEFAULT_PILOT_PROTOCOL_RUNS_ROOT = "runs/suites/pilot_protocol_v0"


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


@dataclass(frozen=True)
class PilotProtocolResult:
    baseline_result: BaselineSuiteResult
    agent_result: AgentSuiteResult

    @property
    def results(self) -> list[PipelineResult]:
        return [*self.baseline_result.results, *self.agent_result.results]

    @property
    def status(self) -> str:
        if self.baseline_result.status == "completed" and self.agent_result.status == "completed":
            return "completed"
        return "failed"

    @property
    def report_csv_path(self) -> Path | None:
        return self.agent_result.report_csv_path or self.baseline_result.report_csv_path

    @property
    def report_markdown_path(self) -> Path | None:
        return self.agent_result.report_markdown_path or self.baseline_result.report_markdown_path

    @property
    def summary_csv_path(self) -> Path | None:
        return self.agent_result.summary_csv_path or self.baseline_result.summary_csv_path

    @property
    def summary_markdown_path(self) -> Path | None:
        return self.agent_result.summary_markdown_path or self.baseline_result.summary_markdown_path


def predictive_task_agent_env(
    *,
    task_id: str,
    seed: int,
    task_path: str | Path,
    data_paths: SyntheticMarketPaths
    | SyntheticEventPaths
    | TreasuryTaskPaths
    | YieldCurveTaskPaths
    | YieldCurve10Y3MTaskPaths
    | FrontEndSpreadTaskPaths
    | USDBroadTaskPaths
    | USDRelativeTaskPaths,
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


def treasury_agent_env(
    *,
    seed: int,
    task_path: str | Path,
    data_paths: TreasuryTaskPaths,
    submission_dir: str | Path,
) -> dict[str, str]:
    return predictive_task_agent_env(
        task_id=TREASURY_TASK_ID,
        seed=seed,
        task_path=task_path,
        data_paths=data_paths,
        submission_dir=submission_dir,
    )


def yield_curve_agent_env(
    *,
    seed: int,
    task_path: str | Path,
    data_paths: YieldCurveTaskPaths,
    submission_dir: str | Path,
) -> dict[str, str]:
    return predictive_task_agent_env(
        task_id=TREASURY_CURVE_TASK_ID,
        seed=seed,
        task_path=task_path,
        data_paths=data_paths,
        submission_dir=submission_dir,
    )


def yield_curve_10y3mo_agent_env(
    *,
    seed: int,
    task_path: str | Path,
    data_paths: YieldCurve10Y3MTaskPaths,
    submission_dir: str | Path,
) -> dict[str, str]:
    return predictive_task_agent_env(
        task_id=TREASURY_CURVE_10Y3MO_TASK_ID,
        seed=seed,
        task_path=task_path,
        data_paths=data_paths,
        submission_dir=submission_dir,
    )


def front_end_agent_env(
    *,
    seed: int,
    task_path: str | Path,
    data_paths: FrontEndSpreadTaskPaths,
    submission_dir: str | Path,
) -> dict[str, str]:
    return predictive_task_agent_env(
        task_id=FRONT_END_TASK_ID,
        seed=seed,
        task_path=task_path,
        data_paths=data_paths,
        submission_dir=submission_dir,
    )


def usd_broad_agent_env(
    *,
    seed: int,
    task_path: str | Path,
    data_paths: USDBroadTaskPaths,
    submission_dir: str | Path,
) -> dict[str, str]:
    return predictive_task_agent_env(
        task_id=USD_BROAD_TASK_ID,
        seed=seed,
        task_path=task_path,
        data_paths=data_paths,
        submission_dir=submission_dir,
    )


def usd_relative_agent_env(
    *,
    seed: int,
    task_path: str | Path,
    data_paths: USDRelativeTaskPaths,
    submission_dir: str | Path,
) -> dict[str, str]:
    return predictive_task_agent_env(
        task_id=USD_RELATIVE_TASK_ID,
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


def remove_output_path(path: str | Path) -> None:
    target = Path(path)
    if not target.exists():
        return
    if target.is_dir() and not target.is_symlink():
        shutil.rmtree(target)
        return
    target.unlink()


def clear_benchmark_report_outputs(
    *,
    report_csv_path: str | Path,
    report_markdown_path: str | Path,
    summary_csv_path: str | Path,
    summary_markdown_path: str | Path,
) -> None:
    for output_path in (
        report_csv_path,
        report_markdown_path,
        summary_csv_path,
        summary_markdown_path,
    ):
        remove_output_path(output_path)


def write_benchmark_reports_for_results(
    *,
    results: list[PipelineResult],
    report_csv_path: str | Path,
    report_markdown_path: str | Path,
    summary_csv_path: str | Path,
    summary_markdown_path: str | Path,
) -> tuple[Path, Path, Path, Path]:
    rows = load_result_rows_from_manifests([result.manifest_path for result in results])
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


def complete_yield_direction_treasury10y_baseline_pipeline(
    *,
    task_path: str | Path,
    data_paths: TreasuryTaskPaths,
    run_path: Path,
    baseline_id: str,
    seed: int,
    run_label: str | None,
    repeat_index: int | None,
    repeat_count: int | None,
    runs_root: str | Path | None,
    report_csv_path: str | Path,
    report_markdown_path: str | Path,
    summary_csv_path: str | Path,
    summary_markdown_path: str | Path,
    execute_notebook: bool,
    command: str,
    baseline_metadata: dict[str, Any],
) -> PipelineResult:
    score = score_yield_direction_treasury10y_submission(
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

    metadata = json.loads(data_paths.metadata.read_text(encoding="utf-8"))
    command_started_at = utc_now()
    command_completed_at = utc_now()
    manifest = build_run_manifest(
        task_id=TREASURY_TASK_ID,
        agent_id=baseline_id,
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
            extra={
                "baseline_metadata": baseline_metadata,
                "observation_start": metadata.get("observation_start"),
                "observation_end": metadata.get("observation_end"),
                "snapshot_date": metadata.get("snapshot_date"),
                "source_mode": metadata.get("source_mode"),
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


def complete_yield_curve_10y2y_steepening_baseline_pipeline(
    *,
    task_path: str | Path,
    data_paths: YieldCurveTaskPaths,
    run_path: Path,
    baseline_id: str,
    seed: int,
    run_label: str | None,
    repeat_index: int | None,
    repeat_count: int | None,
    runs_root: str | Path | None,
    report_csv_path: str | Path,
    report_markdown_path: str | Path,
    summary_csv_path: str | Path,
    summary_markdown_path: str | Path,
    execute_notebook: bool,
    command: str,
    baseline_metadata: dict[str, Any],
) -> PipelineResult:
    score = score_yield_curve_10y2y_steepening_submission(
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

    metadata = json.loads(data_paths.metadata.read_text(encoding="utf-8"))
    command_started_at = utc_now()
    command_completed_at = utc_now()
    manifest = build_run_manifest(
        task_id=TREASURY_CURVE_TASK_ID,
        agent_id=baseline_id,
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
            extra={
                "baseline_metadata": baseline_metadata,
                "observation_start": metadata.get("observation_start"),
                "observation_end": metadata.get("observation_end"),
                "snapshot_date": metadata.get("snapshot_date"),
                "source_mode": metadata.get("source_mode"),
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


def complete_yield_curve_10y3mo_steepening_baseline_pipeline(
    *,
    task_path: str | Path,
    data_paths: YieldCurve10Y3MTaskPaths,
    run_path: Path,
    baseline_id: str,
    seed: int,
    run_label: str | None,
    repeat_index: int | None,
    repeat_count: int | None,
    runs_root: str | Path | None,
    report_csv_path: str | Path,
    report_markdown_path: str | Path,
    summary_csv_path: str | Path,
    summary_markdown_path: str | Path,
    execute_notebook: bool,
    command: str,
    baseline_metadata: dict[str, Any],
) -> PipelineResult:
    score = score_yield_curve_10y3mo_steepening_submission(
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

    metadata = json.loads(data_paths.metadata.read_text(encoding="utf-8"))
    command_started_at = utc_now()
    command_completed_at = utc_now()
    manifest = build_run_manifest(
        task_id=TREASURY_CURVE_10Y3MO_TASK_ID,
        agent_id=baseline_id,
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
            extra={
                "baseline_metadata": baseline_metadata,
                "observation_start": metadata.get("observation_start"),
                "observation_end": metadata.get("observation_end"),
                "snapshot_date": metadata.get("snapshot_date"),
                "source_mode": metadata.get("source_mode"),
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


def complete_front_end_spread_widening_baseline_pipeline(
    *,
    task_path: str | Path,
    data_paths: FrontEndSpreadTaskPaths,
    run_path: Path,
    baseline_id: str,
    seed: int,
    run_label: str | None,
    repeat_index: int | None,
    repeat_count: int | None,
    runs_root: str | Path | None,
    report_csv_path: str | Path,
    report_markdown_path: str | Path,
    summary_csv_path: str | Path,
    summary_markdown_path: str | Path,
    execute_notebook: bool,
    command: str,
    baseline_metadata: dict[str, Any],
) -> PipelineResult:
    score = score_front_end_spread_widening_submission(
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

    metadata = json.loads(data_paths.metadata.read_text(encoding="utf-8"))
    command_started_at = utc_now()
    command_completed_at = utc_now()
    manifest = build_run_manifest(
        task_id=FRONT_END_TASK_ID,
        agent_id=baseline_id,
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
            extra={
                "baseline_metadata": baseline_metadata,
                "observation_start": metadata.get("observation_start"),
                "observation_end": metadata.get("observation_end"),
                "snapshot_date": metadata.get("snapshot_date"),
                "source_mode": metadata.get("source_mode"),
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


def complete_usd_broad_direction_baseline_pipeline(
    *,
    task_path: str | Path,
    data_paths: USDBroadTaskPaths,
    run_path: Path,
    baseline_id: str,
    seed: int,
    run_label: str | None,
    repeat_index: int | None,
    repeat_count: int | None,
    runs_root: str | Path | None,
    report_csv_path: str | Path,
    report_markdown_path: str | Path,
    summary_csv_path: str | Path,
    summary_markdown_path: str | Path,
    execute_notebook: bool,
    command: str,
    baseline_metadata: dict[str, Any],
) -> PipelineResult:
    score = score_usd_broad_direction_submission(
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

    metadata = json.loads(data_paths.metadata.read_text(encoding="utf-8"))
    command_started_at = utc_now()
    command_completed_at = utc_now()
    manifest = build_run_manifest(
        task_id=USD_BROAD_TASK_ID,
        agent_id=baseline_id,
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
            extra={
                "baseline_metadata": baseline_metadata,
                "observation_start": metadata.get("observation_start"),
                "observation_end": metadata.get("observation_end"),
                "snapshot_date": metadata.get("snapshot_date"),
                "source_mode": metadata.get("source_mode"),
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


def complete_usd_afe_vs_eme_relative_direction_baseline_pipeline(
    *,
    task_path: str | Path,
    data_paths: USDRelativeTaskPaths,
    run_path: Path,
    baseline_id: str,
    seed: int,
    run_label: str | None,
    repeat_index: int | None,
    repeat_count: int | None,
    runs_root: str | Path | None,
    report_csv_path: str | Path,
    report_markdown_path: str | Path,
    summary_csv_path: str | Path,
    summary_markdown_path: str | Path,
    execute_notebook: bool,
    command: str,
    baseline_metadata: dict[str, Any],
) -> PipelineResult:
    score = score_usd_afe_vs_eme_relative_submission(
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

    metadata = json.loads(data_paths.metadata.read_text(encoding="utf-8"))
    command_started_at = utc_now()
    command_completed_at = utc_now()
    manifest = build_run_manifest(
        task_id=USD_RELATIVE_TASK_ID,
        agent_id=baseline_id,
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
            extra={
                "baseline_metadata": baseline_metadata,
                "observation_start": metadata.get("observation_start"),
                "observation_end": metadata.get("observation_end"),
                "snapshot_date": metadata.get("snapshot_date"),
                "source_mode": metadata.get("source_mode"),
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


def run_yield_direction_treasury10y_previous_day_pipeline(
    *,
    seed: int = 29,
    task_path: str | Path = "tasks/pilot/yield_direction_treasury10y_v0.yaml",
    data_output_dir: str | Path = "data/raw/yield_direction_treasury10y_v0",
    private_dir: str | Path = "data/private/yield_direction_treasury10y_v0",
    run_dir: str | Path = "runs/yield_direction_treasury10y_v0/previous_day_direction_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_yield_direction_treasury10y_previous_day_pipeline",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_yield_direction_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    run_path = resolve_run_path(run_dir, run_label)
    baseline_metadata = write_yield_previous_day_direction_submission_artifacts(
        train_public_path=data_paths.train_public,
        holdout_features_path=data_paths.private_holdout_features,
        output_dir=run_path,
    )
    return complete_yield_direction_treasury10y_baseline_pipeline(
        task_path=task_path,
        data_paths=data_paths,
        run_path=run_path,
        baseline_id=PREVIOUS_DAY_DIRECTION_BASELINE_ID,
        seed=seed,
        run_label=run_label,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
        runs_root=runs_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command=command,
        baseline_metadata=baseline_metadata,
    )


def run_yield_direction_treasury10y_logistic_pipeline(
    *,
    seed: int = 29,
    task_path: str | Path = "tasks/pilot/yield_direction_treasury10y_v0.yaml",
    data_output_dir: str | Path = "data/raw/yield_direction_treasury10y_v0",
    private_dir: str | Path = "data/private/yield_direction_treasury10y_v0",
    run_dir: str | Path = "runs/yield_direction_treasury10y_v0/logistic_regression_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_yield_direction_treasury10y_logistic_pipeline",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_yield_direction_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    run_path = resolve_run_path(run_dir, run_label)
    baseline_metadata = write_yield_logistic_submission_artifacts(
        train_public_path=data_paths.train_public,
        holdout_features_path=data_paths.private_holdout_features,
        output_dir=run_path,
        random_state=seed,
    )
    return complete_yield_direction_treasury10y_baseline_pipeline(
        task_path=task_path,
        data_paths=data_paths,
        run_path=run_path,
        baseline_id=LOGISTIC_BASELINE_ID,
        seed=seed,
        run_label=run_label,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
        runs_root=runs_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command=command,
        baseline_metadata=baseline_metadata,
    )


def run_yield_direction_treasury10y_random_forest_pipeline(
    *,
    seed: int = 29,
    task_path: str | Path = "tasks/pilot/yield_direction_treasury10y_v0.yaml",
    data_output_dir: str | Path = "data/raw/yield_direction_treasury10y_v0",
    private_dir: str | Path = "data/private/yield_direction_treasury10y_v0",
    run_dir: str | Path = "runs/yield_direction_treasury10y_v0/random_forest_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_yield_direction_treasury10y_random_forest_pipeline",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_yield_direction_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    run_path = resolve_run_path(run_dir, run_label)
    baseline_metadata = write_yield_random_forest_submission_artifacts(
        train_public_path=data_paths.train_public,
        holdout_features_path=data_paths.private_holdout_features,
        output_dir=run_path,
        random_state=seed,
    )
    return complete_yield_direction_treasury10y_baseline_pipeline(
        task_path=task_path,
        data_paths=data_paths,
        run_path=run_path,
        baseline_id=RANDOM_FOREST_BASELINE_ID,
        seed=seed,
        run_label=run_label,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
        runs_root=runs_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command=command,
        baseline_metadata=baseline_metadata,
    )


def run_yield_direction_treasury10y_extra_trees_pipeline(
    *,
    seed: int = 29,
    task_path: str | Path = "tasks/pilot/yield_direction_treasury10y_v0.yaml",
    data_output_dir: str | Path = "data/raw/yield_direction_treasury10y_v0",
    private_dir: str | Path = "data/private/yield_direction_treasury10y_v0",
    run_dir: str | Path = "runs/yield_direction_treasury10y_v0/extra_trees_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_yield_direction_treasury10y_extra_trees_pipeline",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_yield_direction_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    run_path = resolve_run_path(run_dir, run_label)
    baseline_metadata = write_yield_extra_trees_submission_artifacts(
        train_public_path=data_paths.train_public,
        holdout_features_path=data_paths.private_holdout_features,
        output_dir=run_path,
        random_state=seed,
    )
    return complete_yield_direction_treasury10y_baseline_pipeline(
        task_path=task_path,
        data_paths=data_paths,
        run_path=run_path,
        baseline_id=EXTRA_TREES_BASELINE_ID,
        seed=seed,
        run_label=run_label,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
        runs_root=runs_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command=command,
        baseline_metadata=baseline_metadata,
    )


def run_yield_curve_10y2y_steepening_previous_day_pipeline(
    *,
    seed: int = 29,
    task_path: str | Path = "tasks/pilot/yield_curve_10y2y_steepening_v0.yaml",
    data_output_dir: str | Path = "data/raw/yield_curve_10y2y_steepening_v0",
    private_dir: str | Path = "data/private/yield_curve_10y2y_steepening_v0",
    run_dir: str | Path = "runs/yield_curve_10y2y_steepening_v0/previous_day_direction_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_yield_curve_10y2y_steepening_previous_day_pipeline",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_yield_curve_10y2y_steepening_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    run_path = resolve_run_path(run_dir, run_label)
    baseline_metadata = write_curve_previous_day_direction_submission_artifacts(
        train_public_path=data_paths.train_public,
        holdout_features_path=data_paths.private_holdout_features,
        output_dir=run_path,
    )
    return complete_yield_curve_10y2y_steepening_baseline_pipeline(
        task_path=task_path,
        data_paths=data_paths,
        run_path=run_path,
        baseline_id=PREVIOUS_DAY_DIRECTION_BASELINE_ID,
        seed=seed,
        run_label=run_label,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
        runs_root=runs_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command=command,
        baseline_metadata=baseline_metadata,
    )


def run_yield_curve_10y2y_steepening_logistic_pipeline(
    *,
    seed: int = 29,
    task_path: str | Path = "tasks/pilot/yield_curve_10y2y_steepening_v0.yaml",
    data_output_dir: str | Path = "data/raw/yield_curve_10y2y_steepening_v0",
    private_dir: str | Path = "data/private/yield_curve_10y2y_steepening_v0",
    run_dir: str | Path = "runs/yield_curve_10y2y_steepening_v0/logistic_regression_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_yield_curve_10y2y_steepening_logistic_pipeline",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_yield_curve_10y2y_steepening_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    run_path = resolve_run_path(run_dir, run_label)
    baseline_metadata = write_curve_logistic_submission_artifacts(
        train_public_path=data_paths.train_public,
        holdout_features_path=data_paths.private_holdout_features,
        output_dir=run_path,
        random_state=seed,
    )
    return complete_yield_curve_10y2y_steepening_baseline_pipeline(
        task_path=task_path,
        data_paths=data_paths,
        run_path=run_path,
        baseline_id=LOGISTIC_BASELINE_ID,
        seed=seed,
        run_label=run_label,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
        runs_root=runs_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command=command,
        baseline_metadata=baseline_metadata,
    )


def run_yield_curve_10y2y_steepening_random_forest_pipeline(
    *,
    seed: int = 29,
    task_path: str | Path = "tasks/pilot/yield_curve_10y2y_steepening_v0.yaml",
    data_output_dir: str | Path = "data/raw/yield_curve_10y2y_steepening_v0",
    private_dir: str | Path = "data/private/yield_curve_10y2y_steepening_v0",
    run_dir: str | Path = "runs/yield_curve_10y2y_steepening_v0/random_forest_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_yield_curve_10y2y_steepening_random_forest_pipeline",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_yield_curve_10y2y_steepening_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    run_path = resolve_run_path(run_dir, run_label)
    baseline_metadata = write_curve_random_forest_submission_artifacts(
        train_public_path=data_paths.train_public,
        holdout_features_path=data_paths.private_holdout_features,
        output_dir=run_path,
        random_state=seed,
    )
    return complete_yield_curve_10y2y_steepening_baseline_pipeline(
        task_path=task_path,
        data_paths=data_paths,
        run_path=run_path,
        baseline_id=RANDOM_FOREST_BASELINE_ID,
        seed=seed,
        run_label=run_label,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
        runs_root=runs_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command=command,
        baseline_metadata=baseline_metadata,
    )


def run_yield_curve_10y2y_steepening_extra_trees_pipeline(
    *,
    seed: int = 29,
    task_path: str | Path = "tasks/pilot/yield_curve_10y2y_steepening_v0.yaml",
    data_output_dir: str | Path = "data/raw/yield_curve_10y2y_steepening_v0",
    private_dir: str | Path = "data/private/yield_curve_10y2y_steepening_v0",
    run_dir: str | Path = "runs/yield_curve_10y2y_steepening_v0/extra_trees_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_yield_curve_10y2y_steepening_extra_trees_pipeline",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_yield_curve_10y2y_steepening_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    run_path = resolve_run_path(run_dir, run_label)
    baseline_metadata = write_curve_extra_trees_submission_artifacts(
        train_public_path=data_paths.train_public,
        holdout_features_path=data_paths.private_holdout_features,
        output_dir=run_path,
        random_state=seed,
    )
    return complete_yield_curve_10y2y_steepening_baseline_pipeline(
        task_path=task_path,
        data_paths=data_paths,
        run_path=run_path,
        baseline_id=EXTRA_TREES_BASELINE_ID,
        seed=seed,
        run_label=run_label,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
        runs_root=runs_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command=command,
        baseline_metadata=baseline_metadata,
    )


def run_yield_curve_10y3mo_steepening_previous_day_pipeline(
    *,
    seed: int = 29,
    task_path: str | Path = "tasks/pilot/yield_curve_10y3mo_steepening_v0.yaml",
    data_output_dir: str | Path = "data/raw/yield_curve_10y3mo_steepening_v0",
    private_dir: str | Path = "data/private/yield_curve_10y3mo_steepening_v0",
    run_dir: str | Path = "runs/yield_curve_10y3mo_steepening_v0/previous_day_direction_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_yield_curve_10y3mo_steepening_previous_day_pipeline",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_yield_curve_10y3mo_steepening_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    run_path = resolve_run_path(run_dir, run_label)
    baseline_metadata = curve_10y3mo_module.write_curve_previous_day_direction_submission_artifacts(
        train_public_path=data_paths.train_public,
        holdout_features_path=data_paths.private_holdout_features,
        output_dir=run_path,
    )
    return complete_yield_curve_10y3mo_steepening_baseline_pipeline(
        task_path=task_path,
        data_paths=data_paths,
        run_path=run_path,
        baseline_id=PREVIOUS_DAY_DIRECTION_BASELINE_ID,
        seed=seed,
        run_label=run_label,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
        runs_root=runs_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command=command,
        baseline_metadata=baseline_metadata,
    )


def run_yield_curve_10y3mo_steepening_logistic_pipeline(
    *,
    seed: int = 29,
    task_path: str | Path = "tasks/pilot/yield_curve_10y3mo_steepening_v0.yaml",
    data_output_dir: str | Path = "data/raw/yield_curve_10y3mo_steepening_v0",
    private_dir: str | Path = "data/private/yield_curve_10y3mo_steepening_v0",
    run_dir: str | Path = "runs/yield_curve_10y3mo_steepening_v0/logistic_regression_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_yield_curve_10y3mo_steepening_logistic_pipeline",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_yield_curve_10y3mo_steepening_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    run_path = resolve_run_path(run_dir, run_label)
    baseline_metadata = curve_10y3mo_module.write_curve_logistic_submission_artifacts(
        train_public_path=data_paths.train_public,
        holdout_features_path=data_paths.private_holdout_features,
        output_dir=run_path,
        random_state=seed,
    )
    return complete_yield_curve_10y3mo_steepening_baseline_pipeline(
        task_path=task_path,
        data_paths=data_paths,
        run_path=run_path,
        baseline_id=LOGISTIC_BASELINE_ID,
        seed=seed,
        run_label=run_label,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
        runs_root=runs_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command=command,
        baseline_metadata=baseline_metadata,
    )


def run_yield_curve_10y3mo_steepening_random_forest_pipeline(
    *,
    seed: int = 29,
    task_path: str | Path = "tasks/pilot/yield_curve_10y3mo_steepening_v0.yaml",
    data_output_dir: str | Path = "data/raw/yield_curve_10y3mo_steepening_v0",
    private_dir: str | Path = "data/private/yield_curve_10y3mo_steepening_v0",
    run_dir: str | Path = "runs/yield_curve_10y3mo_steepening_v0/random_forest_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_yield_curve_10y3mo_steepening_random_forest_pipeline",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_yield_curve_10y3mo_steepening_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    run_path = resolve_run_path(run_dir, run_label)
    baseline_metadata = curve_10y3mo_module.write_curve_random_forest_submission_artifacts(
        train_public_path=data_paths.train_public,
        holdout_features_path=data_paths.private_holdout_features,
        output_dir=run_path,
        random_state=seed,
    )
    return complete_yield_curve_10y3mo_steepening_baseline_pipeline(
        task_path=task_path,
        data_paths=data_paths,
        run_path=run_path,
        baseline_id=RANDOM_FOREST_BASELINE_ID,
        seed=seed,
        run_label=run_label,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
        runs_root=runs_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command=command,
        baseline_metadata=baseline_metadata,
    )


def run_yield_curve_10y3mo_steepening_extra_trees_pipeline(
    *,
    seed: int = 29,
    task_path: str | Path = "tasks/pilot/yield_curve_10y3mo_steepening_v0.yaml",
    data_output_dir: str | Path = "data/raw/yield_curve_10y3mo_steepening_v0",
    private_dir: str | Path = "data/private/yield_curve_10y3mo_steepening_v0",
    run_dir: str | Path = "runs/yield_curve_10y3mo_steepening_v0/extra_trees_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_yield_curve_10y3mo_steepening_extra_trees_pipeline",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_yield_curve_10y3mo_steepening_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    run_path = resolve_run_path(run_dir, run_label)
    baseline_metadata = curve_10y3mo_module.write_curve_extra_trees_submission_artifacts(
        train_public_path=data_paths.train_public,
        holdout_features_path=data_paths.private_holdout_features,
        output_dir=run_path,
        random_state=seed,
    )
    return complete_yield_curve_10y3mo_steepening_baseline_pipeline(
        task_path=task_path,
        data_paths=data_paths,
        run_path=run_path,
        baseline_id=EXTRA_TREES_BASELINE_ID,
        seed=seed,
        run_label=run_label,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
        runs_root=runs_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command=command,
        baseline_metadata=baseline_metadata,
    )


def run_front_end_spread_widening_v0_previous_day_pipeline(
    *,
    seed: int = 31,
    task_path: str | Path = "tasks/pilot/front_end_spread_widening_v0.yaml",
    data_output_dir: str | Path = "data/raw/front_end_spread_widening_v0",
    private_dir: str | Path = "data/private/front_end_spread_widening_v0",
    run_dir: str | Path = "runs/front_end_spread_widening_v0/previous_day_direction_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_front_end_spread_widening_v0_previous_day_pipeline",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_front_end_spread_widening_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    run_path = resolve_run_path(run_dir, run_label)
    baseline_metadata = write_front_end_previous_day_direction_submission_artifacts(
        train_public_path=data_paths.train_public,
        holdout_features_path=data_paths.private_holdout_features,
        output_dir=run_path,
    )
    return complete_front_end_spread_widening_baseline_pipeline(
        task_path=task_path,
        data_paths=data_paths,
        run_path=run_path,
        baseline_id=PREVIOUS_DAY_DIRECTION_BASELINE_ID,
        seed=seed,
        run_label=run_label,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
        runs_root=runs_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command=command,
        baseline_metadata=baseline_metadata,
    )


def run_front_end_spread_widening_v0_logistic_pipeline(
    *,
    seed: int = 31,
    task_path: str | Path = "tasks/pilot/front_end_spread_widening_v0.yaml",
    data_output_dir: str | Path = "data/raw/front_end_spread_widening_v0",
    private_dir: str | Path = "data/private/front_end_spread_widening_v0",
    run_dir: str | Path = "runs/front_end_spread_widening_v0/logistic_regression_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_front_end_spread_widening_v0_logistic_pipeline",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_front_end_spread_widening_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    run_path = resolve_run_path(run_dir, run_label)
    baseline_metadata = write_front_end_logistic_submission_artifacts(
        train_public_path=data_paths.train_public,
        holdout_features_path=data_paths.private_holdout_features,
        output_dir=run_path,
        random_state=seed,
    )
    return complete_front_end_spread_widening_baseline_pipeline(
        task_path=task_path,
        data_paths=data_paths,
        run_path=run_path,
        baseline_id=LOGISTIC_BASELINE_ID,
        seed=seed,
        run_label=run_label,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
        runs_root=runs_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command=command,
        baseline_metadata=baseline_metadata,
    )


def run_front_end_spread_widening_v0_random_forest_pipeline(
    *,
    seed: int = 31,
    task_path: str | Path = "tasks/pilot/front_end_spread_widening_v0.yaml",
    data_output_dir: str | Path = "data/raw/front_end_spread_widening_v0",
    private_dir: str | Path = "data/private/front_end_spread_widening_v0",
    run_dir: str | Path = "runs/front_end_spread_widening_v0/random_forest_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_front_end_spread_widening_v0_random_forest_pipeline",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_front_end_spread_widening_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    run_path = resolve_run_path(run_dir, run_label)
    baseline_metadata = write_front_end_random_forest_submission_artifacts(
        train_public_path=data_paths.train_public,
        holdout_features_path=data_paths.private_holdout_features,
        output_dir=run_path,
        random_state=seed,
    )
    return complete_front_end_spread_widening_baseline_pipeline(
        task_path=task_path,
        data_paths=data_paths,
        run_path=run_path,
        baseline_id=RANDOM_FOREST_BASELINE_ID,
        seed=seed,
        run_label=run_label,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
        runs_root=runs_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command=command,
        baseline_metadata=baseline_metadata,
    )


def run_front_end_spread_widening_v0_extra_trees_pipeline(
    *,
    seed: int = 31,
    task_path: str | Path = "tasks/pilot/front_end_spread_widening_v0.yaml",
    data_output_dir: str | Path = "data/raw/front_end_spread_widening_v0",
    private_dir: str | Path = "data/private/front_end_spread_widening_v0",
    run_dir: str | Path = "runs/front_end_spread_widening_v0/extra_trees_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_front_end_spread_widening_v0_extra_trees_pipeline",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_front_end_spread_widening_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    run_path = resolve_run_path(run_dir, run_label)
    baseline_metadata = write_front_end_extra_trees_submission_artifacts(
        train_public_path=data_paths.train_public,
        holdout_features_path=data_paths.private_holdout_features,
        output_dir=run_path,
        random_state=seed,
    )
    return complete_front_end_spread_widening_baseline_pipeline(
        task_path=task_path,
        data_paths=data_paths,
        run_path=run_path,
        baseline_id=EXTRA_TREES_BASELINE_ID,
        seed=seed,
        run_label=run_label,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
        runs_root=runs_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command=command,
        baseline_metadata=baseline_metadata,
    )


def run_usd_broad_direction_v0_previous_day_pipeline(
    *,
    seed: int = 37,
    task_path: str | Path = "tasks/pilot/usd_broad_direction_v0.yaml",
    data_output_dir: str | Path = "data/raw/usd_broad_direction_v0",
    private_dir: str | Path = "data/private/usd_broad_direction_v0",
    run_dir: str | Path = "runs/usd_broad_direction_v0/previous_day_direction_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_usd_broad_direction_v0_previous_day_pipeline",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_usd_broad_direction_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    run_path = resolve_run_path(run_dir, run_label)
    baseline_metadata = write_usd_broad_previous_day_direction_submission_artifacts(
        train_public_path=data_paths.train_public,
        holdout_features_path=data_paths.private_holdout_features,
        output_dir=run_path,
    )
    return complete_usd_broad_direction_baseline_pipeline(
        task_path=task_path,
        data_paths=data_paths,
        run_path=run_path,
        baseline_id=PREVIOUS_DAY_DIRECTION_BASELINE_ID,
        seed=seed,
        run_label=run_label,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
        runs_root=runs_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command=command,
        baseline_metadata=baseline_metadata,
    )


def run_usd_broad_direction_v0_logistic_pipeline(
    *,
    seed: int = 37,
    task_path: str | Path = "tasks/pilot/usd_broad_direction_v0.yaml",
    data_output_dir: str | Path = "data/raw/usd_broad_direction_v0",
    private_dir: str | Path = "data/private/usd_broad_direction_v0",
    run_dir: str | Path = "runs/usd_broad_direction_v0/logistic_regression_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_usd_broad_direction_v0_logistic_pipeline",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_usd_broad_direction_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    run_path = resolve_run_path(run_dir, run_label)
    baseline_metadata = write_usd_broad_logistic_submission_artifacts(
        train_public_path=data_paths.train_public,
        holdout_features_path=data_paths.private_holdout_features,
        output_dir=run_path,
        random_state=seed,
    )
    return complete_usd_broad_direction_baseline_pipeline(
        task_path=task_path,
        data_paths=data_paths,
        run_path=run_path,
        baseline_id=LOGISTIC_BASELINE_ID,
        seed=seed,
        run_label=run_label,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
        runs_root=runs_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command=command,
        baseline_metadata=baseline_metadata,
    )


def run_usd_broad_direction_v0_random_forest_pipeline(
    *,
    seed: int = 37,
    task_path: str | Path = "tasks/pilot/usd_broad_direction_v0.yaml",
    data_output_dir: str | Path = "data/raw/usd_broad_direction_v0",
    private_dir: str | Path = "data/private/usd_broad_direction_v0",
    run_dir: str | Path = "runs/usd_broad_direction_v0/random_forest_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_usd_broad_direction_v0_random_forest_pipeline",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_usd_broad_direction_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    run_path = resolve_run_path(run_dir, run_label)
    baseline_metadata = write_usd_broad_random_forest_submission_artifacts(
        train_public_path=data_paths.train_public,
        holdout_features_path=data_paths.private_holdout_features,
        output_dir=run_path,
        random_state=seed,
    )
    return complete_usd_broad_direction_baseline_pipeline(
        task_path=task_path,
        data_paths=data_paths,
        run_path=run_path,
        baseline_id=RANDOM_FOREST_BASELINE_ID,
        seed=seed,
        run_label=run_label,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
        runs_root=runs_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command=command,
        baseline_metadata=baseline_metadata,
    )


def run_usd_broad_direction_v0_extra_trees_pipeline(
    *,
    seed: int = 37,
    task_path: str | Path = "tasks/pilot/usd_broad_direction_v0.yaml",
    data_output_dir: str | Path = "data/raw/usd_broad_direction_v0",
    private_dir: str | Path = "data/private/usd_broad_direction_v0",
    run_dir: str | Path = "runs/usd_broad_direction_v0/extra_trees_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_usd_broad_direction_v0_extra_trees_pipeline",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_usd_broad_direction_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    run_path = resolve_run_path(run_dir, run_label)
    baseline_metadata = write_usd_broad_extra_trees_submission_artifacts(
        train_public_path=data_paths.train_public,
        holdout_features_path=data_paths.private_holdout_features,
        output_dir=run_path,
        random_state=seed,
    )
    return complete_usd_broad_direction_baseline_pipeline(
        task_path=task_path,
        data_paths=data_paths,
        run_path=run_path,
        baseline_id=EXTRA_TREES_BASELINE_ID,
        seed=seed,
        run_label=run_label,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
        runs_root=runs_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command=command,
        baseline_metadata=baseline_metadata,
    )


def run_usd_afe_vs_eme_relative_direction_v0_previous_day_pipeline(
    *,
    seed: int = 41,
    task_path: str | Path = "tasks/pilot/usd_afe_vs_eme_relative_direction_v0.yaml",
    data_output_dir: str | Path = "data/raw/usd_afe_vs_eme_relative_direction_v0",
    private_dir: str | Path = "data/private/usd_afe_vs_eme_relative_direction_v0",
    run_dir: str | Path = "runs/usd_afe_vs_eme_relative_direction_v0/previous_day_direction_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_usd_afe_vs_eme_relative_direction_v0_previous_day_pipeline",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_usd_relative_direction_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    run_path = resolve_run_path(run_dir, run_label)
    baseline_metadata = write_usd_relative_previous_day_direction_submission_artifacts(
        train_public_path=data_paths.train_public,
        holdout_features_path=data_paths.private_holdout_features,
        output_dir=run_path,
    )
    return complete_usd_afe_vs_eme_relative_direction_baseline_pipeline(
        task_path=task_path,
        data_paths=data_paths,
        run_path=run_path,
        baseline_id=PREVIOUS_DAY_DIRECTION_BASELINE_ID,
        seed=seed,
        run_label=run_label,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
        runs_root=runs_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command=command,
        baseline_metadata=baseline_metadata,
    )


def run_usd_afe_vs_eme_relative_direction_v0_logistic_pipeline(
    *,
    seed: int = 41,
    task_path: str | Path = "tasks/pilot/usd_afe_vs_eme_relative_direction_v0.yaml",
    data_output_dir: str | Path = "data/raw/usd_afe_vs_eme_relative_direction_v0",
    private_dir: str | Path = "data/private/usd_afe_vs_eme_relative_direction_v0",
    run_dir: str | Path = "runs/usd_afe_vs_eme_relative_direction_v0/logistic_regression_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_usd_afe_vs_eme_relative_direction_v0_logistic_pipeline",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_usd_relative_direction_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    run_path = resolve_run_path(run_dir, run_label)
    baseline_metadata = write_usd_relative_logistic_submission_artifacts(
        train_public_path=data_paths.train_public,
        holdout_features_path=data_paths.private_holdout_features,
        output_dir=run_path,
        random_state=seed,
    )
    return complete_usd_afe_vs_eme_relative_direction_baseline_pipeline(
        task_path=task_path,
        data_paths=data_paths,
        run_path=run_path,
        baseline_id=LOGISTIC_BASELINE_ID,
        seed=seed,
        run_label=run_label,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
        runs_root=runs_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command=command,
        baseline_metadata=baseline_metadata,
    )


def run_usd_afe_vs_eme_relative_direction_v0_random_forest_pipeline(
    *,
    seed: int = 41,
    task_path: str | Path = "tasks/pilot/usd_afe_vs_eme_relative_direction_v0.yaml",
    data_output_dir: str | Path = "data/raw/usd_afe_vs_eme_relative_direction_v0",
    private_dir: str | Path = "data/private/usd_afe_vs_eme_relative_direction_v0",
    run_dir: str | Path = "runs/usd_afe_vs_eme_relative_direction_v0/random_forest_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_usd_afe_vs_eme_relative_direction_v0_random_forest_pipeline",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_usd_relative_direction_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    run_path = resolve_run_path(run_dir, run_label)
    baseline_metadata = write_usd_relative_random_forest_submission_artifacts(
        train_public_path=data_paths.train_public,
        holdout_features_path=data_paths.private_holdout_features,
        output_dir=run_path,
        random_state=seed,
    )
    return complete_usd_afe_vs_eme_relative_direction_baseline_pipeline(
        task_path=task_path,
        data_paths=data_paths,
        run_path=run_path,
        baseline_id=RANDOM_FOREST_BASELINE_ID,
        seed=seed,
        run_label=run_label,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
        runs_root=runs_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command=command,
        baseline_metadata=baseline_metadata,
    )


def run_usd_afe_vs_eme_relative_direction_v0_extra_trees_pipeline(
    *,
    seed: int = 41,
    task_path: str | Path = "tasks/pilot/usd_afe_vs_eme_relative_direction_v0.yaml",
    data_output_dir: str | Path = "data/raw/usd_afe_vs_eme_relative_direction_v0",
    private_dir: str | Path = "data/private/usd_afe_vs_eme_relative_direction_v0",
    run_dir: str | Path = "runs/usd_afe_vs_eme_relative_direction_v0/extra_trees_baseline",
    run_label: str | None = None,
    repeat_index: int | None = None,
    repeat_count: int | None = None,
    runs_root: str | Path | None = None,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_usd_afe_vs_eme_relative_direction_v0_extra_trees_pipeline",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_usd_relative_direction_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    run_path = resolve_run_path(run_dir, run_label)
    baseline_metadata = write_usd_relative_extra_trees_submission_artifacts(
        train_public_path=data_paths.train_public,
        holdout_features_path=data_paths.private_holdout_features,
        output_dir=run_path,
        random_state=seed,
    )
    return complete_usd_afe_vs_eme_relative_direction_baseline_pipeline(
        task_path=task_path,
        data_paths=data_paths,
        run_path=run_path,
        baseline_id=EXTRA_TREES_BASELINE_ID,
        seed=seed,
        run_label=run_label,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
        runs_root=runs_root,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command=command,
        baseline_metadata=baseline_metadata,
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

    write_benchmark_reports_for_results(
        results=results,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
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

    write_benchmark_reports_for_results(
        results=results,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
    )
    return AgentSuiteResult(results=results)


def run_yield_direction_treasury10y_agent_command(
    *,
    agent_id: str,
    agent_version: str,
    agent_command: str | list[str] | tuple[str, ...],
    seed: int = 29,
    task_path: str | Path = "tasks/pilot/yield_direction_treasury10y_v0.yaml",
    data_output_dir: str | Path = "data/raw/yield_direction_treasury10y_v0",
    private_dir: str | Path = "data/private/yield_direction_treasury10y_v0",
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
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_yield_direction_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    base_run_dir = run_dir or Path("runs") / TREASURY_TASK_ID / agent_id
    run_path = resolve_run_path(base_run_dir, run_label)
    run_path.mkdir(parents=True, exist_ok=True)

    command_result = run_agent_command(
        command=agent_command,
        env=treasury_agent_env(
            seed=seed,
            task_path=task_path,
            data_paths=data_paths,
            submission_dir=run_path,
        ),
        cwd=cwd,
        log_dir=run_path / "logs",
        timeout_seconds=command_timeout_seconds,
    )

    score = score_yield_direction_treasury10y_submission(
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
        task_id=TREASURY_TASK_ID,
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
                "snapshot_date": snapshot_date,
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


def run_yield_direction_treasury10y_agent_command_suite(
    *,
    agent_id: str,
    agent_version: str,
    agent_command: str | list[str] | tuple[str, ...],
    seed: int = 29,
    repeat: int = 3,
    run_label_prefix: str = "agent",
    task_path: str | Path = "tasks/pilot/yield_direction_treasury10y_v0.yaml",
    data_output_dir: str | Path = "data/raw/yield_direction_treasury10y_v0",
    private_dir: str | Path = "data/private/yield_direction_treasury10y_v0",
    runs_root: str | Path = DEFAULT_TREASURY_AGENT_SUITE_RUNS_ROOT,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command_timeout_seconds: int = 1800,
    cwd: str | Path | None = None,
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> AgentSuiteResult:
    if repeat < 1:
        raise ValueError("repeat must be at least 1")

    root = Path(runs_root)
    task_run_root = root / TREASURY_TASK_ID
    results: list[PipelineResult] = []
    for repeat_offset in range(repeat):
        current_seed = seed + repeat_offset
        run_label = f"{run_label_prefix}_{repeat_offset + 1:03d}_seed_{current_seed}"
        results.append(
            run_yield_direction_treasury10y_agent_command(
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
                snapshot_date=snapshot_date,
                api_key=api_key,
                source_frame=source_frame,
            )
        )

    write_benchmark_reports_for_results(
        results=results,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
    )
    return AgentSuiteResult(results=results)


def run_yield_curve_10y2y_steepening_agent_command(
    *,
    agent_id: str,
    agent_version: str,
    agent_command: str | list[str] | tuple[str, ...],
    seed: int = 29,
    task_path: str | Path = "tasks/pilot/yield_curve_10y2y_steepening_v0.yaml",
    data_output_dir: str | Path = "data/raw/yield_curve_10y2y_steepening_v0",
    private_dir: str | Path = "data/private/yield_curve_10y2y_steepening_v0",
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
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_yield_curve_10y2y_steepening_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    base_run_dir = run_dir or Path("runs") / TREASURY_CURVE_TASK_ID / agent_id
    run_path = resolve_run_path(base_run_dir, run_label)
    run_path.mkdir(parents=True, exist_ok=True)

    command_result = run_agent_command(
        command=agent_command,
        env=yield_curve_agent_env(
            seed=seed,
            task_path=task_path,
            data_paths=data_paths,
            submission_dir=run_path,
        ),
        cwd=cwd,
        log_dir=run_path / "logs",
        timeout_seconds=command_timeout_seconds,
    )

    score = score_yield_curve_10y2y_steepening_submission(
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
        task_id=TREASURY_CURVE_TASK_ID,
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
                "snapshot_date": snapshot_date,
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


def run_yield_curve_10y2y_steepening_agent_command_suite(
    *,
    agent_id: str,
    agent_version: str,
    agent_command: str | list[str] | tuple[str, ...],
    seed: int = 29,
    repeat: int = 3,
    run_label_prefix: str = "agent",
    task_path: str | Path = "tasks/pilot/yield_curve_10y2y_steepening_v0.yaml",
    data_output_dir: str | Path = "data/raw/yield_curve_10y2y_steepening_v0",
    private_dir: str | Path = "data/private/yield_curve_10y2y_steepening_v0",
    runs_root: str | Path = DEFAULT_TREASURY_CURVE_AGENT_SUITE_RUNS_ROOT,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command_timeout_seconds: int = 1800,
    cwd: str | Path | None = None,
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> AgentSuiteResult:
    if repeat < 1:
        raise ValueError("repeat must be at least 1")

    root = Path(runs_root)
    task_run_root = root / TREASURY_CURVE_TASK_ID
    results: list[PipelineResult] = []
    for repeat_offset in range(repeat):
        current_seed = seed + repeat_offset
        run_label = f"{run_label_prefix}_{repeat_offset + 1:03d}_seed_{current_seed}"
        results.append(
            run_yield_curve_10y2y_steepening_agent_command(
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
                snapshot_date=snapshot_date,
                api_key=api_key,
                source_frame=source_frame,
            )
        )

    write_benchmark_reports_for_results(
        results=results,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
    )
    return AgentSuiteResult(results=results)


def run_yield_curve_10y3mo_steepening_agent_command(
    *,
    agent_id: str,
    agent_version: str,
    agent_command: str | list[str] | tuple[str, ...],
    seed: int = 29,
    task_path: str | Path = "tasks/pilot/yield_curve_10y3mo_steepening_v0.yaml",
    data_output_dir: str | Path = "data/raw/yield_curve_10y3mo_steepening_v0",
    private_dir: str | Path = "data/private/yield_curve_10y3mo_steepening_v0",
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
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_yield_curve_10y3mo_steepening_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    base_run_dir = run_dir or Path("runs") / TREASURY_CURVE_10Y3MO_TASK_ID / agent_id
    run_path = resolve_run_path(base_run_dir, run_label)
    run_path.mkdir(parents=True, exist_ok=True)

    command_result = run_agent_command(
        command=agent_command,
        env=yield_curve_10y3mo_agent_env(
            seed=seed,
            task_path=task_path,
            data_paths=data_paths,
            submission_dir=run_path,
        ),
        cwd=cwd,
        log_dir=run_path / "logs",
        timeout_seconds=command_timeout_seconds,
    )

    score = score_yield_curve_10y3mo_steepening_submission(
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
        task_id=TREASURY_CURVE_10Y3MO_TASK_ID,
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
                "snapshot_date": snapshot_date,
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


def run_yield_curve_10y3mo_steepening_agent_command_suite(
    *,
    agent_id: str,
    agent_version: str,
    agent_command: str | list[str] | tuple[str, ...],
    seed: int = 29,
    repeat: int = 3,
    run_label_prefix: str = "agent",
    task_path: str | Path = "tasks/pilot/yield_curve_10y3mo_steepening_v0.yaml",
    data_output_dir: str | Path = "data/raw/yield_curve_10y3mo_steepening_v0",
    private_dir: str | Path = "data/private/yield_curve_10y3mo_steepening_v0",
    runs_root: str | Path = DEFAULT_TREASURY_CURVE_10Y3MO_AGENT_SUITE_RUNS_ROOT,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command_timeout_seconds: int = 1800,
    cwd: str | Path | None = None,
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> AgentSuiteResult:
    if repeat < 1:
        raise ValueError("repeat must be at least 1")

    root = Path(runs_root)
    task_run_root = root / TREASURY_CURVE_10Y3MO_TASK_ID
    results: list[PipelineResult] = []
    for repeat_offset in range(repeat):
        current_seed = seed + repeat_offset
        run_label = f"{run_label_prefix}_{repeat_offset + 1:03d}_seed_{current_seed}"
        results.append(
            run_yield_curve_10y3mo_steepening_agent_command(
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
                snapshot_date=snapshot_date,
                api_key=api_key,
                source_frame=source_frame,
            )
        )

    write_benchmark_reports_for_results(
        results=results,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
    )
    return AgentSuiteResult(results=results)


def run_front_end_spread_widening_v0_agent_command(
    *,
    agent_id: str,
    agent_version: str,
    agent_command: str | list[str] | tuple[str, ...],
    seed: int = 31,
    task_path: str | Path = "tasks/pilot/front_end_spread_widening_v0.yaml",
    data_output_dir: str | Path = "data/raw/front_end_spread_widening_v0",
    private_dir: str | Path = "data/private/front_end_spread_widening_v0",
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
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_front_end_spread_widening_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    base_run_dir = run_dir or Path("runs") / FRONT_END_TASK_ID / agent_id
    run_path = resolve_run_path(base_run_dir, run_label)
    run_path.mkdir(parents=True, exist_ok=True)

    command_result = run_agent_command(
        command=agent_command,
        env=front_end_agent_env(
            seed=seed,
            task_path=task_path,
            data_paths=data_paths,
            submission_dir=run_path,
        ),
        cwd=cwd,
        log_dir=run_path / "logs",
        timeout_seconds=command_timeout_seconds,
    )

    score = score_front_end_spread_widening_submission(
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
        task_id=FRONT_END_TASK_ID,
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
                "snapshot_date": snapshot_date,
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


def run_front_end_spread_widening_v0_agent_command_suite(
    *,
    agent_id: str,
    agent_version: str,
    agent_command: str | list[str] | tuple[str, ...],
    seed: int = 31,
    repeat: int = 3,
    run_label_prefix: str = "agent",
    task_path: str | Path = "tasks/pilot/front_end_spread_widening_v0.yaml",
    data_output_dir: str | Path = "data/raw/front_end_spread_widening_v0",
    private_dir: str | Path = "data/private/front_end_spread_widening_v0",
    runs_root: str | Path = DEFAULT_FRONT_END_AGENT_SUITE_RUNS_ROOT,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command_timeout_seconds: int = 1800,
    cwd: str | Path | None = None,
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> AgentSuiteResult:
    if repeat < 1:
        raise ValueError("repeat must be at least 1")

    root = Path(runs_root)
    task_run_root = root / FRONT_END_TASK_ID
    results: list[PipelineResult] = []
    for repeat_offset in range(repeat):
        current_seed = seed + repeat_offset
        run_label = f"{run_label_prefix}_{repeat_offset + 1:03d}_seed_{current_seed}"
        results.append(
            run_front_end_spread_widening_v0_agent_command(
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
                snapshot_date=snapshot_date,
                api_key=api_key,
                source_frame=source_frame,
            )
        )

    write_benchmark_reports_for_results(
        results=results,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
    )
    return AgentSuiteResult(results=results)


def run_usd_broad_direction_v0_agent_command(
    *,
    agent_id: str,
    agent_version: str,
    agent_command: str | list[str] | tuple[str, ...],
    seed: int = 37,
    task_path: str | Path = "tasks/pilot/usd_broad_direction_v0.yaml",
    data_output_dir: str | Path = "data/raw/usd_broad_direction_v0",
    private_dir: str | Path = "data/private/usd_broad_direction_v0",
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
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_usd_broad_direction_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    base_run_dir = run_dir or Path("runs") / USD_BROAD_TASK_ID / agent_id
    run_path = resolve_run_path(base_run_dir, run_label)
    run_path.mkdir(parents=True, exist_ok=True)

    command_result = run_agent_command(
        command=agent_command,
        env=usd_broad_agent_env(
            seed=seed,
            task_path=task_path,
            data_paths=data_paths,
            submission_dir=run_path,
        ),
        cwd=cwd,
        log_dir=run_path / "logs",
        timeout_seconds=command_timeout_seconds,
    )

    score = score_usd_broad_direction_submission(
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
        task_id=USD_BROAD_TASK_ID,
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
                "snapshot_date": snapshot_date,
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


def run_usd_broad_direction_v0_agent_command_suite(
    *,
    agent_id: str,
    agent_version: str,
    agent_command: str | list[str] | tuple[str, ...],
    seed: int = 37,
    repeat: int = 3,
    run_label_prefix: str = "agent",
    task_path: str | Path = "tasks/pilot/usd_broad_direction_v0.yaml",
    data_output_dir: str | Path = "data/raw/usd_broad_direction_v0",
    private_dir: str | Path = "data/private/usd_broad_direction_v0",
    runs_root: str | Path = DEFAULT_USD_BROAD_AGENT_SUITE_RUNS_ROOT,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command_timeout_seconds: int = 1800,
    cwd: str | Path | None = None,
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> AgentSuiteResult:
    if repeat < 1:
        raise ValueError("repeat must be at least 1")

    root = Path(runs_root)
    task_run_root = root / USD_BROAD_TASK_ID
    results: list[PipelineResult] = []
    for repeat_offset in range(repeat):
        current_seed = seed + repeat_offset
        run_label = f"{run_label_prefix}_{repeat_offset + 1:03d}_seed_{current_seed}"
        results.append(
            run_usd_broad_direction_v0_agent_command(
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
                snapshot_date=snapshot_date,
                api_key=api_key,
                source_frame=source_frame,
            )
        )

    write_benchmark_reports_for_results(
        results=results,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
    )
    return AgentSuiteResult(results=results)


def run_usd_afe_vs_eme_relative_direction_v0_agent_command(
    *,
    agent_id: str,
    agent_version: str,
    agent_command: str | list[str] | tuple[str, ...],
    seed: int = 41,
    task_path: str | Path = "tasks/pilot/usd_afe_vs_eme_relative_direction_v0.yaml",
    data_output_dir: str | Path = "data/raw/usd_afe_vs_eme_relative_direction_v0",
    private_dir: str | Path = "data/private/usd_afe_vs_eme_relative_direction_v0",
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
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> PipelineResult:
    data_paths = write_usd_relative_direction_task(
        output_dir=data_output_dir,
        private_dir=private_dir,
        api_key=api_key,
        snapshot_date=snapshot_date,
        source_frame=source_frame,
    )
    base_run_dir = run_dir or Path("runs") / USD_RELATIVE_TASK_ID / agent_id
    run_path = resolve_run_path(base_run_dir, run_label)
    run_path.mkdir(parents=True, exist_ok=True)

    command_result = run_agent_command(
        command=agent_command,
        env=usd_relative_agent_env(
            seed=seed,
            task_path=task_path,
            data_paths=data_paths,
            submission_dir=run_path,
        ),
        cwd=cwd,
        log_dir=run_path / "logs",
        timeout_seconds=command_timeout_seconds,
    )

    score = score_usd_afe_vs_eme_relative_submission(
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
        task_id=USD_RELATIVE_TASK_ID,
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
                "snapshot_date": snapshot_date,
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


def run_usd_afe_vs_eme_relative_direction_v0_agent_command_suite(
    *,
    agent_id: str,
    agent_version: str,
    agent_command: str | list[str] | tuple[str, ...],
    seed: int = 41,
    repeat: int = 3,
    run_label_prefix: str = "agent",
    task_path: str | Path = "tasks/pilot/usd_afe_vs_eme_relative_direction_v0.yaml",
    data_output_dir: str | Path = "data/raw/usd_afe_vs_eme_relative_direction_v0",
    private_dir: str | Path = "data/private/usd_afe_vs_eme_relative_direction_v0",
    runs_root: str | Path = DEFAULT_USD_RELATIVE_AGENT_SUITE_RUNS_ROOT,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command_timeout_seconds: int = 1800,
    cwd: str | Path | None = None,
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> AgentSuiteResult:
    if repeat < 1:
        raise ValueError("repeat must be at least 1")

    root = Path(runs_root)
    task_run_root = root / USD_RELATIVE_TASK_ID
    results: list[PipelineResult] = []
    for repeat_offset in range(repeat):
        current_seed = seed + repeat_offset
        run_label = f"{run_label_prefix}_{repeat_offset + 1:03d}_seed_{current_seed}"
        results.append(
            run_usd_afe_vs_eme_relative_direction_v0_agent_command(
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
                snapshot_date=snapshot_date,
                api_key=api_key,
                source_frame=source_frame,
            )
        )

    write_benchmark_reports_for_results(
        results=results,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
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

    write_benchmark_reports_for_results(
        results=results,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
    )
    return BaselineSuiteResult(results=results)


def run_yield_direction_treasury10y_baseline_suite(
    *,
    seed: int = 29,
    repeat: int = 3,
    baselines: list[str] | tuple[str, ...] | None = None,
    run_label_prefix: str = "pilot",
    task_path: str | Path = "tasks/pilot/yield_direction_treasury10y_v0.yaml",
    data_output_dir: str | Path = "data/raw/yield_direction_treasury10y_v0",
    private_dir: str | Path = "data/private/yield_direction_treasury10y_v0",
    runs_root: str | Path = DEFAULT_TREASURY_SUITE_RUNS_ROOT,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_yield_direction_treasury10y_baseline_suite",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> BaselineSuiteResult:
    if repeat < 1:
        raise ValueError("repeat must be at least 1")

    selected_baselines = tuple(baselines or DEFAULT_TREASURY_BASELINES)
    unknown_baselines = sorted(set(selected_baselines) - set(DEFAULT_TREASURY_BASELINES))
    if unknown_baselines:
        raise ValueError(f"Unknown baselines: {unknown_baselines}")

    root = Path(runs_root)
    task_run_root = root / TREASURY_TASK_ID
    results: list[PipelineResult] = []
    for repeat_offset in range(repeat):
        current_seed = seed + repeat_offset
        run_label = f"{run_label_prefix}_{repeat_offset + 1:03d}_seed_{current_seed}"
        repeat_data_dir = Path(data_output_dir) / run_label
        repeat_private_dir = Path(private_dir) / run_label

        if PREVIOUS_DAY_DIRECTION_BASELINE_ID in selected_baselines:
            results.append(
                run_yield_direction_treasury10y_previous_day_pipeline(
                    seed=current_seed,
                    task_path=task_path,
                    data_output_dir=repeat_data_dir,
                    private_dir=repeat_private_dir,
                    run_dir=task_run_root / PREVIOUS_DAY_DIRECTION_BASELINE_ID,
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
                    snapshot_date=snapshot_date,
                    api_key=api_key,
                    source_frame=source_frame,
                )
            )

        if LOGISTIC_BASELINE_ID in selected_baselines:
            results.append(
                run_yield_direction_treasury10y_logistic_pipeline(
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
                    snapshot_date=snapshot_date,
                    api_key=api_key,
                    source_frame=source_frame,
                )
            )

        if RANDOM_FOREST_BASELINE_ID in selected_baselines:
            results.append(
                run_yield_direction_treasury10y_random_forest_pipeline(
                    seed=current_seed,
                    task_path=task_path,
                    data_output_dir=repeat_data_dir,
                    private_dir=repeat_private_dir,
                    run_dir=task_run_root / RANDOM_FOREST_BASELINE_ID,
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
                    snapshot_date=snapshot_date,
                    api_key=api_key,
                    source_frame=source_frame,
                )
            )

        if EXTRA_TREES_BASELINE_ID in selected_baselines:
            results.append(
                run_yield_direction_treasury10y_extra_trees_pipeline(
                    seed=current_seed,
                    task_path=task_path,
                    data_output_dir=repeat_data_dir,
                    private_dir=repeat_private_dir,
                    run_dir=task_run_root / EXTRA_TREES_BASELINE_ID,
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
                    snapshot_date=snapshot_date,
                    api_key=api_key,
                    source_frame=source_frame,
                )
            )

    write_benchmark_reports_for_results(
        results=results,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
    )
    return BaselineSuiteResult(results=results)


def run_yield_curve_10y2y_steepening_baseline_suite(
    *,
    seed: int = 29,
    repeat: int = 3,
    baselines: list[str] | tuple[str, ...] | None = None,
    run_label_prefix: str = "pilot",
    task_path: str | Path = "tasks/pilot/yield_curve_10y2y_steepening_v0.yaml",
    data_output_dir: str | Path = "data/raw/yield_curve_10y2y_steepening_v0",
    private_dir: str | Path = "data/private/yield_curve_10y2y_steepening_v0",
    runs_root: str | Path = DEFAULT_TREASURY_CURVE_SUITE_RUNS_ROOT,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_yield_curve_10y2y_steepening_baseline_suite",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> BaselineSuiteResult:
    if repeat < 1:
        raise ValueError("repeat must be at least 1")

    selected_baselines = tuple(baselines or DEFAULT_TREASURY_BASELINES)
    unknown_baselines = sorted(set(selected_baselines) - set(DEFAULT_TREASURY_BASELINES))
    if unknown_baselines:
        raise ValueError(f"Unknown baselines: {unknown_baselines}")

    root = Path(runs_root)
    task_run_root = root / TREASURY_CURVE_TASK_ID
    results: list[PipelineResult] = []
    for repeat_offset in range(repeat):
        current_seed = seed + repeat_offset
        run_label = f"{run_label_prefix}_{repeat_offset + 1:03d}_seed_{current_seed}"
        repeat_data_dir = Path(data_output_dir) / run_label
        repeat_private_dir = Path(private_dir) / run_label

        if PREVIOUS_DAY_DIRECTION_BASELINE_ID in selected_baselines:
            results.append(
                run_yield_curve_10y2y_steepening_previous_day_pipeline(
                    seed=current_seed,
                    task_path=task_path,
                    data_output_dir=repeat_data_dir,
                    private_dir=repeat_private_dir,
                    run_dir=task_run_root / PREVIOUS_DAY_DIRECTION_BASELINE_ID,
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
                    snapshot_date=snapshot_date,
                    api_key=api_key,
                    source_frame=source_frame,
                )
            )

        if LOGISTIC_BASELINE_ID in selected_baselines:
            results.append(
                run_yield_curve_10y2y_steepening_logistic_pipeline(
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
                    snapshot_date=snapshot_date,
                    api_key=api_key,
                    source_frame=source_frame,
                )
            )

        if RANDOM_FOREST_BASELINE_ID in selected_baselines:
            results.append(
                run_yield_curve_10y2y_steepening_random_forest_pipeline(
                    seed=current_seed,
                    task_path=task_path,
                    data_output_dir=repeat_data_dir,
                    private_dir=repeat_private_dir,
                    run_dir=task_run_root / RANDOM_FOREST_BASELINE_ID,
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
                    snapshot_date=snapshot_date,
                    api_key=api_key,
                    source_frame=source_frame,
                )
            )

        if EXTRA_TREES_BASELINE_ID in selected_baselines:
            results.append(
                run_yield_curve_10y2y_steepening_extra_trees_pipeline(
                    seed=current_seed,
                    task_path=task_path,
                    data_output_dir=repeat_data_dir,
                    private_dir=repeat_private_dir,
                    run_dir=task_run_root / EXTRA_TREES_BASELINE_ID,
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
                    snapshot_date=snapshot_date,
                    api_key=api_key,
                    source_frame=source_frame,
                )
            )

    write_benchmark_reports_for_results(
        results=results,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
    )
    return BaselineSuiteResult(results=results)


def run_yield_curve_10y3mo_steepening_baseline_suite(
    *,
    seed: int = 29,
    repeat: int = 3,
    baselines: list[str] | tuple[str, ...] | None = None,
    run_label_prefix: str = "pilot",
    task_path: str | Path = "tasks/pilot/yield_curve_10y3mo_steepening_v0.yaml",
    data_output_dir: str | Path = "data/raw/yield_curve_10y3mo_steepening_v0",
    private_dir: str | Path = "data/private/yield_curve_10y3mo_steepening_v0",
    runs_root: str | Path = DEFAULT_TREASURY_CURVE_10Y3MO_SUITE_RUNS_ROOT,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_yield_curve_10y3mo_steepening_baseline_suite",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> BaselineSuiteResult:
    if repeat < 1:
        raise ValueError("repeat must be at least 1")

    selected_baselines = tuple(baselines or DEFAULT_TREASURY_BASELINES)
    unknown_baselines = sorted(set(selected_baselines) - set(DEFAULT_TREASURY_BASELINES))
    if unknown_baselines:
        raise ValueError(f"Unknown baselines: {unknown_baselines}")

    root = Path(runs_root)
    task_run_root = root / TREASURY_CURVE_10Y3MO_TASK_ID
    results: list[PipelineResult] = []
    for repeat_offset in range(repeat):
        current_seed = seed + repeat_offset
        run_label = f"{run_label_prefix}_{repeat_offset + 1:03d}_seed_{current_seed}"
        repeat_data_dir = Path(data_output_dir) / run_label
        repeat_private_dir = Path(private_dir) / run_label

        if PREVIOUS_DAY_DIRECTION_BASELINE_ID in selected_baselines:
            results.append(
                run_yield_curve_10y3mo_steepening_previous_day_pipeline(
                    seed=current_seed,
                    task_path=task_path,
                    data_output_dir=repeat_data_dir,
                    private_dir=repeat_private_dir,
                    run_dir=task_run_root / PREVIOUS_DAY_DIRECTION_BASELINE_ID,
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
                    snapshot_date=snapshot_date,
                    api_key=api_key,
                    source_frame=source_frame,
                )
            )

        if LOGISTIC_BASELINE_ID in selected_baselines:
            results.append(
                run_yield_curve_10y3mo_steepening_logistic_pipeline(
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
                    snapshot_date=snapshot_date,
                    api_key=api_key,
                    source_frame=source_frame,
                )
            )

        if RANDOM_FOREST_BASELINE_ID in selected_baselines:
            results.append(
                run_yield_curve_10y3mo_steepening_random_forest_pipeline(
                    seed=current_seed,
                    task_path=task_path,
                    data_output_dir=repeat_data_dir,
                    private_dir=repeat_private_dir,
                    run_dir=task_run_root / RANDOM_FOREST_BASELINE_ID,
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
                    snapshot_date=snapshot_date,
                    api_key=api_key,
                    source_frame=source_frame,
                )
            )

        if EXTRA_TREES_BASELINE_ID in selected_baselines:
            results.append(
                run_yield_curve_10y3mo_steepening_extra_trees_pipeline(
                    seed=current_seed,
                    task_path=task_path,
                    data_output_dir=repeat_data_dir,
                    private_dir=repeat_private_dir,
                    run_dir=task_run_root / EXTRA_TREES_BASELINE_ID,
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
                    snapshot_date=snapshot_date,
                    api_key=api_key,
                    source_frame=source_frame,
                )
            )

    write_benchmark_reports_for_results(
        results=results,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
    )
    return BaselineSuiteResult(results=results)


def run_front_end_spread_widening_v0_baseline_suite(
    *,
    seed: int = 31,
    repeat: int = 3,
    baselines: list[str] | tuple[str, ...] | None = None,
    run_label_prefix: str = "pilot",
    task_path: str | Path = "tasks/pilot/front_end_spread_widening_v0.yaml",
    data_output_dir: str | Path = "data/raw/front_end_spread_widening_v0",
    private_dir: str | Path = "data/private/front_end_spread_widening_v0",
    runs_root: str | Path = DEFAULT_FRONT_END_SUITE_RUNS_ROOT,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_front_end_spread_widening_v0_baseline_suite",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> BaselineSuiteResult:
    if repeat < 1:
        raise ValueError("repeat must be at least 1")

    selected_baselines = tuple(baselines or DEFAULT_TREASURY_BASELINES)
    unknown_baselines = sorted(set(selected_baselines) - set(DEFAULT_TREASURY_BASELINES))
    if unknown_baselines:
        raise ValueError(f"Unknown baselines: {unknown_baselines}")

    root = Path(runs_root)
    task_run_root = root / FRONT_END_TASK_ID
    results: list[PipelineResult] = []
    for repeat_offset in range(repeat):
        current_seed = seed + repeat_offset
        run_label = f"{run_label_prefix}_{repeat_offset + 1:03d}_seed_{current_seed}"
        repeat_data_dir = Path(data_output_dir) / run_label
        repeat_private_dir = Path(private_dir) / run_label

        if PREVIOUS_DAY_DIRECTION_BASELINE_ID in selected_baselines:
            results.append(
                run_front_end_spread_widening_v0_previous_day_pipeline(
                    seed=current_seed,
                    task_path=task_path,
                    data_output_dir=repeat_data_dir,
                    private_dir=repeat_private_dir,
                    run_dir=task_run_root / PREVIOUS_DAY_DIRECTION_BASELINE_ID,
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
                    snapshot_date=snapshot_date,
                    api_key=api_key,
                    source_frame=source_frame,
                )
            )

        if LOGISTIC_BASELINE_ID in selected_baselines:
            results.append(
                run_front_end_spread_widening_v0_logistic_pipeline(
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
                    snapshot_date=snapshot_date,
                    api_key=api_key,
                    source_frame=source_frame,
                )
            )

        if RANDOM_FOREST_BASELINE_ID in selected_baselines:
            results.append(
                run_front_end_spread_widening_v0_random_forest_pipeline(
                    seed=current_seed,
                    task_path=task_path,
                    data_output_dir=repeat_data_dir,
                    private_dir=repeat_private_dir,
                    run_dir=task_run_root / RANDOM_FOREST_BASELINE_ID,
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
                    snapshot_date=snapshot_date,
                    api_key=api_key,
                    source_frame=source_frame,
                )
            )

        if EXTRA_TREES_BASELINE_ID in selected_baselines:
            results.append(
                run_front_end_spread_widening_v0_extra_trees_pipeline(
                    seed=current_seed,
                    task_path=task_path,
                    data_output_dir=repeat_data_dir,
                    private_dir=repeat_private_dir,
                    run_dir=task_run_root / EXTRA_TREES_BASELINE_ID,
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
                    snapshot_date=snapshot_date,
                    api_key=api_key,
                    source_frame=source_frame,
                )
            )

    write_benchmark_reports_for_results(
        results=results,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
    )
    return BaselineSuiteResult(results=results)


def run_usd_broad_direction_v0_baseline_suite(
    *,
    seed: int = 37,
    repeat: int = 3,
    baselines: list[str] | tuple[str, ...] | None = None,
    run_label_prefix: str = "pilot",
    task_path: str | Path = "tasks/pilot/usd_broad_direction_v0.yaml",
    data_output_dir: str | Path = "data/raw/usd_broad_direction_v0",
    private_dir: str | Path = "data/private/usd_broad_direction_v0",
    runs_root: str | Path = DEFAULT_USD_BROAD_SUITE_RUNS_ROOT,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_usd_broad_direction_v0_baseline_suite",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> BaselineSuiteResult:
    if repeat < 1:
        raise ValueError("repeat must be at least 1")

    selected_baselines = tuple(baselines or DEFAULT_TREASURY_BASELINES)
    unknown_baselines = sorted(set(selected_baselines) - set(DEFAULT_TREASURY_BASELINES))
    if unknown_baselines:
        raise ValueError(f"Unknown baselines: {unknown_baselines}")

    root = Path(runs_root)
    task_run_root = root / USD_BROAD_TASK_ID
    results: list[PipelineResult] = []
    for repeat_offset in range(repeat):
        current_seed = seed + repeat_offset
        run_label = f"{run_label_prefix}_{repeat_offset + 1:03d}_seed_{current_seed}"
        repeat_data_dir = Path(data_output_dir) / run_label
        repeat_private_dir = Path(private_dir) / run_label

        if PREVIOUS_DAY_DIRECTION_BASELINE_ID in selected_baselines:
            results.append(
                run_usd_broad_direction_v0_previous_day_pipeline(
                    seed=current_seed,
                    task_path=task_path,
                    data_output_dir=repeat_data_dir,
                    private_dir=repeat_private_dir,
                    run_dir=task_run_root / PREVIOUS_DAY_DIRECTION_BASELINE_ID,
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
                    snapshot_date=snapshot_date,
                    api_key=api_key,
                    source_frame=source_frame,
                )
            )

        if LOGISTIC_BASELINE_ID in selected_baselines:
            results.append(
                run_usd_broad_direction_v0_logistic_pipeline(
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
                    snapshot_date=snapshot_date,
                    api_key=api_key,
                    source_frame=source_frame,
                )
            )

        if RANDOM_FOREST_BASELINE_ID in selected_baselines:
            results.append(
                run_usd_broad_direction_v0_random_forest_pipeline(
                    seed=current_seed,
                    task_path=task_path,
                    data_output_dir=repeat_data_dir,
                    private_dir=repeat_private_dir,
                    run_dir=task_run_root / RANDOM_FOREST_BASELINE_ID,
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
                    snapshot_date=snapshot_date,
                    api_key=api_key,
                    source_frame=source_frame,
                )
            )

        if EXTRA_TREES_BASELINE_ID in selected_baselines:
            results.append(
                run_usd_broad_direction_v0_extra_trees_pipeline(
                    seed=current_seed,
                    task_path=task_path,
                    data_output_dir=repeat_data_dir,
                    private_dir=repeat_private_dir,
                    run_dir=task_run_root / EXTRA_TREES_BASELINE_ID,
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
                    snapshot_date=snapshot_date,
                    api_key=api_key,
                    source_frame=source_frame,
                )
            )

    write_benchmark_reports_for_results(
        results=results,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
    )
    return BaselineSuiteResult(results=results)


def run_usd_afe_vs_eme_relative_direction_v0_baseline_suite(
    *,
    seed: int = 41,
    repeat: int = 3,
    baselines: list[str] | tuple[str, ...] | None = None,
    run_label_prefix: str = "pilot",
    task_path: str | Path = "tasks/pilot/usd_afe_vs_eme_relative_direction_v0.yaml",
    data_output_dir: str | Path = "data/raw/usd_afe_vs_eme_relative_direction_v0",
    private_dir: str | Path = "data/private/usd_afe_vs_eme_relative_direction_v0",
    runs_root: str | Path = DEFAULT_USD_RELATIVE_SUITE_RUNS_ROOT,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_usd_afe_vs_eme_relative_direction_v0_baseline_suite",
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    api_key: str | None = None,
    source_frame: Any | None = None,
) -> BaselineSuiteResult:
    if repeat < 1:
        raise ValueError("repeat must be at least 1")

    selected_baselines = tuple(baselines or DEFAULT_TREASURY_BASELINES)
    unknown_baselines = sorted(set(selected_baselines) - set(DEFAULT_TREASURY_BASELINES))
    if unknown_baselines:
        raise ValueError(f"Unknown baselines: {unknown_baselines}")

    root = Path(runs_root)
    task_run_root = root / USD_RELATIVE_TASK_ID
    results: list[PipelineResult] = []
    for repeat_offset in range(repeat):
        current_seed = seed + repeat_offset
        run_label = f"{run_label_prefix}_{repeat_offset + 1:03d}_seed_{current_seed}"
        repeat_data_dir = Path(data_output_dir) / run_label
        repeat_private_dir = Path(private_dir) / run_label

        if PREVIOUS_DAY_DIRECTION_BASELINE_ID in selected_baselines:
            results.append(
                run_usd_afe_vs_eme_relative_direction_v0_previous_day_pipeline(
                    seed=current_seed,
                    task_path=task_path,
                    data_output_dir=repeat_data_dir,
                    private_dir=repeat_private_dir,
                    run_dir=task_run_root / PREVIOUS_DAY_DIRECTION_BASELINE_ID,
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
                    snapshot_date=snapshot_date,
                    api_key=api_key,
                    source_frame=source_frame,
                )
            )

        if LOGISTIC_BASELINE_ID in selected_baselines:
            results.append(
                run_usd_afe_vs_eme_relative_direction_v0_logistic_pipeline(
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
                    snapshot_date=snapshot_date,
                    api_key=api_key,
                    source_frame=source_frame,
                )
            )

        if RANDOM_FOREST_BASELINE_ID in selected_baselines:
            results.append(
                run_usd_afe_vs_eme_relative_direction_v0_random_forest_pipeline(
                    seed=current_seed,
                    task_path=task_path,
                    data_output_dir=repeat_data_dir,
                    private_dir=repeat_private_dir,
                    run_dir=task_run_root / RANDOM_FOREST_BASELINE_ID,
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
                    snapshot_date=snapshot_date,
                    api_key=api_key,
                    source_frame=source_frame,
                )
            )

        if EXTRA_TREES_BASELINE_ID in selected_baselines:
            results.append(
                run_usd_afe_vs_eme_relative_direction_v0_extra_trees_pipeline(
                    seed=current_seed,
                    task_path=task_path,
                    data_output_dir=repeat_data_dir,
                    private_dir=repeat_private_dir,
                    run_dir=task_run_root / EXTRA_TREES_BASELINE_ID,
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
                    snapshot_date=snapshot_date,
                    api_key=api_key,
                    source_frame=source_frame,
                )
            )

    write_benchmark_reports_for_results(
        results=results,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
    )
    return BaselineSuiteResult(results=results)


def run_pilot_baseline_suite(
    *,
    market_seed: int = 11,
    event_seed: int = 23,
    treasury_seed: int = 29,
    curve_seed: int = 31,
    curve3mo_seed: int = 33,
    front_end_seed: int = 31,
    usd_seed: int = 37,
    repeat: int = 3,
    run_label_prefix: str = "pilot",
    market_task_path: str | Path = "tasks/pilot/synthetic_market_direction_v0.yaml",
    event_task_path: str | Path = "tasks/pilot/synthetic_event_response_v0.yaml",
    treasury_task_path: str | Path = "tasks/pilot/yield_direction_treasury10y_v0.yaml",
    curve_task_path: str | Path = "tasks/pilot/yield_curve_10y2y_steepening_v0.yaml",
    curve3mo_task_path: str | Path = "tasks/pilot/yield_curve_10y3mo_steepening_v0.yaml",
    front_end_task_path: str | Path = "tasks/pilot/front_end_spread_widening_v0.yaml",
    usd_task_path: str | Path = "tasks/pilot/usd_broad_direction_v0.yaml",
    usd_relative_task_path: str | Path = "tasks/pilot/usd_afe_vs_eme_relative_direction_v0.yaml",
    market_data_output_dir: str | Path = "data/raw/synthetic_market_direction_v0",
    market_private_dir: str | Path = "data/private/synthetic_market_direction_v0",
    event_data_output_dir: str | Path = "data/raw/synthetic_event_response_v0",
    event_private_dir: str | Path = "data/private/synthetic_event_response_v0",
    treasury_data_output_dir: str | Path = "data/raw/yield_direction_treasury10y_v0",
    treasury_private_dir: str | Path = "data/private/yield_direction_treasury10y_v0",
    curve_data_output_dir: str | Path = "data/raw/yield_curve_10y2y_steepening_v0",
    curve_private_dir: str | Path = "data/private/yield_curve_10y2y_steepening_v0",
    curve3mo_data_output_dir: str | Path = "data/raw/yield_curve_10y3mo_steepening_v0",
    curve3mo_private_dir: str | Path = "data/private/yield_curve_10y3mo_steepening_v0",
    front_end_data_output_dir: str | Path = "data/raw/front_end_spread_widening_v0",
    front_end_private_dir: str | Path = "data/private/front_end_spread_widening_v0",
    usd_data_output_dir: str | Path = "data/raw/usd_broad_direction_v0",
    usd_private_dir: str | Path = "data/private/usd_broad_direction_v0",
    usd_relative_data_output_dir: str | Path = "data/raw/usd_afe_vs_eme_relative_direction_v0",
    usd_relative_private_dir: str | Path = "data/private/usd_afe_vs_eme_relative_direction_v0",
    runs_root: str | Path = DEFAULT_PILOT_BASELINE_SUITE_RUNS_ROOT,
    clean_existing_runs: bool = False,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command: str = "run_pilot_baseline_suite",
    treasury_snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    treasury_api_key: str | None = None,
    treasury_source_frame: Any | None = None,
    curve_snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    curve_api_key: str | None = None,
    curve_source_frame: Any | None = None,
    curve3mo_snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    curve3mo_api_key: str | None = None,
    curve3mo_source_frame: Any | None = None,
    front_end_snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    front_end_api_key: str | None = None,
    front_end_source_frame: Any | None = None,
    usd_snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    usd_api_key: str | None = None,
    usd_source_frame: Any | None = None,
) -> BaselineSuiteResult:
    if repeat < 1:
        raise ValueError("repeat must be at least 1")

    root = Path(runs_root)
    if clean_existing_runs:
        remove_output_path(root)
        clear_benchmark_report_outputs(
            report_csv_path=report_csv_path,
            report_markdown_path=report_markdown_path,
            summary_csv_path=summary_csv_path,
            summary_markdown_path=summary_markdown_path,
        )
    market_run_root = root / SYNTHETIC_MARKET_TASK_ID
    event_run_root = root / SYNTHETIC_EVENT_TASK_ID
    treasury_run_root = root / TREASURY_TASK_ID
    curve_run_root = root / TREASURY_CURVE_TASK_ID
    curve3mo_run_root = root / TREASURY_CURVE_10Y3MO_TASK_ID
    front_end_run_root = root / FRONT_END_TASK_ID
    usd_run_root = root / USD_BROAD_TASK_ID
    usd_relative_run_root = root / USD_RELATIVE_TASK_ID
    results: list[PipelineResult] = []

    for repeat_offset in range(repeat):
        repeat_index = repeat_offset + 1
        current_market_seed = market_seed + repeat_offset
        current_event_seed = event_seed + repeat_offset
        current_treasury_seed = treasury_seed + repeat_offset
        current_curve_seed = curve_seed + repeat_offset
        current_curve3mo_seed = curve3mo_seed + repeat_offset
        current_front_end_seed = front_end_seed + repeat_offset
        current_usd_seed = usd_seed + repeat_offset
        market_label = f"{run_label_prefix}_market_{repeat_index:03d}_seed_{current_market_seed}"
        event_label = f"{run_label_prefix}_event_{repeat_index:03d}_seed_{current_event_seed}"
        treasury_label = (
            f"{run_label_prefix}_treasury_{repeat_index:03d}_seed_{current_treasury_seed}"
        )
        curve_label = f"{run_label_prefix}_curve_{repeat_index:03d}_seed_{current_curve_seed}"
        curve3mo_label = (
            f"{run_label_prefix}_curve3mo_{repeat_index:03d}_seed_{current_curve3mo_seed}"
        )
        front_end_label = (
            f"{run_label_prefix}_front_end_{repeat_index:03d}_seed_{current_front_end_seed}"
        )
        usd_label = f"{run_label_prefix}_usd_{repeat_index:03d}_seed_{current_usd_seed}"
        usd_relative_label = (
            f"{run_label_prefix}_usd_relative_{repeat_index:03d}_seed_{current_usd_seed}"
        )

        results.append(
            run_synthetic_market_momentum_pipeline(
                seed=current_market_seed,
                task_path=market_task_path,
                data_output_dir=Path(market_data_output_dir) / market_label,
                private_dir=Path(market_private_dir) / market_label,
                run_dir=market_run_root / MOMENTUM_BASELINE_ID,
                run_label=market_label,
                repeat_index=repeat_index,
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
        results.append(
            run_synthetic_market_logistic_pipeline(
                seed=current_market_seed,
                task_path=market_task_path,
                data_output_dir=Path(market_data_output_dir) / market_label,
                private_dir=Path(market_private_dir) / market_label,
                run_dir=market_run_root / LOGISTIC_BASELINE_ID,
                run_label=market_label,
                repeat_index=repeat_index,
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
        results.append(
            run_synthetic_event_response_rule_pipeline(
                seed=current_event_seed,
                task_path=event_task_path,
                data_output_dir=Path(event_data_output_dir) / event_label,
                private_dir=Path(event_private_dir) / event_label,
                run_dir=event_run_root / EVENT_RULE_BASELINE_ID,
                run_label=event_label,
                repeat_index=repeat_index,
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
        results.append(
            run_yield_direction_treasury10y_previous_day_pipeline(
                seed=current_treasury_seed,
                task_path=treasury_task_path,
                data_output_dir=Path(treasury_data_output_dir) / treasury_label,
                private_dir=Path(treasury_private_dir) / treasury_label,
                run_dir=treasury_run_root / PREVIOUS_DAY_DIRECTION_BASELINE_ID,
                run_label=treasury_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command=command,
                snapshot_date=treasury_snapshot_date,
                api_key=treasury_api_key,
                source_frame=treasury_source_frame,
            )
        )
        results.append(
            run_yield_direction_treasury10y_logistic_pipeline(
                seed=current_treasury_seed,
                task_path=treasury_task_path,
                data_output_dir=Path(treasury_data_output_dir) / treasury_label,
                private_dir=Path(treasury_private_dir) / treasury_label,
                run_dir=treasury_run_root / LOGISTIC_BASELINE_ID,
                run_label=treasury_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command=command,
                snapshot_date=treasury_snapshot_date,
                api_key=treasury_api_key,
                source_frame=treasury_source_frame,
            )
        )
        results.append(
            run_yield_direction_treasury10y_random_forest_pipeline(
                seed=current_treasury_seed,
                task_path=treasury_task_path,
                data_output_dir=Path(treasury_data_output_dir) / treasury_label,
                private_dir=Path(treasury_private_dir) / treasury_label,
                run_dir=treasury_run_root / RANDOM_FOREST_BASELINE_ID,
                run_label=treasury_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command=command,
                snapshot_date=treasury_snapshot_date,
                api_key=treasury_api_key,
                source_frame=treasury_source_frame,
            )
        )
        results.append(
            run_yield_direction_treasury10y_extra_trees_pipeline(
                seed=current_treasury_seed,
                task_path=treasury_task_path,
                data_output_dir=Path(treasury_data_output_dir) / treasury_label,
                private_dir=Path(treasury_private_dir) / treasury_label,
                run_dir=treasury_run_root / EXTRA_TREES_BASELINE_ID,
                run_label=treasury_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command=command,
                snapshot_date=treasury_snapshot_date,
                api_key=treasury_api_key,
                source_frame=treasury_source_frame,
            )
        )
        results.append(
            run_yield_curve_10y2y_steepening_previous_day_pipeline(
                seed=current_curve_seed,
                task_path=curve_task_path,
                data_output_dir=Path(curve_data_output_dir) / curve_label,
                private_dir=Path(curve_private_dir) / curve_label,
                run_dir=curve_run_root / PREVIOUS_DAY_DIRECTION_BASELINE_ID,
                run_label=curve_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command=command,
                snapshot_date=curve_snapshot_date,
                api_key=curve_api_key,
                source_frame=curve_source_frame if curve_source_frame is not None else treasury_source_frame,
            )
        )
        results.append(
            run_yield_curve_10y2y_steepening_logistic_pipeline(
                seed=current_curve_seed,
                task_path=curve_task_path,
                data_output_dir=Path(curve_data_output_dir) / curve_label,
                private_dir=Path(curve_private_dir) / curve_label,
                run_dir=curve_run_root / LOGISTIC_BASELINE_ID,
                run_label=curve_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command=command,
                snapshot_date=curve_snapshot_date,
                api_key=curve_api_key,
                source_frame=curve_source_frame if curve_source_frame is not None else treasury_source_frame,
            )
        )
        results.append(
            run_yield_curve_10y2y_steepening_random_forest_pipeline(
                seed=current_curve_seed,
                task_path=curve_task_path,
                data_output_dir=Path(curve_data_output_dir) / curve_label,
                private_dir=Path(curve_private_dir) / curve_label,
                run_dir=curve_run_root / RANDOM_FOREST_BASELINE_ID,
                run_label=curve_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command=command,
                snapshot_date=curve_snapshot_date,
                api_key=curve_api_key,
                source_frame=curve_source_frame if curve_source_frame is not None else treasury_source_frame,
            )
        )
        results.append(
            run_yield_curve_10y2y_steepening_extra_trees_pipeline(
                seed=current_curve_seed,
                task_path=curve_task_path,
                data_output_dir=Path(curve_data_output_dir) / curve_label,
                private_dir=Path(curve_private_dir) / curve_label,
                run_dir=curve_run_root / EXTRA_TREES_BASELINE_ID,
                run_label=curve_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command=command,
                snapshot_date=curve_snapshot_date,
                api_key=curve_api_key,
                source_frame=curve_source_frame if curve_source_frame is not None else treasury_source_frame,
            )
        )
        results.append(
            run_yield_curve_10y3mo_steepening_previous_day_pipeline(
                seed=current_curve3mo_seed,
                task_path=curve3mo_task_path,
                data_output_dir=Path(curve3mo_data_output_dir) / curve3mo_label,
                private_dir=Path(curve3mo_private_dir) / curve3mo_label,
                run_dir=curve3mo_run_root / PREVIOUS_DAY_DIRECTION_BASELINE_ID,
                run_label=curve3mo_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command=command,
                snapshot_date=curve3mo_snapshot_date,
                api_key=curve3mo_api_key,
                source_frame=(
                    curve3mo_source_frame
                    if curve3mo_source_frame is not None
                    else treasury_source_frame
                ),
            )
        )
        results.append(
            run_yield_curve_10y3mo_steepening_logistic_pipeline(
                seed=current_curve3mo_seed,
                task_path=curve3mo_task_path,
                data_output_dir=Path(curve3mo_data_output_dir) / curve3mo_label,
                private_dir=Path(curve3mo_private_dir) / curve3mo_label,
                run_dir=curve3mo_run_root / LOGISTIC_BASELINE_ID,
                run_label=curve3mo_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command=command,
                snapshot_date=curve3mo_snapshot_date,
                api_key=curve3mo_api_key,
                source_frame=(
                    curve3mo_source_frame
                    if curve3mo_source_frame is not None
                    else treasury_source_frame
                ),
            )
        )
        results.append(
            run_yield_curve_10y3mo_steepening_random_forest_pipeline(
                seed=current_curve3mo_seed,
                task_path=curve3mo_task_path,
                data_output_dir=Path(curve3mo_data_output_dir) / curve3mo_label,
                private_dir=Path(curve3mo_private_dir) / curve3mo_label,
                run_dir=curve3mo_run_root / RANDOM_FOREST_BASELINE_ID,
                run_label=curve3mo_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command=command,
                snapshot_date=curve3mo_snapshot_date,
                api_key=curve3mo_api_key,
                source_frame=(
                    curve3mo_source_frame
                    if curve3mo_source_frame is not None
                    else treasury_source_frame
                ),
            )
        )
        results.append(
            run_yield_curve_10y3mo_steepening_extra_trees_pipeline(
                seed=current_curve3mo_seed,
                task_path=curve3mo_task_path,
                data_output_dir=Path(curve3mo_data_output_dir) / curve3mo_label,
                private_dir=Path(curve3mo_private_dir) / curve3mo_label,
                run_dir=curve3mo_run_root / EXTRA_TREES_BASELINE_ID,
                run_label=curve3mo_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command=command,
                snapshot_date=curve3mo_snapshot_date,
                api_key=curve3mo_api_key,
                source_frame=(
                    curve3mo_source_frame
                    if curve3mo_source_frame is not None
                    else treasury_source_frame
                ),
            )
        )
        results.append(
            run_front_end_spread_widening_v0_previous_day_pipeline(
                seed=current_front_end_seed,
                task_path=front_end_task_path,
                data_output_dir=Path(front_end_data_output_dir) / front_end_label,
                private_dir=Path(front_end_private_dir) / front_end_label,
                run_dir=front_end_run_root / PREVIOUS_DAY_DIRECTION_BASELINE_ID,
                run_label=front_end_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command=command,
                snapshot_date=front_end_snapshot_date,
                api_key=front_end_api_key,
                source_frame=(
                    front_end_source_frame
                    if front_end_source_frame is not None
                    else treasury_source_frame
                ),
            )
        )
        results.append(
            run_front_end_spread_widening_v0_logistic_pipeline(
                seed=current_front_end_seed,
                task_path=front_end_task_path,
                data_output_dir=Path(front_end_data_output_dir) / front_end_label,
                private_dir=Path(front_end_private_dir) / front_end_label,
                run_dir=front_end_run_root / LOGISTIC_BASELINE_ID,
                run_label=front_end_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command=command,
                snapshot_date=front_end_snapshot_date,
                api_key=front_end_api_key,
                source_frame=(
                    front_end_source_frame
                    if front_end_source_frame is not None
                    else treasury_source_frame
                ),
            )
        )
        results.append(
            run_front_end_spread_widening_v0_random_forest_pipeline(
                seed=current_front_end_seed,
                task_path=front_end_task_path,
                data_output_dir=Path(front_end_data_output_dir) / front_end_label,
                private_dir=Path(front_end_private_dir) / front_end_label,
                run_dir=front_end_run_root / RANDOM_FOREST_BASELINE_ID,
                run_label=front_end_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command=command,
                snapshot_date=front_end_snapshot_date,
                api_key=front_end_api_key,
                source_frame=(
                    front_end_source_frame
                    if front_end_source_frame is not None
                    else treasury_source_frame
                ),
            )
        )
        results.append(
            run_front_end_spread_widening_v0_extra_trees_pipeline(
                seed=current_front_end_seed,
                task_path=front_end_task_path,
                data_output_dir=Path(front_end_data_output_dir) / front_end_label,
                private_dir=Path(front_end_private_dir) / front_end_label,
                run_dir=front_end_run_root / EXTRA_TREES_BASELINE_ID,
                run_label=front_end_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command=command,
                snapshot_date=front_end_snapshot_date,
                api_key=front_end_api_key,
                source_frame=(
                    front_end_source_frame
                    if front_end_source_frame is not None
                    else treasury_source_frame
                ),
            )
        )
        results.append(
            run_usd_broad_direction_v0_previous_day_pipeline(
                seed=current_usd_seed,
                task_path=usd_task_path,
                data_output_dir=Path(usd_data_output_dir) / usd_label,
                private_dir=Path(usd_private_dir) / usd_label,
                run_dir=usd_run_root / PREVIOUS_DAY_DIRECTION_BASELINE_ID,
                run_label=usd_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command=command,
                snapshot_date=usd_snapshot_date,
                api_key=usd_api_key,
                source_frame=usd_source_frame,
            )
        )
        results.append(
            run_usd_broad_direction_v0_logistic_pipeline(
                seed=current_usd_seed,
                task_path=usd_task_path,
                data_output_dir=Path(usd_data_output_dir) / usd_label,
                private_dir=Path(usd_private_dir) / usd_label,
                run_dir=usd_run_root / LOGISTIC_BASELINE_ID,
                run_label=usd_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command=command,
                snapshot_date=usd_snapshot_date,
                api_key=usd_api_key,
                source_frame=usd_source_frame,
            )
        )
        results.append(
            run_usd_broad_direction_v0_random_forest_pipeline(
                seed=current_usd_seed,
                task_path=usd_task_path,
                data_output_dir=Path(usd_data_output_dir) / usd_label,
                private_dir=Path(usd_private_dir) / usd_label,
                run_dir=usd_run_root / RANDOM_FOREST_BASELINE_ID,
                run_label=usd_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command=command,
                snapshot_date=usd_snapshot_date,
                api_key=usd_api_key,
                source_frame=usd_source_frame,
            )
        )
        results.append(
            run_usd_broad_direction_v0_extra_trees_pipeline(
                seed=current_usd_seed,
                task_path=usd_task_path,
                data_output_dir=Path(usd_data_output_dir) / usd_label,
                private_dir=Path(usd_private_dir) / usd_label,
                run_dir=usd_run_root / EXTRA_TREES_BASELINE_ID,
                run_label=usd_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command=command,
                snapshot_date=usd_snapshot_date,
                api_key=usd_api_key,
                source_frame=usd_source_frame,
            )
        )
        results.append(
            run_usd_afe_vs_eme_relative_direction_v0_previous_day_pipeline(
                seed=current_usd_seed,
                task_path=usd_relative_task_path,
                data_output_dir=Path(usd_relative_data_output_dir) / usd_relative_label,
                private_dir=Path(usd_relative_private_dir) / usd_relative_label,
                run_dir=usd_relative_run_root / PREVIOUS_DAY_DIRECTION_BASELINE_ID,
                run_label=usd_relative_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command=command,
                snapshot_date=usd_snapshot_date,
                api_key=usd_api_key,
                source_frame=usd_source_frame,
            )
        )
        results.append(
            run_usd_afe_vs_eme_relative_direction_v0_logistic_pipeline(
                seed=current_usd_seed,
                task_path=usd_relative_task_path,
                data_output_dir=Path(usd_relative_data_output_dir) / usd_relative_label,
                private_dir=Path(usd_relative_private_dir) / usd_relative_label,
                run_dir=usd_relative_run_root / LOGISTIC_BASELINE_ID,
                run_label=usd_relative_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command=command,
                snapshot_date=usd_snapshot_date,
                api_key=usd_api_key,
                source_frame=usd_source_frame,
            )
        )
        results.append(
            run_usd_afe_vs_eme_relative_direction_v0_random_forest_pipeline(
                seed=current_usd_seed,
                task_path=usd_relative_task_path,
                data_output_dir=Path(usd_relative_data_output_dir) / usd_relative_label,
                private_dir=Path(usd_relative_private_dir) / usd_relative_label,
                run_dir=usd_relative_run_root / RANDOM_FOREST_BASELINE_ID,
                run_label=usd_relative_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command=command,
                snapshot_date=usd_snapshot_date,
                api_key=usd_api_key,
                source_frame=usd_source_frame,
            )
        )
        results.append(
            run_usd_afe_vs_eme_relative_direction_v0_extra_trees_pipeline(
                seed=current_usd_seed,
                task_path=usd_relative_task_path,
                data_output_dir=Path(usd_relative_data_output_dir) / usd_relative_label,
                private_dir=Path(usd_relative_private_dir) / usd_relative_label,
                run_dir=usd_relative_run_root / EXTRA_TREES_BASELINE_ID,
                run_label=usd_relative_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command=command,
                snapshot_date=usd_snapshot_date,
                api_key=usd_api_key,
                source_frame=usd_source_frame,
            )
        )

    write_benchmark_reports_for_results(
        results=results,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
    )
    return BaselineSuiteResult(results=results)


def run_pilot_agent_suite(
    *,
    market_agent_id: str,
    market_agent_version: str,
    market_agent_command: str | list[str] | tuple[str, ...],
    event_agent_id: str,
    event_agent_version: str,
    event_agent_command: str | list[str] | tuple[str, ...],
    treasury_agent_id: str,
    treasury_agent_version: str,
    treasury_agent_command: str | list[str] | tuple[str, ...],
    curve_agent_id: str,
    curve_agent_version: str,
    curve_agent_command: str | list[str] | tuple[str, ...],
    curve3mo_agent_id: str = "treasury_curve_10y3mo_research_sweep_env_agent",
    curve3mo_agent_version: str = "0.2.0",
    curve3mo_agent_command: str | list[str] | tuple[str, ...] = (
        f"{sys.executable} agents/examples/research_sweep_env_agent.py"
    ),
    front_end_agent_id: str = "treasury_front_end_research_sweep_env_agent",
    front_end_agent_version: str = "0.2.0",
    front_end_agent_command: str | list[str] | tuple[str, ...] = (
        f"{sys.executable} agents/examples/research_sweep_env_agent.py"
    ),
    usd_agent_id: str = "usd_research_sweep_env_agent",
    usd_agent_version: str = "0.2.0",
    usd_agent_command: str | list[str] | tuple[str, ...] = (
        f"{sys.executable} agents/examples/research_sweep_env_agent.py"
    ),
    market_seed: int = 11,
    event_seed: int = 23,
    treasury_seed: int = 29,
    curve_seed: int = 31,
    curve3mo_seed: int = 33,
    front_end_seed: int = 31,
    usd_seed: int = 37,
    repeat: int = 3,
    run_label_prefix: str = "pilot_agent",
    market_task_path: str | Path = "tasks/pilot/synthetic_market_direction_v0.yaml",
    event_task_path: str | Path = "tasks/pilot/synthetic_event_response_v0.yaml",
    treasury_task_path: str | Path = "tasks/pilot/yield_direction_treasury10y_v0.yaml",
    curve_task_path: str | Path = "tasks/pilot/yield_curve_10y2y_steepening_v0.yaml",
    curve3mo_task_path: str | Path = "tasks/pilot/yield_curve_10y3mo_steepening_v0.yaml",
    front_end_task_path: str | Path = "tasks/pilot/front_end_spread_widening_v0.yaml",
    usd_task_path: str | Path = "tasks/pilot/usd_broad_direction_v0.yaml",
    usd_relative_task_path: str | Path = "tasks/pilot/usd_afe_vs_eme_relative_direction_v0.yaml",
    market_data_output_dir: str | Path = "data/raw/synthetic_market_direction_v0",
    market_private_dir: str | Path = "data/private/synthetic_market_direction_v0",
    event_data_output_dir: str | Path = "data/raw/synthetic_event_response_v0",
    event_private_dir: str | Path = "data/private/synthetic_event_response_v0",
    treasury_data_output_dir: str | Path = "data/raw/yield_direction_treasury10y_v0",
    treasury_private_dir: str | Path = "data/private/yield_direction_treasury10y_v0",
    curve_data_output_dir: str | Path = "data/raw/yield_curve_10y2y_steepening_v0",
    curve_private_dir: str | Path = "data/private/yield_curve_10y2y_steepening_v0",
    curve3mo_data_output_dir: str | Path = "data/raw/yield_curve_10y3mo_steepening_v0",
    curve3mo_private_dir: str | Path = "data/private/yield_curve_10y3mo_steepening_v0",
    front_end_data_output_dir: str | Path = "data/raw/front_end_spread_widening_v0",
    front_end_private_dir: str | Path = "data/private/front_end_spread_widening_v0",
    usd_data_output_dir: str | Path = "data/raw/usd_broad_direction_v0",
    usd_private_dir: str | Path = "data/private/usd_broad_direction_v0",
    usd_relative_data_output_dir: str | Path = "data/raw/usd_afe_vs_eme_relative_direction_v0",
    usd_relative_private_dir: str | Path = "data/private/usd_afe_vs_eme_relative_direction_v0",
    runs_root: str | Path = DEFAULT_PILOT_AGENT_SUITE_RUNS_ROOT,
    clean_existing_runs: bool = False,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command_timeout_seconds: int = 1800,
    cwd: str | Path | None = None,
    treasury_snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    treasury_api_key: str | None = None,
    treasury_source_frame: Any | None = None,
    curve_snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    curve_api_key: str | None = None,
    curve_source_frame: Any | None = None,
    curve3mo_snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    curve3mo_api_key: str | None = None,
    curve3mo_source_frame: Any | None = None,
    front_end_snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    front_end_api_key: str | None = None,
    front_end_source_frame: Any | None = None,
    usd_snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    usd_api_key: str | None = None,
    usd_source_frame: Any | None = None,
) -> AgentSuiteResult:
    if repeat < 1:
        raise ValueError("repeat must be at least 1")

    root = Path(runs_root)
    if clean_existing_runs:
        remove_output_path(root)
        clear_benchmark_report_outputs(
            report_csv_path=report_csv_path,
            report_markdown_path=report_markdown_path,
            summary_csv_path=summary_csv_path,
            summary_markdown_path=summary_markdown_path,
        )
    market_run_root = root / SYNTHETIC_MARKET_TASK_ID
    event_run_root = root / SYNTHETIC_EVENT_TASK_ID
    treasury_run_root = root / TREASURY_TASK_ID
    curve_run_root = root / TREASURY_CURVE_TASK_ID
    curve3mo_run_root = root / TREASURY_CURVE_10Y3MO_TASK_ID
    front_end_run_root = root / FRONT_END_TASK_ID
    usd_run_root = root / USD_BROAD_TASK_ID
    usd_relative_run_root = root / USD_RELATIVE_TASK_ID
    results: list[PipelineResult] = []

    for repeat_offset in range(repeat):
        repeat_index = repeat_offset + 1
        current_market_seed = market_seed + repeat_offset
        current_event_seed = event_seed + repeat_offset
        current_treasury_seed = treasury_seed + repeat_offset
        current_curve_seed = curve_seed + repeat_offset
        current_curve3mo_seed = curve3mo_seed + repeat_offset
        current_front_end_seed = front_end_seed + repeat_offset
        current_usd_seed = usd_seed + repeat_offset
        market_label = f"{run_label_prefix}_market_{repeat_index:03d}_seed_{current_market_seed}"
        event_label = f"{run_label_prefix}_event_{repeat_index:03d}_seed_{current_event_seed}"
        treasury_label = (
            f"{run_label_prefix}_treasury_{repeat_index:03d}_seed_{current_treasury_seed}"
        )
        curve_label = f"{run_label_prefix}_curve_{repeat_index:03d}_seed_{current_curve_seed}"
        curve3mo_label = (
            f"{run_label_prefix}_curve3mo_{repeat_index:03d}_seed_{current_curve3mo_seed}"
        )
        front_end_label = (
            f"{run_label_prefix}_front_end_{repeat_index:03d}_seed_{current_front_end_seed}"
        )
        usd_label = f"{run_label_prefix}_usd_{repeat_index:03d}_seed_{current_usd_seed}"
        usd_relative_label = (
            f"{run_label_prefix}_usd_relative_{repeat_index:03d}_seed_{current_usd_seed}"
        )

        results.append(
            run_synthetic_market_agent_command(
                agent_id=market_agent_id,
                agent_version=market_agent_version,
                agent_command=market_agent_command,
                seed=current_market_seed,
                task_path=market_task_path,
                data_output_dir=Path(market_data_output_dir) / market_label,
                private_dir=Path(market_private_dir) / market_label,
                run_dir=market_run_root / market_agent_id,
                run_label=market_label,
                repeat_index=repeat_index,
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
        results.append(
            run_synthetic_event_response_agent_command(
                agent_id=event_agent_id,
                agent_version=event_agent_version,
                agent_command=event_agent_command,
                seed=current_event_seed,
                task_path=event_task_path,
                data_output_dir=Path(event_data_output_dir) / event_label,
                private_dir=Path(event_private_dir) / event_label,
                run_dir=event_run_root / event_agent_id,
                run_label=event_label,
                repeat_index=repeat_index,
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
        results.append(
            run_yield_direction_treasury10y_agent_command(
                agent_id=treasury_agent_id,
                agent_version=treasury_agent_version,
                agent_command=treasury_agent_command,
                seed=current_treasury_seed,
                task_path=treasury_task_path,
                data_output_dir=Path(treasury_data_output_dir) / treasury_label,
                private_dir=Path(treasury_private_dir) / treasury_label,
                run_dir=treasury_run_root / treasury_agent_id,
                run_label=treasury_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command_timeout_seconds=command_timeout_seconds,
                cwd=cwd,
                snapshot_date=treasury_snapshot_date,
                api_key=treasury_api_key,
                source_frame=treasury_source_frame,
            )
        )
        results.append(
            run_yield_curve_10y2y_steepening_agent_command(
                agent_id=curve_agent_id,
                agent_version=curve_agent_version,
                agent_command=curve_agent_command,
                seed=current_curve_seed,
                task_path=curve_task_path,
                data_output_dir=Path(curve_data_output_dir) / curve_label,
                private_dir=Path(curve_private_dir) / curve_label,
                run_dir=curve_run_root / curve_agent_id,
                run_label=curve_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command_timeout_seconds=command_timeout_seconds,
                cwd=cwd,
                snapshot_date=curve_snapshot_date,
                api_key=curve_api_key,
                source_frame=curve_source_frame if curve_source_frame is not None else treasury_source_frame,
            )
        )
        results.append(
            run_yield_curve_10y3mo_steepening_agent_command(
                agent_id=curve3mo_agent_id,
                agent_version=curve3mo_agent_version,
                agent_command=curve3mo_agent_command,
                seed=current_curve3mo_seed,
                task_path=curve3mo_task_path,
                data_output_dir=Path(curve3mo_data_output_dir) / curve3mo_label,
                private_dir=Path(curve3mo_private_dir) / curve3mo_label,
                run_dir=curve3mo_run_root / curve3mo_agent_id,
                run_label=curve3mo_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command_timeout_seconds=command_timeout_seconds,
                cwd=cwd,
                snapshot_date=curve3mo_snapshot_date,
                api_key=curve3mo_api_key,
                source_frame=(
                    curve3mo_source_frame
                    if curve3mo_source_frame is not None
                    else treasury_source_frame
                ),
            )
        )
        results.append(
            run_front_end_spread_widening_v0_agent_command(
                agent_id=front_end_agent_id,
                agent_version=front_end_agent_version,
                agent_command=front_end_agent_command,
                seed=current_front_end_seed,
                task_path=front_end_task_path,
                data_output_dir=Path(front_end_data_output_dir) / front_end_label,
                private_dir=Path(front_end_private_dir) / front_end_label,
                run_dir=front_end_run_root / front_end_agent_id,
                run_label=front_end_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command_timeout_seconds=command_timeout_seconds,
                cwd=cwd,
                snapshot_date=front_end_snapshot_date,
                api_key=front_end_api_key,
                source_frame=(
                    front_end_source_frame
                    if front_end_source_frame is not None
                    else treasury_source_frame
                ),
            )
        )
        results.append(
            run_usd_broad_direction_v0_agent_command(
                agent_id=usd_agent_id,
                agent_version=usd_agent_version,
                agent_command=usd_agent_command,
                seed=current_usd_seed,
                task_path=usd_task_path,
                data_output_dir=Path(usd_data_output_dir) / usd_label,
                private_dir=Path(usd_private_dir) / usd_label,
                run_dir=usd_run_root / usd_agent_id,
                run_label=usd_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command_timeout_seconds=command_timeout_seconds,
                cwd=cwd,
                snapshot_date=usd_snapshot_date,
                api_key=usd_api_key,
                source_frame=usd_source_frame,
            )
        )
        results.append(
            run_usd_afe_vs_eme_relative_direction_v0_agent_command(
                agent_id=usd_agent_id,
                agent_version=usd_agent_version,
                agent_command=usd_agent_command,
                seed=current_usd_seed,
                task_path=usd_relative_task_path,
                data_output_dir=Path(usd_relative_data_output_dir) / usd_relative_label,
                private_dir=Path(usd_relative_private_dir) / usd_relative_label,
                run_dir=usd_relative_run_root / usd_agent_id,
                run_label=usd_relative_label,
                repeat_index=repeat_index,
                repeat_count=repeat,
                runs_root=root,
                report_csv_path=report_csv_path,
                report_markdown_path=report_markdown_path,
                summary_csv_path=summary_csv_path,
                summary_markdown_path=summary_markdown_path,
                execute_notebook=execute_notebook,
                command_timeout_seconds=command_timeout_seconds,
                cwd=cwd,
                snapshot_date=usd_snapshot_date,
                api_key=usd_api_key,
                source_frame=usd_source_frame,
            )
        )

    write_benchmark_reports_for_results(
        results=results,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
    )
    return AgentSuiteResult(results=results)


def run_pilot_protocol(
    *,
    market_agent_id: str,
    market_agent_version: str,
    market_agent_command: str | list[str] | tuple[str, ...],
    event_agent_id: str,
    event_agent_version: str,
    event_agent_command: str | list[str] | tuple[str, ...],
    treasury_agent_id: str,
    treasury_agent_version: str,
    treasury_agent_command: str | list[str] | tuple[str, ...],
    curve_agent_id: str,
    curve_agent_version: str,
    curve_agent_command: str | list[str] | tuple[str, ...],
    curve3mo_agent_id: str = "treasury_curve_10y3mo_research_sweep_env_agent",
    curve3mo_agent_version: str = "0.2.0",
    curve3mo_agent_command: str | list[str] | tuple[str, ...] = (
        f"{sys.executable} agents/examples/research_sweep_env_agent.py"
    ),
    front_end_agent_id: str = "treasury_front_end_research_sweep_env_agent",
    front_end_agent_version: str = "0.2.0",
    front_end_agent_command: str | list[str] | tuple[str, ...] = (
        f"{sys.executable} agents/examples/research_sweep_env_agent.py"
    ),
    usd_agent_id: str = "usd_research_sweep_env_agent",
    usd_agent_version: str = "0.2.0",
    usd_agent_command: str | list[str] | tuple[str, ...] = (
        f"{sys.executable} agents/examples/research_sweep_env_agent.py"
    ),
    market_seed: int = 11,
    event_seed: int = 23,
    treasury_seed: int = 29,
    curve_seed: int = 31,
    curve3mo_seed: int = 33,
    front_end_seed: int = 31,
    usd_seed: int = 37,
    repeat: int = 3,
    run_label_prefix: str = "pilot_protocol",
    market_task_path: str | Path = "tasks/pilot/synthetic_market_direction_v0.yaml",
    event_task_path: str | Path = "tasks/pilot/synthetic_event_response_v0.yaml",
    treasury_task_path: str | Path = "tasks/pilot/yield_direction_treasury10y_v0.yaml",
    curve_task_path: str | Path = "tasks/pilot/yield_curve_10y2y_steepening_v0.yaml",
    curve3mo_task_path: str | Path = "tasks/pilot/yield_curve_10y3mo_steepening_v0.yaml",
    front_end_task_path: str | Path = "tasks/pilot/front_end_spread_widening_v0.yaml",
    usd_task_path: str | Path = "tasks/pilot/usd_broad_direction_v0.yaml",
    usd_relative_task_path: str | Path = "tasks/pilot/usd_afe_vs_eme_relative_direction_v0.yaml",
    market_data_output_dir: str | Path = "data/raw/synthetic_market_direction_v0",
    market_private_dir: str | Path = "data/private/synthetic_market_direction_v0",
    event_data_output_dir: str | Path = "data/raw/synthetic_event_response_v0",
    event_private_dir: str | Path = "data/private/synthetic_event_response_v0",
    treasury_data_output_dir: str | Path = "data/raw/yield_direction_treasury10y_v0",
    treasury_private_dir: str | Path = "data/private/yield_direction_treasury10y_v0",
    curve_data_output_dir: str | Path = "data/raw/yield_curve_10y2y_steepening_v0",
    curve_private_dir: str | Path = "data/private/yield_curve_10y2y_steepening_v0",
    curve3mo_data_output_dir: str | Path = "data/raw/yield_curve_10y3mo_steepening_v0",
    curve3mo_private_dir: str | Path = "data/private/yield_curve_10y3mo_steepening_v0",
    front_end_data_output_dir: str | Path = "data/raw/front_end_spread_widening_v0",
    front_end_private_dir: str | Path = "data/private/front_end_spread_widening_v0",
    usd_data_output_dir: str | Path = "data/raw/usd_broad_direction_v0",
    usd_private_dir: str | Path = "data/private/usd_broad_direction_v0",
    usd_relative_data_output_dir: str | Path = "data/raw/usd_afe_vs_eme_relative_direction_v0",
    usd_relative_private_dir: str | Path = "data/private/usd_afe_vs_eme_relative_direction_v0",
    runs_root: str | Path = DEFAULT_PILOT_PROTOCOL_RUNS_ROOT,
    clean_existing_runs: bool = False,
    report_csv_path: str | Path = "reports/generated/run_results.csv",
    report_markdown_path: str | Path = "reports/generated/run_results.md",
    summary_csv_path: str | Path = "reports/generated/run_summary.csv",
    summary_markdown_path: str | Path = "reports/generated/run_summary.md",
    execute_notebook: bool = False,
    command_timeout_seconds: int = 1800,
    cwd: str | Path | None = None,
    command: str = "run_pilot_protocol",
    treasury_snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    treasury_api_key: str | None = None,
    treasury_source_frame: Any | None = None,
    curve_snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    curve_api_key: str | None = None,
    curve_source_frame: Any | None = None,
    curve3mo_snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    curve3mo_api_key: str | None = None,
    curve3mo_source_frame: Any | None = None,
    front_end_snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    front_end_api_key: str | None = None,
    front_end_source_frame: Any | None = None,
    usd_snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    usd_api_key: str | None = None,
    usd_source_frame: Any | None = None,
) -> PilotProtocolResult:
    if repeat < 1:
        raise ValueError("repeat must be at least 1")

    root = Path(runs_root)
    if clean_existing_runs:
        remove_output_path(root)
        clear_benchmark_report_outputs(
            report_csv_path=report_csv_path,
            report_markdown_path=report_markdown_path,
            summary_csv_path=summary_csv_path,
            summary_markdown_path=summary_markdown_path,
        )
    baseline_result = run_pilot_baseline_suite(
        market_seed=market_seed,
        event_seed=event_seed,
        treasury_seed=treasury_seed,
        curve_seed=curve_seed,
        curve3mo_seed=curve3mo_seed,
        front_end_seed=front_end_seed,
        usd_seed=usd_seed,
        repeat=repeat,
        run_label_prefix=f"{run_label_prefix}_baseline",
        market_task_path=market_task_path,
        event_task_path=event_task_path,
        treasury_task_path=treasury_task_path,
        curve_task_path=curve_task_path,
        curve3mo_task_path=curve3mo_task_path,
        front_end_task_path=front_end_task_path,
        usd_task_path=usd_task_path,
        usd_relative_task_path=usd_relative_task_path,
        market_data_output_dir=Path(market_data_output_dir) / "baseline",
        market_private_dir=Path(market_private_dir) / "baseline",
        event_data_output_dir=Path(event_data_output_dir) / "baseline",
        event_private_dir=Path(event_private_dir) / "baseline",
        treasury_data_output_dir=Path(treasury_data_output_dir) / "baseline",
        treasury_private_dir=Path(treasury_private_dir) / "baseline",
        curve_data_output_dir=Path(curve_data_output_dir) / "baseline",
        curve_private_dir=Path(curve_private_dir) / "baseline",
        curve3mo_data_output_dir=Path(curve3mo_data_output_dir) / "baseline",
        curve3mo_private_dir=Path(curve3mo_private_dir) / "baseline",
        front_end_data_output_dir=Path(front_end_data_output_dir) / "baseline",
        front_end_private_dir=Path(front_end_private_dir) / "baseline",
        usd_data_output_dir=Path(usd_data_output_dir) / "baseline",
        usd_private_dir=Path(usd_private_dir) / "baseline",
        usd_relative_data_output_dir=Path(usd_relative_data_output_dir) / "baseline",
        usd_relative_private_dir=Path(usd_relative_private_dir) / "baseline",
        runs_root=root,
        clean_existing_runs=False,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command=command,
        treasury_snapshot_date=treasury_snapshot_date,
        treasury_api_key=treasury_api_key,
        treasury_source_frame=treasury_source_frame,
        curve_snapshot_date=curve_snapshot_date,
        curve_api_key=curve_api_key,
        curve_source_frame=curve_source_frame if curve_source_frame is not None else treasury_source_frame,
        curve3mo_snapshot_date=curve3mo_snapshot_date,
        curve3mo_api_key=curve3mo_api_key,
        curve3mo_source_frame=(
            curve3mo_source_frame if curve3mo_source_frame is not None else treasury_source_frame
        ),
        front_end_snapshot_date=front_end_snapshot_date,
        front_end_api_key=front_end_api_key,
        front_end_source_frame=(
            front_end_source_frame if front_end_source_frame is not None else treasury_source_frame
        ),
        usd_snapshot_date=usd_snapshot_date,
        usd_api_key=usd_api_key,
        usd_source_frame=usd_source_frame,
    )
    agent_result = run_pilot_agent_suite(
        market_agent_id=market_agent_id,
        market_agent_version=market_agent_version,
        market_agent_command=market_agent_command,
        event_agent_id=event_agent_id,
        event_agent_version=event_agent_version,
        event_agent_command=event_agent_command,
        treasury_agent_id=treasury_agent_id,
        treasury_agent_version=treasury_agent_version,
        treasury_agent_command=treasury_agent_command,
        curve_agent_id=curve_agent_id,
        curve_agent_version=curve_agent_version,
        curve_agent_command=curve_agent_command,
        curve3mo_agent_id=curve3mo_agent_id,
        curve3mo_agent_version=curve3mo_agent_version,
        curve3mo_agent_command=curve3mo_agent_command,
        front_end_agent_id=front_end_agent_id,
        front_end_agent_version=front_end_agent_version,
        front_end_agent_command=front_end_agent_command,
        usd_agent_id=usd_agent_id,
        usd_agent_version=usd_agent_version,
        usd_agent_command=usd_agent_command,
        market_seed=market_seed,
        event_seed=event_seed,
        treasury_seed=treasury_seed,
        curve_seed=curve_seed,
        curve3mo_seed=curve3mo_seed,
        front_end_seed=front_end_seed,
        usd_seed=usd_seed,
        repeat=repeat,
        run_label_prefix=f"{run_label_prefix}_agent",
        market_task_path=market_task_path,
        event_task_path=event_task_path,
        treasury_task_path=treasury_task_path,
        curve_task_path=curve_task_path,
        curve3mo_task_path=curve3mo_task_path,
        front_end_task_path=front_end_task_path,
        usd_task_path=usd_task_path,
        usd_relative_task_path=usd_relative_task_path,
        market_data_output_dir=Path(market_data_output_dir) / "agent",
        market_private_dir=Path(market_private_dir) / "agent",
        event_data_output_dir=Path(event_data_output_dir) / "agent",
        event_private_dir=Path(event_private_dir) / "agent",
        treasury_data_output_dir=Path(treasury_data_output_dir) / "agent",
        treasury_private_dir=Path(treasury_private_dir) / "agent",
        curve_data_output_dir=Path(curve_data_output_dir) / "agent",
        curve_private_dir=Path(curve_private_dir) / "agent",
        curve3mo_data_output_dir=Path(curve3mo_data_output_dir) / "agent",
        curve3mo_private_dir=Path(curve3mo_private_dir) / "agent",
        front_end_data_output_dir=Path(front_end_data_output_dir) / "agent",
        front_end_private_dir=Path(front_end_private_dir) / "agent",
        usd_data_output_dir=Path(usd_data_output_dir) / "agent",
        usd_private_dir=Path(usd_private_dir) / "agent",
        usd_relative_data_output_dir=Path(usd_relative_data_output_dir) / "agent",
        usd_relative_private_dir=Path(usd_relative_private_dir) / "agent",
        runs_root=root,
        clean_existing_runs=False,
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
        execute_notebook=execute_notebook,
        command_timeout_seconds=command_timeout_seconds,
        cwd=cwd,
        treasury_snapshot_date=treasury_snapshot_date,
        treasury_api_key=treasury_api_key,
        treasury_source_frame=treasury_source_frame,
        curve_snapshot_date=curve_snapshot_date,
        curve_api_key=curve_api_key,
        curve_source_frame=curve_source_frame if curve_source_frame is not None else treasury_source_frame,
        curve3mo_snapshot_date=curve3mo_snapshot_date,
        curve3mo_api_key=curve3mo_api_key,
        curve3mo_source_frame=(
            curve3mo_source_frame if curve3mo_source_frame is not None else treasury_source_frame
        ),
        front_end_snapshot_date=front_end_snapshot_date,
        front_end_api_key=front_end_api_key,
        front_end_source_frame=(
            front_end_source_frame if front_end_source_frame is not None else treasury_source_frame
        ),
        usd_snapshot_date=usd_snapshot_date,
        usd_api_key=usd_api_key,
        usd_source_frame=usd_source_frame,
    )

    write_benchmark_reports_for_results(
        results=[*baseline_result.results, *agent_result.results],
        report_csv_path=report_csv_path,
        report_markdown_path=report_markdown_path,
        summary_csv_path=summary_csv_path,
        summary_markdown_path=summary_markdown_path,
    )

    return PilotProtocolResult(
        baseline_result=baseline_result,
        agent_result=agent_result,
    )
