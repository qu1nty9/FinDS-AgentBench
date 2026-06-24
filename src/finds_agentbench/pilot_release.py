from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from finds_agentbench.benchmark_manifest import (
    BENCHMARK_ID,
    BENCHMARK_VERSION,
    RELEASE_STAGE,
    build_benchmark_manifest,
    command_for_protocol,
)
from finds_agentbench.paper_artifacts import build_paper_artifacts
from finds_agentbench.pipelines import (
    AgentSuiteResult,
    BaselineSuiteResult,
    DEFAULT_PILOT_AGENT_SUITE_RUNS_ROOT,
    DEFAULT_PILOT_BASELINE_SUITE_RUNS_ROOT,
    DEFAULT_PILOT_PROTOCOL_RUNS_ROOT,
    PilotProtocolResult,
    remove_output_path,
    run_pilot_agent_suite,
    run_pilot_baseline_suite,
    run_pilot_protocol,
)
from finds_agentbench.io import load_yaml
from finds_agentbench.reference_results import load_csv_rows, write_reference_results_snapshot
from finds_agentbench.statistical_artifacts import build_statistical_artifacts
from finds_agentbench.task_cards import discover_task_specs
from finds_agentbench.treasury import DEFAULT_REALTIME_SNAPSHOT_DATE


DEFAULT_RELEASE_REPORTS_ROOT = Path("reports/release_runs")
DEFAULT_RELEASE_OUTPUT_ROOT = Path("docs/releases/pilot_v0")
DEFAULT_REFERENCE_RESULTS_MARKDOWN_PATH = DEFAULT_RELEASE_OUTPUT_ROOT / "reference_results.md"
DEFAULT_REFERENCE_RESULTS_JSON_PATH = DEFAULT_RELEASE_OUTPUT_ROOT / "reference_results.json"
DEFAULT_PAPER_ARTIFACTS_OUTPUT_DIR = DEFAULT_RELEASE_OUTPUT_ROOT / "paper_artifacts"
DEFAULT_STATISTICAL_ARTIFACTS_OUTPUT_DIR = DEFAULT_RELEASE_OUTPUT_ROOT / "statistical_artifacts"

DEFAULT_MARKET_AGENT_ID = "market_research_sweep_env_agent"
DEFAULT_MARKET_AGENT_VERSION = "0.2.0"
DEFAULT_MARKET_AGENT_COMMAND = f"{sys.executable} agents/examples/research_sweep_env_agent.py"
DEFAULT_EVENT_AGENT_ID = "event_rule_env_agent"
DEFAULT_EVENT_AGENT_VERSION = "0.1.0"
DEFAULT_EVENT_AGENT_COMMAND = f"{sys.executable} agents/examples/event_rule_env_agent.py"
DEFAULT_TREASURY_AGENT_ID = "treasury_research_sweep_env_agent"
DEFAULT_TREASURY_AGENT_VERSION = "0.2.0"
DEFAULT_TREASURY_AGENT_COMMAND = f"{sys.executable} agents/examples/research_sweep_env_agent.py"
DEFAULT_CURVE_AGENT_ID = "treasury_curve_research_sweep_env_agent"
DEFAULT_CURVE_AGENT_VERSION = "0.2.0"
DEFAULT_CURVE_AGENT_COMMAND = f"{sys.executable} agents/examples/research_sweep_env_agent.py"
DEFAULT_CURVE3MO_AGENT_ID = "treasury_curve_10y3mo_research_sweep_env_agent"
DEFAULT_CURVE3MO_AGENT_VERSION = "0.2.0"
DEFAULT_CURVE3MO_AGENT_COMMAND = f"{sys.executable} agents/examples/research_sweep_env_agent.py"
DEFAULT_FRONT_END_AGENT_ID = "treasury_front_end_research_sweep_env_agent"
DEFAULT_FRONT_END_AGENT_VERSION = "0.2.0"
DEFAULT_FRONT_END_AGENT_COMMAND = f"{sys.executable} agents/examples/research_sweep_env_agent.py"
DEFAULT_USD_AGENT_ID = "usd_research_sweep_env_agent"
DEFAULT_USD_AGENT_VERSION = "0.2.0"
DEFAULT_USD_AGENT_COMMAND = f"{sys.executable} agents/examples/research_sweep_env_agent.py"


@dataclass(frozen=True)
class PilotReleaseBuildResult:
    baseline_result: BaselineSuiteResult
    agent_result: AgentSuiteResult
    protocol_result: PilotProtocolResult
    report_paths: dict[str, Path]
    reference_results_markdown_path: Path
    reference_results_json_path: Path
    paper_artifact_paths: dict[str, Path]
    statistical_artifact_paths: dict[str, Path]
    manifest_path: Path
    release_readme_path: Path
    cards_index_path: Path
    data_manifests_index_path: Path


def report_paths_for_suite(report_root: str | Path, suite_prefix: str) -> dict[str, Path]:
    root = Path(report_root)
    return {
        f"{suite_prefix}_results_csv": root / f"{suite_prefix}_run_results.csv",
        f"{suite_prefix}_results_markdown": root / f"{suite_prefix}_run_results.md",
        f"{suite_prefix}_summary_csv": root / f"{suite_prefix}_run_summary.csv",
        f"{suite_prefix}_summary_markdown": root / f"{suite_prefix}_run_summary.md",
    }


def require_existing_paths(paths: dict[str, Path]) -> None:
    missing = [f"{name}={path}" for name, path in sorted(paths.items()) if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing expected pilot release outputs: " + ", ".join(missing))


def load_task_ids_from_index(index_path: str | Path) -> set[str]:
    path = Path(index_path)
    if not path.exists():
        return set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    if not isinstance(payload, list):
        return set()
    task_ids: set[str] = set()
    for entry in payload:
        if isinstance(entry, dict) and entry.get("task_id"):
            task_ids.add(str(entry["task_id"]))
    return task_ids


def discover_release_task_ids(tasks_root: str | Path) -> set[str]:
    task_ids: set[str] = set()
    for spec_path in discover_task_specs(tasks_root):
        spec = load_yaml(spec_path)
        metadata = spec.get("metadata", {})
        task_id = metadata.get("task_id")
        if task_id:
            task_ids.add(str(task_id))
    return task_ids


def clear_generated_benchmark_docs(
    *,
    tasks_root: str | Path,
    cards_root: str | Path,
    data_manifests_root: str | Path,
) -> None:
    cards_path = Path(cards_root)
    data_path = Path(data_manifests_root)
    task_ids = discover_release_task_ids(tasks_root)
    task_ids.update(load_task_ids_from_index(cards_path / "task_registry.json"))
    task_ids.update(load_task_ids_from_index(data_path / "index.json"))

    for task_id in sorted(task_ids):
        remove_output_path(cards_path / "tasks" / f"{task_id}.md")
        remove_output_path(cards_path / "evaluations" / f"{task_id}.md")
        remove_output_path(data_path / f"{task_id}.json")

    for index_path in (
        cards_path / "task_registry.json",
        cards_path / "task_registry.csv",
        cards_path / "README.md",
        data_path / "index.json",
        data_path / "index.csv",
        data_path / "README.md",
    ):
        remove_output_path(index_path)


def clear_pilot_release_outputs(
    *,
    tasks_root: str | Path,
    cards_root: str | Path,
    data_manifests_root: str | Path,
    release_output_root: str | Path,
    reference_results_markdown_path: str | Path,
    reference_results_json_path: str | Path,
    paper_artifacts_output_dir: str | Path,
    statistical_artifacts_output_dir: str | Path,
) -> None:
    clear_generated_benchmark_docs(
        tasks_root=tasks_root,
        cards_root=cards_root,
        data_manifests_root=data_manifests_root,
    )
    remove_output_path(reference_results_markdown_path)
    remove_output_path(reference_results_json_path)
    remove_output_path(paper_artifacts_output_dir)
    remove_output_path(statistical_artifacts_output_dir)
    release_root = Path(release_output_root)
    remove_output_path(release_root / "manifest.json")
    remove_output_path(release_root / "README.md")


def build_pilot_release(
    *,
    market_agent_id: str = DEFAULT_MARKET_AGENT_ID,
    market_agent_version: str = DEFAULT_MARKET_AGENT_VERSION,
    market_agent_command: str | list[str] | tuple[str, ...] = DEFAULT_MARKET_AGENT_COMMAND,
    event_agent_id: str = DEFAULT_EVENT_AGENT_ID,
    event_agent_version: str = DEFAULT_EVENT_AGENT_VERSION,
    event_agent_command: str | list[str] | tuple[str, ...] = DEFAULT_EVENT_AGENT_COMMAND,
    treasury_agent_id: str = DEFAULT_TREASURY_AGENT_ID,
    treasury_agent_version: str = DEFAULT_TREASURY_AGENT_VERSION,
    treasury_agent_command: str | list[str] | tuple[str, ...] = DEFAULT_TREASURY_AGENT_COMMAND,
    curve_agent_id: str = DEFAULT_CURVE_AGENT_ID,
    curve_agent_version: str = DEFAULT_CURVE_AGENT_VERSION,
    curve_agent_command: str | list[str] | tuple[str, ...] = DEFAULT_CURVE_AGENT_COMMAND,
    curve3mo_agent_id: str = DEFAULT_CURVE3MO_AGENT_ID,
    curve3mo_agent_version: str = DEFAULT_CURVE3MO_AGENT_VERSION,
    curve3mo_agent_command: str | list[str] | tuple[str, ...] = DEFAULT_CURVE3MO_AGENT_COMMAND,
    front_end_agent_id: str = DEFAULT_FRONT_END_AGENT_ID,
    front_end_agent_version: str = DEFAULT_FRONT_END_AGENT_VERSION,
    front_end_agent_command: str | list[str] | tuple[str, ...] = DEFAULT_FRONT_END_AGENT_COMMAND,
    usd_agent_id: str = DEFAULT_USD_AGENT_ID,
    usd_agent_version: str = DEFAULT_USD_AGENT_VERSION,
    usd_agent_command: str | list[str] | tuple[str, ...] = DEFAULT_USD_AGENT_COMMAND,
    market_seed: int = 11,
    event_seed: int = 23,
    treasury_seed: int = 29,
    curve_seed: int = 31,
    curve3mo_seed: int = 33,
    front_end_seed: int = 31,
    usd_seed: int = 37,
    repeat: int = 3,
    baseline_run_label_prefix: str = "pilot",
    agent_run_label_prefix: str = "pilot_agent",
    protocol_run_label_prefix: str = "pilot_protocol",
    market_task_path: str | Path = "tasks/pilot/synthetic_market_direction_v0.yaml",
    event_task_path: str | Path = "tasks/pilot/synthetic_event_response_v0.yaml",
    treasury_task_path: str | Path = "tasks/pilot/yield_direction_treasury10y_v0.yaml",
    curve_task_path: str | Path = "tasks/pilot/yield_curve_10y2y_steepening_v0.yaml",
    curve3mo_task_path: str | Path = "tasks/pilot/yield_curve_10y3mo_steepening_v0.yaml",
    front_end_task_path: str | Path = "tasks/pilot/front_end_spread_widening_v0.yaml",
    usd_task_path: str | Path = "tasks/pilot/usd_broad_direction_v0.yaml",
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
    baseline_runs_root: str | Path = DEFAULT_PILOT_BASELINE_SUITE_RUNS_ROOT,
    agent_runs_root: str | Path = DEFAULT_PILOT_AGENT_SUITE_RUNS_ROOT,
    protocol_runs_root: str | Path = DEFAULT_PILOT_PROTOCOL_RUNS_ROOT,
    reports_root: str | Path = DEFAULT_RELEASE_REPORTS_ROOT,
    release_output_root: str | Path = DEFAULT_RELEASE_OUTPUT_ROOT,
    reference_results_markdown_path: str | Path = DEFAULT_REFERENCE_RESULTS_MARKDOWN_PATH,
    reference_results_json_path: str | Path = DEFAULT_REFERENCE_RESULTS_JSON_PATH,
    paper_artifacts_output_dir: str | Path = DEFAULT_PAPER_ARTIFACTS_OUTPUT_DIR,
    statistical_artifacts_output_dir: str | Path = DEFAULT_STATISTICAL_ARTIFACTS_OUTPUT_DIR,
    tasks_root: str | Path = "tasks/pilot",
    cards_root: str | Path = "docs/cards",
    data_manifests_root: str | Path = "docs/data_manifests/pilot_v0",
    clean_existing_outputs: bool = False,
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
) -> PilotReleaseBuildResult:
    if repeat < 1:
        raise ValueError("repeat must be at least 1")

    report_root = Path(reports_root)
    release_root = Path(release_output_root)
    if clean_existing_outputs:
        clear_pilot_release_outputs(
            tasks_root=tasks_root,
            cards_root=cards_root,
            data_manifests_root=data_manifests_root,
            release_output_root=release_root,
            reference_results_markdown_path=reference_results_markdown_path,
            reference_results_json_path=reference_results_json_path,
            paper_artifacts_output_dir=paper_artifacts_output_dir,
            statistical_artifacts_output_dir=statistical_artifacts_output_dir,
        )
    report_root.mkdir(parents=True, exist_ok=True)
    release_root.mkdir(parents=True, exist_ok=True)

    baseline_report_paths = report_paths_for_suite(report_root, "pilot_baseline")
    agent_report_paths = report_paths_for_suite(report_root, "pilot_agent")
    protocol_report_paths = report_paths_for_suite(report_root, "pilot_protocol")

    baseline_result = run_pilot_baseline_suite(
        market_seed=market_seed,
        event_seed=event_seed,
        treasury_seed=treasury_seed,
        curve_seed=curve_seed,
        curve3mo_seed=curve3mo_seed,
        front_end_seed=front_end_seed,
        usd_seed=usd_seed,
        repeat=repeat,
        run_label_prefix=baseline_run_label_prefix,
        market_task_path=market_task_path,
        event_task_path=event_task_path,
        treasury_task_path=treasury_task_path,
        curve_task_path=curve_task_path,
        curve3mo_task_path=curve3mo_task_path,
        front_end_task_path=front_end_task_path,
        usd_task_path=usd_task_path,
        market_data_output_dir=market_data_output_dir,
        market_private_dir=market_private_dir,
        event_data_output_dir=event_data_output_dir,
        event_private_dir=event_private_dir,
        treasury_data_output_dir=treasury_data_output_dir,
        treasury_private_dir=treasury_private_dir,
        curve_data_output_dir=curve_data_output_dir,
        curve_private_dir=curve_private_dir,
        curve3mo_data_output_dir=curve3mo_data_output_dir,
        curve3mo_private_dir=curve3mo_private_dir,
        front_end_data_output_dir=front_end_data_output_dir,
        front_end_private_dir=front_end_private_dir,
        usd_data_output_dir=usd_data_output_dir,
        usd_private_dir=usd_private_dir,
        runs_root=baseline_runs_root,
        clean_existing_runs=clean_existing_outputs,
        report_csv_path=baseline_report_paths["pilot_baseline_results_csv"],
        report_markdown_path=baseline_report_paths["pilot_baseline_results_markdown"],
        summary_csv_path=baseline_report_paths["pilot_baseline_summary_csv"],
        summary_markdown_path=baseline_report_paths["pilot_baseline_summary_markdown"],
        execute_notebook=execute_notebook,
        command=command_for_protocol("pilot_baseline_suite"),
        treasury_snapshot_date=treasury_snapshot_date,
        treasury_api_key=treasury_api_key,
        treasury_source_frame=treasury_source_frame,
        curve_snapshot_date=curve_snapshot_date,
        curve_api_key=curve_api_key,
        curve_source_frame=curve_source_frame,
        curve3mo_snapshot_date=curve3mo_snapshot_date,
        curve3mo_api_key=curve3mo_api_key,
        curve3mo_source_frame=curve3mo_source_frame,
        front_end_snapshot_date=front_end_snapshot_date,
        front_end_api_key=front_end_api_key,
        front_end_source_frame=front_end_source_frame,
        usd_snapshot_date=usd_snapshot_date,
        usd_api_key=usd_api_key,
        usd_source_frame=usd_source_frame,
    )
    if baseline_result.status != "completed":
        raise RuntimeError(f"Pilot baseline suite failed with status={baseline_result.status}")
    require_existing_paths(baseline_report_paths)

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
        run_label_prefix=agent_run_label_prefix,
        market_task_path=market_task_path,
        event_task_path=event_task_path,
        treasury_task_path=treasury_task_path,
        curve_task_path=curve_task_path,
        curve3mo_task_path=curve3mo_task_path,
        front_end_task_path=front_end_task_path,
        usd_task_path=usd_task_path,
        market_data_output_dir=market_data_output_dir,
        market_private_dir=market_private_dir,
        event_data_output_dir=event_data_output_dir,
        event_private_dir=event_private_dir,
        treasury_data_output_dir=treasury_data_output_dir,
        treasury_private_dir=treasury_private_dir,
        curve_data_output_dir=curve_data_output_dir,
        curve_private_dir=curve_private_dir,
        curve3mo_data_output_dir=curve3mo_data_output_dir,
        curve3mo_private_dir=curve3mo_private_dir,
        front_end_data_output_dir=front_end_data_output_dir,
        front_end_private_dir=front_end_private_dir,
        usd_data_output_dir=usd_data_output_dir,
        usd_private_dir=usd_private_dir,
        runs_root=agent_runs_root,
        clean_existing_runs=clean_existing_outputs,
        report_csv_path=agent_report_paths["pilot_agent_results_csv"],
        report_markdown_path=agent_report_paths["pilot_agent_results_markdown"],
        summary_csv_path=agent_report_paths["pilot_agent_summary_csv"],
        summary_markdown_path=agent_report_paths["pilot_agent_summary_markdown"],
        execute_notebook=execute_notebook,
        command_timeout_seconds=command_timeout_seconds,
        cwd=cwd,
        treasury_snapshot_date=treasury_snapshot_date,
        treasury_api_key=treasury_api_key,
        treasury_source_frame=treasury_source_frame,
        curve_snapshot_date=curve_snapshot_date,
        curve_api_key=curve_api_key,
        curve_source_frame=curve_source_frame,
        curve3mo_snapshot_date=curve3mo_snapshot_date,
        curve3mo_api_key=curve3mo_api_key,
        curve3mo_source_frame=curve3mo_source_frame,
        front_end_snapshot_date=front_end_snapshot_date,
        front_end_api_key=front_end_api_key,
        front_end_source_frame=front_end_source_frame,
        usd_snapshot_date=usd_snapshot_date,
        usd_api_key=usd_api_key,
        usd_source_frame=usd_source_frame,
    )
    if agent_result.status != "completed":
        raise RuntimeError(f"Pilot agent suite failed with status={agent_result.status}")
    require_existing_paths(agent_report_paths)

    protocol_result = run_pilot_protocol(
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
        run_label_prefix=protocol_run_label_prefix,
        market_task_path=market_task_path,
        event_task_path=event_task_path,
        treasury_task_path=treasury_task_path,
        curve_task_path=curve_task_path,
        curve3mo_task_path=curve3mo_task_path,
        front_end_task_path=front_end_task_path,
        usd_task_path=usd_task_path,
        market_data_output_dir=market_data_output_dir,
        market_private_dir=market_private_dir,
        event_data_output_dir=event_data_output_dir,
        event_private_dir=event_private_dir,
        treasury_data_output_dir=treasury_data_output_dir,
        treasury_private_dir=treasury_private_dir,
        curve_data_output_dir=curve_data_output_dir,
        curve_private_dir=curve_private_dir,
        curve3mo_data_output_dir=curve3mo_data_output_dir,
        curve3mo_private_dir=curve3mo_private_dir,
        front_end_data_output_dir=front_end_data_output_dir,
        front_end_private_dir=front_end_private_dir,
        usd_data_output_dir=usd_data_output_dir,
        usd_private_dir=usd_private_dir,
        runs_root=protocol_runs_root,
        clean_existing_runs=clean_existing_outputs,
        report_csv_path=protocol_report_paths["pilot_protocol_results_csv"],
        report_markdown_path=protocol_report_paths["pilot_protocol_results_markdown"],
        summary_csv_path=protocol_report_paths["pilot_protocol_summary_csv"],
        summary_markdown_path=protocol_report_paths["pilot_protocol_summary_markdown"],
        execute_notebook=execute_notebook,
        command_timeout_seconds=command_timeout_seconds,
        cwd=cwd,
        command=command_for_protocol("pilot_protocol"),
        treasury_snapshot_date=treasury_snapshot_date,
        treasury_api_key=treasury_api_key,
        treasury_source_frame=treasury_source_frame,
        curve_snapshot_date=curve_snapshot_date,
        curve_api_key=curve_api_key,
        curve_source_frame=curve_source_frame,
        curve3mo_snapshot_date=curve3mo_snapshot_date,
        curve3mo_api_key=curve3mo_api_key,
        curve3mo_source_frame=curve3mo_source_frame,
        front_end_snapshot_date=front_end_snapshot_date,
        front_end_api_key=front_end_api_key,
        front_end_source_frame=front_end_source_frame,
        usd_snapshot_date=usd_snapshot_date,
        usd_api_key=usd_api_key,
        usd_source_frame=usd_source_frame,
    )
    if protocol_result.status != "completed":
        raise RuntimeError(f"Pilot protocol suite failed with status={protocol_result.status}")
    require_existing_paths(protocol_report_paths)

    reference_markdown_path, reference_json_path = write_reference_results_snapshot(
        output_markdown_path=reference_results_markdown_path,
        output_json_path=reference_results_json_path,
        benchmark_id=BENCHMARK_ID,
        benchmark_version=BENCHMARK_VERSION,
        release_stage=RELEASE_STAGE,
        treasury_snapshot_date=treasury_snapshot_date or "",
        baseline_rows=load_csv_rows(baseline_report_paths["pilot_baseline_summary_csv"]),
        agent_rows=load_csv_rows(agent_report_paths["pilot_agent_summary_csv"]),
        protocol_rows=load_csv_rows(protocol_report_paths["pilot_protocol_summary_csv"]),
        baseline_command=command_for_protocol("pilot_baseline_suite"),
        agent_command=command_for_protocol("pilot_agent_suite"),
        protocol_command=command_for_protocol("pilot_protocol"),
        expected_run_count=repeat,
    )

    paper_artifact_paths = build_paper_artifacts(
        reference_results_path=reference_json_path,
        output_dir=paper_artifacts_output_dir,
    )
    require_existing_paths(paper_artifact_paths)

    statistical_artifact_paths = build_statistical_artifacts(
        protocol_results_csv_path=protocol_report_paths["pilot_protocol_results_csv"],
        output_dir=statistical_artifacts_output_dir,
    )
    require_existing_paths(statistical_artifact_paths)

    manifest_result = build_benchmark_manifest(
        tasks_root=tasks_root,
        cards_root=cards_root,
        data_manifests_root=data_manifests_root,
        output_root=release_root,
    )
    manifest_paths = {
        "manifest": manifest_result.manifest_path,
        "release_readme": manifest_result.readme_path,
        "cards_index": manifest_result.cards_index_path,
        "data_manifests_index": manifest_result.data_manifests_readme_path,
        "reference_results_markdown": reference_markdown_path,
        "reference_results_json": reference_json_path,
        "statistical_artifacts_readme": statistical_artifact_paths["readme"],
    }
    require_existing_paths(manifest_paths)

    report_paths = {
        **baseline_report_paths,
        **agent_report_paths,
        **protocol_report_paths,
    }

    return PilotReleaseBuildResult(
        baseline_result=baseline_result,
        agent_result=agent_result,
        protocol_result=protocol_result,
        report_paths=report_paths,
        reference_results_markdown_path=reference_markdown_path,
        reference_results_json_path=reference_json_path,
        paper_artifact_paths=paper_artifact_paths,
        statistical_artifact_paths=statistical_artifact_paths,
        manifest_path=manifest_result.manifest_path,
        release_readme_path=manifest_result.readme_path,
        cards_index_path=manifest_result.cards_index_path,
        data_manifests_index_path=manifest_result.data_manifests_readme_path,
    )
