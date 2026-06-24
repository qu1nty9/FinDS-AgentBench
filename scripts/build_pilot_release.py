#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from finds_agentbench.pilot_release import (
    DEFAULT_EVENT_AGENT_COMMAND,
    DEFAULT_EVENT_AGENT_ID,
    DEFAULT_EVENT_AGENT_VERSION,
    DEFAULT_CURVE_AGENT_COMMAND,
    DEFAULT_CURVE_AGENT_ID,
    DEFAULT_CURVE_AGENT_VERSION,
    DEFAULT_CURVE3MO_AGENT_COMMAND,
    DEFAULT_CURVE3MO_AGENT_ID,
    DEFAULT_CURVE3MO_AGENT_VERSION,
    DEFAULT_FRONT_END_AGENT_COMMAND,
    DEFAULT_FRONT_END_AGENT_ID,
    DEFAULT_FRONT_END_AGENT_VERSION,
    DEFAULT_MARKET_AGENT_COMMAND,
    DEFAULT_MARKET_AGENT_ID,
    DEFAULT_MARKET_AGENT_VERSION,
    DEFAULT_PAPER_ARTIFACTS_OUTPUT_DIR,
    DEFAULT_REFERENCE_RESULTS_JSON_PATH,
    DEFAULT_REFERENCE_RESULTS_MARKDOWN_PATH,
    DEFAULT_RELEASE_OUTPUT_ROOT,
    DEFAULT_RELEASE_REPORTS_ROOT,
    DEFAULT_STATISTICAL_ARTIFACTS_OUTPUT_DIR,
    DEFAULT_TREASURY_AGENT_COMMAND,
    DEFAULT_TREASURY_AGENT_ID,
    DEFAULT_TREASURY_AGENT_VERSION,
    DEFAULT_USD_AGENT_COMMAND,
    DEFAULT_USD_AGENT_ID,
    DEFAULT_USD_AGENT_VERSION,
    build_pilot_release,
)
from finds_agentbench.pipelines import (
    DEFAULT_PILOT_AGENT_SUITE_RUNS_ROOT,
    DEFAULT_PILOT_BASELINE_SUITE_RUNS_ROOT,
    DEFAULT_PILOT_PROTOCOL_RUNS_ROOT,
)
from finds_agentbench.treasury import DEFAULT_REALTIME_SNAPSHOT_DATE


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the full FinDS-AgentBench pilot release pipeline and rebuild publication artifacts."
    )
    parser.add_argument("--market-agent-id", default=DEFAULT_MARKET_AGENT_ID)
    parser.add_argument("--market-agent-version", default=DEFAULT_MARKET_AGENT_VERSION)
    parser.add_argument("--market-agent-command", default=DEFAULT_MARKET_AGENT_COMMAND)
    parser.add_argument("--event-agent-id", default=DEFAULT_EVENT_AGENT_ID)
    parser.add_argument("--event-agent-version", default=DEFAULT_EVENT_AGENT_VERSION)
    parser.add_argument("--event-agent-command", default=DEFAULT_EVENT_AGENT_COMMAND)
    parser.add_argument("--treasury-agent-id", default=DEFAULT_TREASURY_AGENT_ID)
    parser.add_argument("--treasury-agent-version", default=DEFAULT_TREASURY_AGENT_VERSION)
    parser.add_argument("--treasury-agent-command", default=DEFAULT_TREASURY_AGENT_COMMAND)
    parser.add_argument("--curve-agent-id", default=DEFAULT_CURVE_AGENT_ID)
    parser.add_argument("--curve-agent-version", default=DEFAULT_CURVE_AGENT_VERSION)
    parser.add_argument("--curve-agent-command", default=DEFAULT_CURVE_AGENT_COMMAND)
    parser.add_argument("--curve3mo-agent-id", default=DEFAULT_CURVE3MO_AGENT_ID)
    parser.add_argument("--curve3mo-agent-version", default=DEFAULT_CURVE3MO_AGENT_VERSION)
    parser.add_argument("--curve3mo-agent-command", default=DEFAULT_CURVE3MO_AGENT_COMMAND)
    parser.add_argument("--front-end-agent-id", default=DEFAULT_FRONT_END_AGENT_ID)
    parser.add_argument("--front-end-agent-version", default=DEFAULT_FRONT_END_AGENT_VERSION)
    parser.add_argument("--front-end-agent-command", default=DEFAULT_FRONT_END_AGENT_COMMAND)
    parser.add_argument("--usd-agent-id", default=DEFAULT_USD_AGENT_ID)
    parser.add_argument("--usd-agent-version", default=DEFAULT_USD_AGENT_VERSION)
    parser.add_argument("--usd-agent-command", default=DEFAULT_USD_AGENT_COMMAND)
    parser.add_argument("--market-seed", type=int, default=11)
    parser.add_argument("--event-seed", type=int, default=23)
    parser.add_argument("--treasury-seed", type=int, default=29)
    parser.add_argument("--curve-seed", type=int, default=31)
    parser.add_argument("--curve3mo-seed", type=int, default=33)
    parser.add_argument("--front-end-seed", type=int, default=31)
    parser.add_argument("--usd-seed", type=int, default=37)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--baseline-run-label-prefix", default="pilot")
    parser.add_argument("--agent-run-label-prefix", default="pilot_agent")
    parser.add_argument("--protocol-run-label-prefix", default="pilot_protocol")
    parser.add_argument(
        "--market-task",
        type=Path,
        default=Path("tasks/pilot/synthetic_market_direction_v0.yaml"),
    )
    parser.add_argument(
        "--event-task",
        type=Path,
        default=Path("tasks/pilot/synthetic_event_response_v0.yaml"),
    )
    parser.add_argument(
        "--treasury-task",
        type=Path,
        default=Path("tasks/pilot/yield_direction_treasury10y_v0.yaml"),
    )
    parser.add_argument(
        "--curve-task",
        type=Path,
        default=Path("tasks/pilot/yield_curve_10y2y_steepening_v0.yaml"),
    )
    parser.add_argument(
        "--curve3mo-task",
        type=Path,
        default=Path("tasks/pilot/yield_curve_10y3mo_steepening_v0.yaml"),
    )
    parser.add_argument(
        "--front-end-task",
        type=Path,
        default=Path("tasks/pilot/front_end_spread_widening_v0.yaml"),
    )
    parser.add_argument(
        "--usd-task",
        type=Path,
        default=Path("tasks/pilot/usd_broad_direction_v0.yaml"),
    )
    parser.add_argument(
        "--market-data-output-dir",
        type=Path,
        default=Path("data/raw/synthetic_market_direction_v0"),
    )
    parser.add_argument(
        "--market-private-dir",
        type=Path,
        default=Path("data/private/synthetic_market_direction_v0"),
    )
    parser.add_argument(
        "--event-data-output-dir",
        type=Path,
        default=Path("data/raw/synthetic_event_response_v0"),
    )
    parser.add_argument(
        "--event-private-dir",
        type=Path,
        default=Path("data/private/synthetic_event_response_v0"),
    )
    parser.add_argument(
        "--treasury-data-output-dir",
        type=Path,
        default=Path("data/raw/yield_direction_treasury10y_v0"),
    )
    parser.add_argument(
        "--treasury-private-dir",
        type=Path,
        default=Path("data/private/yield_direction_treasury10y_v0"),
    )
    parser.add_argument(
        "--curve-data-output-dir",
        type=Path,
        default=Path("data/raw/yield_curve_10y2y_steepening_v0"),
    )
    parser.add_argument(
        "--curve-private-dir",
        type=Path,
        default=Path("data/private/yield_curve_10y2y_steepening_v0"),
    )
    parser.add_argument(
        "--curve3mo-data-output-dir",
        type=Path,
        default=Path("data/raw/yield_curve_10y3mo_steepening_v0"),
    )
    parser.add_argument(
        "--curve3mo-private-dir",
        type=Path,
        default=Path("data/private/yield_curve_10y3mo_steepening_v0"),
    )
    parser.add_argument(
        "--front-end-data-output-dir",
        type=Path,
        default=Path("data/raw/front_end_spread_widening_v0"),
    )
    parser.add_argument(
        "--front-end-private-dir",
        type=Path,
        default=Path("data/private/front_end_spread_widening_v0"),
    )
    parser.add_argument(
        "--usd-data-output-dir",
        type=Path,
        default=Path("data/raw/usd_broad_direction_v0"),
    )
    parser.add_argument(
        "--usd-private-dir",
        type=Path,
        default=Path("data/private/usd_broad_direction_v0"),
    )
    parser.add_argument(
        "--baseline-runs-root",
        type=Path,
        default=Path(DEFAULT_PILOT_BASELINE_SUITE_RUNS_ROOT),
    )
    parser.add_argument(
        "--agent-runs-root",
        type=Path,
        default=Path(DEFAULT_PILOT_AGENT_SUITE_RUNS_ROOT),
    )
    parser.add_argument(
        "--protocol-runs-root",
        type=Path,
        default=Path(DEFAULT_PILOT_PROTOCOL_RUNS_ROOT),
    )
    parser.add_argument("--reports-root", type=Path, default=DEFAULT_RELEASE_REPORTS_ROOT)
    parser.add_argument("--release-output-root", type=Path, default=DEFAULT_RELEASE_OUTPUT_ROOT)
    parser.add_argument(
        "--reference-results-markdown",
        type=Path,
        default=DEFAULT_REFERENCE_RESULTS_MARKDOWN_PATH,
    )
    parser.add_argument(
        "--reference-results-json",
        type=Path,
        default=DEFAULT_REFERENCE_RESULTS_JSON_PATH,
    )
    parser.add_argument(
        "--paper-artifacts-output-dir",
        type=Path,
        default=DEFAULT_PAPER_ARTIFACTS_OUTPUT_DIR,
    )
    parser.add_argument(
        "--statistical-artifacts-output-dir",
        type=Path,
        default=DEFAULT_STATISTICAL_ARTIFACTS_OUTPUT_DIR,
    )
    parser.add_argument("--tasks-root", type=Path, default=Path("tasks/pilot"))
    parser.add_argument("--cards-root", type=Path, default=Path("docs/cards"))
    parser.add_argument(
        "--data-manifests-root",
        type=Path,
        default=Path("docs/data_manifests/pilot_v0"),
    )
    parser.add_argument("--clean-existing-outputs", action="store_true")
    parser.add_argument(
        "--treasury-snapshot-date",
        type=str,
        default=DEFAULT_REALTIME_SNAPSHOT_DATE,
    )
    parser.add_argument("--treasury-api-key", default=None)
    parser.add_argument(
        "--curve-snapshot-date",
        type=str,
        default=DEFAULT_REALTIME_SNAPSHOT_DATE,
    )
    parser.add_argument("--curve-api-key", default=None)
    parser.add_argument(
        "--curve3mo-snapshot-date",
        type=str,
        default=DEFAULT_REALTIME_SNAPSHOT_DATE,
    )
    parser.add_argument("--curve3mo-api-key", default=None)
    parser.add_argument(
        "--front-end-snapshot-date",
        type=str,
        default=DEFAULT_REALTIME_SNAPSHOT_DATE,
    )
    parser.add_argument("--front-end-api-key", default=None)
    parser.add_argument(
        "--usd-snapshot-date",
        type=str,
        default=DEFAULT_REALTIME_SNAPSHOT_DATE,
    )
    parser.add_argument("--usd-api-key", default=None)
    parser.add_argument("--execute-notebook", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--cwd", type=Path, default=None)
    args = parser.parse_args()

    if args.repeat < 1:
        parser.error("--repeat must be at least 1")

    result = build_pilot_release(
        market_agent_id=args.market_agent_id,
        market_agent_version=args.market_agent_version,
        market_agent_command=args.market_agent_command,
        event_agent_id=args.event_agent_id,
        event_agent_version=args.event_agent_version,
        event_agent_command=args.event_agent_command,
        treasury_agent_id=args.treasury_agent_id,
        treasury_agent_version=args.treasury_agent_version,
        treasury_agent_command=args.treasury_agent_command,
        curve_agent_id=args.curve_agent_id,
        curve_agent_version=args.curve_agent_version,
        curve_agent_command=args.curve_agent_command,
        curve3mo_agent_id=args.curve3mo_agent_id,
        curve3mo_agent_version=args.curve3mo_agent_version,
        curve3mo_agent_command=args.curve3mo_agent_command,
        front_end_agent_id=args.front_end_agent_id,
        front_end_agent_version=args.front_end_agent_version,
        front_end_agent_command=args.front_end_agent_command,
        usd_agent_id=args.usd_agent_id,
        usd_agent_version=args.usd_agent_version,
        usd_agent_command=args.usd_agent_command,
        market_seed=args.market_seed,
        event_seed=args.event_seed,
        treasury_seed=args.treasury_seed,
        curve_seed=args.curve_seed,
        curve3mo_seed=args.curve3mo_seed,
        front_end_seed=args.front_end_seed,
        usd_seed=args.usd_seed,
        repeat=args.repeat,
        baseline_run_label_prefix=args.baseline_run_label_prefix,
        agent_run_label_prefix=args.agent_run_label_prefix,
        protocol_run_label_prefix=args.protocol_run_label_prefix,
        market_task_path=args.market_task,
        event_task_path=args.event_task,
        treasury_task_path=args.treasury_task,
        curve_task_path=args.curve_task,
        curve3mo_task_path=args.curve3mo_task,
        front_end_task_path=args.front_end_task,
        usd_task_path=args.usd_task,
        market_data_output_dir=args.market_data_output_dir,
        market_private_dir=args.market_private_dir,
        event_data_output_dir=args.event_data_output_dir,
        event_private_dir=args.event_private_dir,
        treasury_data_output_dir=args.treasury_data_output_dir,
        treasury_private_dir=args.treasury_private_dir,
        curve_data_output_dir=args.curve_data_output_dir,
        curve_private_dir=args.curve_private_dir,
        curve3mo_data_output_dir=args.curve3mo_data_output_dir,
        curve3mo_private_dir=args.curve3mo_private_dir,
        front_end_data_output_dir=args.front_end_data_output_dir,
        front_end_private_dir=args.front_end_private_dir,
        usd_data_output_dir=args.usd_data_output_dir,
        usd_private_dir=args.usd_private_dir,
        baseline_runs_root=args.baseline_runs_root,
        agent_runs_root=args.agent_runs_root,
        protocol_runs_root=args.protocol_runs_root,
        reports_root=args.reports_root,
        release_output_root=args.release_output_root,
        reference_results_markdown_path=args.reference_results_markdown,
        reference_results_json_path=args.reference_results_json,
        paper_artifacts_output_dir=args.paper_artifacts_output_dir,
        statistical_artifacts_output_dir=args.statistical_artifacts_output_dir,
        tasks_root=args.tasks_root,
        cards_root=args.cards_root,
        data_manifests_root=args.data_manifests_root,
        clean_existing_outputs=args.clean_existing_outputs,
        execute_notebook=args.execute_notebook,
        command_timeout_seconds=args.timeout_seconds,
        cwd=args.cwd,
        treasury_snapshot_date=args.treasury_snapshot_date,
        treasury_api_key=args.treasury_api_key,
        curve_snapshot_date=args.curve_snapshot_date,
        curve_api_key=args.curve_api_key,
        curve3mo_snapshot_date=args.curve3mo_snapshot_date,
        curve3mo_api_key=args.curve3mo_api_key,
        front_end_snapshot_date=args.front_end_snapshot_date,
        front_end_api_key=args.front_end_api_key,
        usd_snapshot_date=args.usd_snapshot_date,
        usd_api_key=args.usd_api_key,
    )

    for key, path in sorted(result.report_paths.items()):
        print(f"{key}: {path}")
    print(f"reference_results_markdown: {result.reference_results_markdown_path}")
    print(f"reference_results_json: {result.reference_results_json_path}")
    for key, path in sorted(result.paper_artifact_paths.items()):
        print(f"{key}: {path}")
    for key, path in sorted(result.statistical_artifact_paths.items()):
        print(f"{key}: {path}")
    print(f"manifest: {result.manifest_path}")
    print(f"release_readme: {result.release_readme_path}")
    print(f"cards_index: {result.cards_index_path}")
    print(f"data_manifests_index: {result.data_manifests_index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
