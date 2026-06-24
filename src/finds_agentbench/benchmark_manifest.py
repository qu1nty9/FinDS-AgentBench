from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from finds_agentbench.data_manifest import build_data_manifests
from finds_agentbench.external_agents import build_external_agent_readiness_artifacts
from finds_agentbench.manual_audit import build_manual_audit_workflow_artifacts, load_manual_audit_bundle
from finds_agentbench.submission_readiness import build_submission_readiness_artifacts
from finds_agentbench.task_cards import build_task_cards, markdown_table


BENCHMARK_ID = "finds_agentbench_pilot_v0"
BENCHMARK_VERSION = "0.1.0"
RELEASE_STAGE = "pilot"
MANUAL_AUDIT_RUBRIC_PATH = "audits/pilot_v0/manual_audit_rubric.yaml"
MANUAL_AUDIT_SUBSET_PATH = "audits/pilot_v0/adjudicated_subset.json"
MANUAL_AUDIT_README_PATH = "audits/pilot_v0/README.md"
EXTERNAL_AGENT_REGISTRY_PATH = "agents/external_agent_registry.yaml"
PILOT_RELEASE_DOCS_ROOT = "docs/releases/pilot_v0"
EXTERNAL_AGENT_PROTOCOL_MARKDOWN_PATH = f"{PILOT_RELEASE_DOCS_ROOT}/external_agent_protocol.md"
EXTERNAL_AGENT_READINESS_JSON_PATH = f"{PILOT_RELEASE_DOCS_ROOT}/external_agent_readiness.json"
EXTERNAL_AGENT_READINESS_MARKDOWN_PATH = f"{PILOT_RELEASE_DOCS_ROOT}/external_agent_readiness.md"
EXTERNAL_AGENT_REGISTRATION_VALIDATION_JSON_PATH = (
    f"{PILOT_RELEASE_DOCS_ROOT}/external_agent_registration_validation.json"
)
EXTERNAL_AGENT_REGISTRATION_VALIDATION_MARKDOWN_PATH = (
    f"{PILOT_RELEASE_DOCS_ROOT}/external_agent_registration_validation.md"
)
SUBMISSION_READINESS_JSON_PATH = f"{PILOT_RELEASE_DOCS_ROOT}/submission_readiness.json"
SUBMISSION_READINESS_MARKDOWN_PATH = f"{PILOT_RELEASE_DOCS_ROOT}/submission_readiness.md"
RELEASE_ARCHIVE_PATH = (
    f"dist/release_archives/{BENCHMARK_ID}-{BENCHMARK_VERSION}-{RELEASE_STAGE}.tar.gz"
)
RELEASE_ARCHIVE_MANIFEST_JSON_PATH = f"{PILOT_RELEASE_DOCS_ROOT}/archive_manifest.json"
RELEASE_ARCHIVE_MANIFEST_MARKDOWN_PATH = f"{PILOT_RELEASE_DOCS_ROOT}/archive_manifest.md"

TASK_RELEASE_METADATA: dict[str, dict[str, Any]] = {
    "leakage_audit_temporal_split_v0": {
        "runnable": True,
        "release_status": "runnable_public_pilot",
        "blocked_reason": None,
        "default_commands": [
            "PYTHONPATH=src python scripts/generate_leakage_audit_temporal_split_v0.py --seed 7",
            "PYTHONPATH=src python scripts/validate_task.py tasks/pilot/leakage_audit_temporal_split_v0.yaml",
            "PYTHONPATH=src python scripts/score_leakage_audit_temporal_split_v0.py --submission-dir baselines/leakage_audit_temporal_split_v0/expert_submission",
        ],
    },
    "synthetic_event_response_v0": {
        "runnable": True,
        "release_status": "runnable_public_pilot",
        "blocked_reason": None,
        "default_commands": [
            "PYTHONPATH=src python scripts/generate_synthetic_event_response_v0.py --seed 23",
            "PYTHONPATH=src python scripts/run_synthetic_event_response_rule_pipeline.py",
            "PYTHONPATH=src python scripts/run_synthetic_event_response_agent_suite.py --agent-id event_rule_env_agent --agent-version 0.1.0 --agent-command \".venv/bin/python agents/examples/event_rule_env_agent.py\" --repeat 3 --seed 23 --run-label-prefix pilot_event_agent",
        ],
    },
    "synthetic_market_direction_v0": {
        "runnable": True,
        "release_status": "runnable_public_pilot",
        "blocked_reason": None,
        "default_commands": [
            "PYTHONPATH=src python scripts/generate_synthetic_market_direction_v0.py --seed 11",
            "PYTHONPATH=src python scripts/run_synthetic_market_momentum_pipeline.py",
            "PYTHONPATH=src python scripts/run_synthetic_market_logistic_pipeline.py",
            "PYTHONPATH=src python scripts/run_synthetic_market_agent_suite.py --agent-id market_research_sweep_env_agent --agent-version 0.2.0 --agent-command \".venv/bin/python agents/examples/research_sweep_env_agent.py\" --repeat 3 --seed 11 --run-label-prefix pilot_agent",
        ],
    },
    "yield_direction_treasury10y_v0": {
        "runnable": True,
        "release_status": "runnable_public_pilot",
        "blocked_reason": None,
        "default_commands": [
            "PYTHONPATH=src python scripts/download_yield_direction_treasury10y_v0.py --observation-start 2003-01-02 --observation-end 2026-01-02 --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/validate_task.py tasks/pilot/yield_direction_treasury10y_v0.yaml",
            "PYTHONPATH=src python scripts/run_yield_direction_treasury10y_previous_day_pipeline.py --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/run_yield_direction_treasury10y_logistic_pipeline.py --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/run_yield_direction_treasury10y_random_forest_pipeline.py --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/run_yield_direction_treasury10y_extra_trees_pipeline.py --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/run_yield_direction_treasury10y_agent_suite.py --agent-id treasury_research_sweep_env_agent --agent-version 0.2.0 --agent-command \".venv/bin/python agents/examples/research_sweep_env_agent.py\" --repeat 3 --seed 29 --snapshot-date 2026-06-21 --run-label-prefix pilot_treasury_agent",
        ],
    },
    "yield_curve_10y2y_steepening_v0": {
        "runnable": True,
        "release_status": "runnable_public_pilot",
        "blocked_reason": None,
        "default_commands": [
            "PYTHONPATH=src python scripts/download_yield_curve_10y2y_steepening_v0.py --observation-start 2003-01-02 --observation-end 2026-01-02 --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/validate_task.py tasks/pilot/yield_curve_10y2y_steepening_v0.yaml",
            "PYTHONPATH=src python scripts/run_yield_curve_10y2y_steepening_previous_day_pipeline.py --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/run_yield_curve_10y2y_steepening_logistic_pipeline.py --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/run_yield_curve_10y2y_steepening_random_forest_pipeline.py --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/run_yield_curve_10y2y_steepening_extra_trees_pipeline.py --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/run_yield_curve_10y2y_steepening_agent_suite.py --agent-id treasury_curve_research_sweep_env_agent --agent-version 0.2.0 --agent-command \".venv/bin/python agents/examples/research_sweep_env_agent.py\" --repeat 3 --seed 31 --snapshot-date 2026-06-21 --run-label-prefix pilot_curve_agent",
        ],
    },
    "yield_curve_10y3mo_steepening_v0": {
        "runnable": True,
        "release_status": "runnable_public_pilot",
        "blocked_reason": None,
        "default_commands": [
            "PYTHONPATH=src python scripts/download_yield_curve_10y3mo_steepening_v0.py --observation-start 2003-01-02 --observation-end 2026-01-02 --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/validate_task.py tasks/pilot/yield_curve_10y3mo_steepening_v0.yaml",
            "PYTHONPATH=src python scripts/run_yield_curve_10y3mo_steepening_previous_day_pipeline.py --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/run_yield_curve_10y3mo_steepening_logistic_pipeline.py --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/run_yield_curve_10y3mo_steepening_random_forest_pipeline.py --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/run_yield_curve_10y3mo_steepening_extra_trees_pipeline.py --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/run_yield_curve_10y3mo_steepening_agent_suite.py --agent-id treasury_curve_10y3mo_research_sweep_env_agent --agent-version 0.2.0 --agent-command \".venv/bin/python agents/examples/research_sweep_env_agent.py\" --repeat 3 --seed 33 --snapshot-date 2026-06-21 --run-label-prefix pilot_curve3mo_agent",
        ],
    },
    "front_end_spread_widening_v0": {
        "runnable": True,
        "release_status": "runnable_public_pilot",
        "blocked_reason": None,
        "default_commands": [
            "PYTHONPATH=src python scripts/download_front_end_spread_widening_v0.py --observation-start 2003-01-02 --observation-end 2026-01-02 --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/validate_task.py tasks/pilot/front_end_spread_widening_v0.yaml",
            "PYTHONPATH=src python scripts/run_front_end_spread_widening_v0_previous_day_pipeline.py --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/run_front_end_spread_widening_v0_logistic_pipeline.py --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/run_front_end_spread_widening_v0_random_forest_pipeline.py --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/run_front_end_spread_widening_v0_extra_trees_pipeline.py --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/run_front_end_spread_widening_v0_agent_suite.py --agent-id treasury_front_end_research_sweep_env_agent --agent-version 0.2.0 --agent-command \".venv/bin/python agents/examples/research_sweep_env_agent.py\" --repeat 3 --seed 31 --snapshot-date 2026-06-21 --run-label-prefix pilot_front_end_agent",
        ],
    },
    "usd_broad_direction_v0": {
        "runnable": True,
        "release_status": "runnable_public_pilot",
        "blocked_reason": None,
        "default_commands": [
            "PYTHONPATH=src python scripts/download_usd_broad_direction_v0.py --observation-start 2006-01-03 --observation-end 2026-01-02 --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/validate_task.py tasks/pilot/usd_broad_direction_v0.yaml",
            "PYTHONPATH=src python scripts/run_usd_broad_direction_v0_previous_day_pipeline.py --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/run_usd_broad_direction_v0_logistic_pipeline.py --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/run_usd_broad_direction_v0_random_forest_pipeline.py --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/run_usd_broad_direction_v0_extra_trees_pipeline.py --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/run_usd_broad_direction_v0_agent_suite.py --agent-id usd_research_sweep_env_agent --agent-version 0.2.0 --agent-command \".venv/bin/python agents/examples/research_sweep_env_agent.py\" --repeat 3 --seed 37 --snapshot-date 2026-06-21 --run-label-prefix pilot_usd_agent",
        ],
    },
    "usd_afe_vs_eme_relative_direction_v0": {
        "runnable": True,
        "release_status": "runnable_public_pilot",
        "blocked_reason": None,
        "default_commands": [
            "PYTHONPATH=src python scripts/download_usd_afe_vs_eme_relative_direction_v0.py --observation-start 2006-01-03 --observation-end 2026-01-02 --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/validate_task.py tasks/pilot/usd_afe_vs_eme_relative_direction_v0.yaml",
            "PYTHONPATH=src python scripts/run_usd_afe_vs_eme_relative_direction_v0_previous_day_pipeline.py --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/run_usd_afe_vs_eme_relative_direction_v0_logistic_pipeline.py --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/run_usd_afe_vs_eme_relative_direction_v0_random_forest_pipeline.py --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/run_usd_afe_vs_eme_relative_direction_v0_extra_trees_pipeline.py --snapshot-date 2026-06-21",
            "PYTHONPATH=src python scripts/run_usd_afe_vs_eme_relative_direction_v0_agent_suite.py --agent-id usd_relative_research_sweep_env_agent --agent-version 0.2.0 --agent-command \".venv/bin/python agents/examples/research_sweep_env_agent.py\" --repeat 3 --seed 37 --snapshot-date 2026-06-21 --run-label-prefix pilot_usd_relative_agent",
        ],
    },
}

PILOT_PROTOCOLS = [
    {
        "protocol_id": "pilot_baseline_suite",
        "status": "active",
        "run_types": ["baseline"],
        "task_ids": [
            "synthetic_market_direction_v0",
            "synthetic_event_response_v0",
            "yield_direction_treasury10y_v0",
            "yield_curve_10y2y_steepening_v0",
            "yield_curve_10y3mo_steepening_v0",
            "front_end_spread_widening_v0",
            "usd_broad_direction_v0",
            "usd_afe_vs_eme_relative_direction_v0",
        ],
        "runs_root": "runs/suites/pilot_baselines_v0",
        "command": "PYTHONPATH=src python scripts/run_pilot_baseline_suite.py --repeat 3 --market-seed 11 --event-seed 23 --treasury-seed 29 --curve-seed 31 --curve3mo-seed 33 --front-end-seed 31 --usd-seed 37 --treasury-snapshot-date 2026-06-21 --curve-snapshot-date 2026-06-21 --curve3mo-snapshot-date 2026-06-21 --front-end-snapshot-date 2026-06-21 --usd-snapshot-date 2026-06-21 --clean-existing-runs --run-label-prefix pilot",
    },
    {
        "protocol_id": "pilot_agent_suite",
        "status": "active",
        "run_types": ["agent"],
        "task_ids": [
            "synthetic_market_direction_v0",
            "synthetic_event_response_v0",
            "yield_direction_treasury10y_v0",
            "yield_curve_10y2y_steepening_v0",
            "yield_curve_10y3mo_steepening_v0",
            "front_end_spread_widening_v0",
            "usd_broad_direction_v0",
            "usd_afe_vs_eme_relative_direction_v0",
        ],
        "runs_root": "runs/suites/pilot_agents_v0",
        "command": "PYTHONPATH=src python scripts/run_pilot_agent_suite.py --repeat 3 --market-seed 11 --event-seed 23 --treasury-seed 29 --curve-seed 31 --curve3mo-seed 33 --front-end-seed 31 --usd-seed 37 --treasury-snapshot-date 2026-06-21 --curve-snapshot-date 2026-06-21 --curve3mo-snapshot-date 2026-06-21 --front-end-snapshot-date 2026-06-21 --usd-snapshot-date 2026-06-21 --clean-existing-runs --run-label-prefix pilot_agent",
    },
    {
        "protocol_id": "pilot_protocol",
        "status": "active",
        "run_types": ["baseline", "agent"],
        "task_ids": [
            "synthetic_market_direction_v0",
            "synthetic_event_response_v0",
            "yield_direction_treasury10y_v0",
            "yield_curve_10y2y_steepening_v0",
            "yield_curve_10y3mo_steepening_v0",
            "front_end_spread_widening_v0",
            "usd_broad_direction_v0",
            "usd_afe_vs_eme_relative_direction_v0",
        ],
        "runs_root": "runs/suites/pilot_protocol_v0",
        "command": "PYTHONPATH=src python scripts/run_pilot_protocol.py --repeat 3 --market-seed 11 --event-seed 23 --treasury-seed 29 --curve-seed 31 --curve3mo-seed 33 --front-end-seed 31 --usd-seed 37 --treasury-snapshot-date 2026-06-21 --curve-snapshot-date 2026-06-21 --curve3mo-snapshot-date 2026-06-21 --front-end-snapshot-date 2026-06-21 --usd-snapshot-date 2026-06-21 --clean-existing-runs --run-label-prefix pilot_protocol",
    },
]

PILOT_RELEASE_BUILD_COMMAND = (
    "PYTHONPATH=src python scripts/build_pilot_release.py "
    "--repeat 3 --market-seed 11 --event-seed 23 --treasury-seed 29 --curve-seed 31 --curve3mo-seed 33 --front-end-seed 31 --usd-seed 37 "
    "--treasury-snapshot-date 2026-06-21 --curve-snapshot-date 2026-06-21 --curve3mo-snapshot-date 2026-06-21 --front-end-snapshot-date 2026-06-21 --usd-snapshot-date 2026-06-21 "
    "--clean-existing-outputs"
)


@dataclass(frozen=True)
class BenchmarkManifestBuildResult:
    manifest_path: Path
    readme_path: Path
    cards_index_path: Path
    data_manifests_readme_path: Path


def command_for_protocol(protocol_id: str) -> str:
    for protocol in PILOT_PROTOCOLS:
        if protocol["protocol_id"] == protocol_id:
            return str(protocol["command"])
    raise KeyError(f"Unknown protocol_id: {protocol_id}")


def build_task_release_entry(entry: dict[str, Any], *, data_entry: dict[str, Any] | None) -> dict[str, Any]:
    task_id = entry["task_id"]
    release_metadata = TASK_RELEASE_METADATA.get(
        task_id,
        {
            "runnable": False,
            "release_status": "unclassified",
            "blocked_reason": "No release metadata registered for this task.",
            "default_commands": [],
        },
    )
    return {
        **entry,
        "runnable": release_metadata["runnable"],
        "release_status": release_metadata["release_status"],
        "blocked_reason": release_metadata["blocked_reason"],
        "default_commands": release_metadata["default_commands"],
        "task_card_path": f"docs/cards/tasks/{task_id}.md",
        "evaluation_card_path": f"docs/cards/evaluations/{task_id}.md",
        "data_manifest_path": f"docs/data_manifests/pilot_v0/{task_id}.json",
        "public_data_present": data_entry["public_data_present"] if data_entry is not None else False,
        "public_file_count": data_entry["public_file_count"] if data_entry is not None else 0,
        "public_total_size_bytes": data_entry["public_total_size_bytes"] if data_entry is not None else 0,
    }


def render_release_readme(manifest: dict[str, Any]) -> str:
    task_rows = [
        [
            task["task_id"],
            task["track"],
            task["status"],
            task["release_status"],
            "yes" if task["runnable"] else "no",
            "yes" if task["public_data_present"] else "no",
            f"[task](../../cards/tasks/{task['task_id']}.md)",
            f"[evaluation](../../cards/evaluations/{task['task_id']}.md)",
            f"[data](../../data_manifests/pilot_v0/{task['task_id']}.json)",
        ]
        for task in manifest["tasks"]
    ]
    protocol_rows = [
        [
            protocol["protocol_id"],
            ", ".join(protocol["run_types"]),
            ", ".join(protocol["task_ids"]),
            protocol["runs_root"],
            protocol["status"],
        ]
        for protocol in manifest["protocols"]
    ]
    track_rows = [
        [track["track"], track["task_count"], ", ".join(track["task_ids"])]
        for track in manifest["tracks"]
    ]
    manual_audit = manifest["manual_audit"]
    external_agents = manifest["external_agents"]
    submission_readiness = manifest["submission_readiness"]
    return "\n".join(
        [
            f"# {manifest['benchmark_id']}",
            "",
            "Canonical pilot release manifest for FinDS-AgentBench.",
            "",
            "## Snapshot",
            "",
            markdown_table(
                ["Field", "Value"],
                [
                    ["Benchmark ID", manifest["benchmark_id"]],
                    ["Benchmark Version", manifest["benchmark_version"]],
                    ["Release Stage", manifest["release_stage"]],
                    ["Task Count", manifest["task_count"]],
                    ["Runnable Task Count", manifest["runnable_task_count"]],
                    ["Cards Index", "../../cards/README.md"],
                    ["Data Manifests Index", "../../data_manifests/pilot_v0/README.md"],
                    ["Reference Results", "reference_results.md"],
                    ["Paper Artifacts", "paper_artifacts/README.md"],
                    ["Statistical Artifacts", "statistical_artifacts/README.md"],
                    ["Release Archive Manifest", "archive_manifest.md"],
                    ["Manual Audit", manual_audit["readme_path"]],
                    ["Agreement Report", manual_audit["agreement_report_markdown_path"]],
                    ["Adjudication Queue", manual_audit["adjudication_report_markdown_path"]],
                    ["Reviewer Readiness", manual_audit["reviewer_readiness_markdown_path"]],
                    ["External Agent Protocol", external_agents["protocol_markdown_path"]],
                    ["External Agent Readiness", external_agents["readiness_markdown_path"]],
                    ["Submission Readiness", submission_readiness["markdown_path"]],
                ],
            ).strip(),
            "",
            "## Tracks",
            "",
            markdown_table(["Track", "Task Count", "Task IDs"], track_rows).strip(),
            "",
            "## Tasks",
            "",
            markdown_table(
                [
                    "Task ID",
                    "Track",
                    "Spec Status",
                    "Release Status",
                    "Runnable",
                    "Public Data Present",
                    "Task Card",
                    "Evaluation Card",
                    "Data Manifest",
                ],
                task_rows,
            ).strip(),
            "",
            "## Protocols",
            "",
            markdown_table(
                ["Protocol", "Run Types", "Task IDs", "Runs Root", "Status"],
                protocol_rows,
            ).strip(),
            "",
            "## Submission Readiness",
            "",
            markdown_table(
                ["Field", "Value"],
                [
                    ["Status", submission_readiness["status"]],
                    [
                        "Ready for Workshop Submission",
                        "yes" if submission_readiness["ready_for_workshop_submission"] else "no",
                    ],
                    ["Ready Gates", f"{submission_readiness['ready_gate_count']} / {submission_readiness['gate_count']}"],
                    ["Blocking Gates", submission_readiness["blocking_gate_count"]],
                    ["Report", submission_readiness["markdown_path"]],
                ],
            ).strip(),
            "",
            "## External Agents",
            "",
            markdown_table(
                ["Field", "Value"],
                [
                    ["Readiness Status", external_agents["readiness_status"]],
                    [
                        "Ready for External-Agent Claims",
                        "yes" if external_agents["ready_for_external_agent_claims"] else "no",
                    ],
                    ["Bundled Reference Agents", external_agents["bundled_reference_agent_count"]],
                    [
                        "External Agent Configurations",
                        external_agents["external_agent_configuration_count"],
                    ],
                    [
                        "Completed External Agent Configurations",
                        external_agents["completed_external_agent_configuration_count"],
                    ],
                    [
                        "External Task Coverage",
                        (
                            f"{external_agents['external_task_coverage_count']} / "
                            f"{external_agents['expected_task_count']}"
                        ),
                    ],
                    ["Registry", external_agents["registry_path"]],
                    ["Protocol", external_agents["protocol_markdown_path"]],
                    ["External Agent Handoff", external_agents["handoff_markdown_path"]],
                    ["Readiness Report", external_agents["readiness_markdown_path"]],
                    [
                        "Registration Validation",
                        external_agents["registration_validation_markdown_path"],
                    ],
                ],
            ).strip(),
            "",
            "## Manual Audit",
            "",
            markdown_table(
                ["Field", "Value"],
                [
                    ["Status", manual_audit["status"]],
                    ["Case Count", manual_audit["case_count"]],
                    ["Reviewed Task Count", manual_audit["reviewed_task_count"]],
                    ["Reviewer Readiness Status", manual_audit["reviewer_readiness_status"]],
                    [
                        "Ready for Submission Claims",
                        "yes" if manual_audit["ready_for_submission_claims"] else "no",
                    ],
                    ["Official Agreement Status", manual_audit["agreement_status"]],
                    ["Exploratory Dry-Run Status", manual_audit["exploratory_agreement_status"]],
                    ["Scope Tracks", ", ".join(manual_audit["scope_tracks"])],
                    ["Run Types", ", ".join(manual_audit["run_types"])],
                    ["Rubric", manual_audit["rubric_path"]],
                    ["Seed Subset", manual_audit["subset_path"]],
                    ["Reviews Workflow", manual_audit["reviews_readme_path"]],
                    ["Independent Reviewer Handoff", manual_audit["independent_reviewer_handoff_path"]],
                    [
                        "Independent Reviewer Packet Manifest",
                        manual_audit["independent_reviewer_packet_manifest_markdown_path"],
                    ],
                    ["Seed Reviewer Packet", manual_audit["reviewer_1_seed_path"]],
                    ["Blank Reviewer Template", manual_audit["reviewer_2_template_path"]],
                    ["Shadow Demo Reviewer Packet", manual_audit["reviewer_2_shadow_path"]],
                    ["Agreement Report", manual_audit["agreement_report_markdown_path"]],
                    ["Adjudication Queue", manual_audit["adjudication_report_markdown_path"]],
                    ["Reviewer Readiness", manual_audit["reviewer_readiness_markdown_path"]],
                    [
                        "Independent Packet Validation",
                        manual_audit["independent_reviewer_packet_validation_markdown_path"],
                    ],
                ],
            ).strip(),
            "",
            "## Release Build",
            "",
            f"- `{manifest['release_build_command']}`",
            "",
            "## Official Commands",
            "",
            "\n".join(f"- `{protocol['command']}`" for protocol in manifest["protocols"]),
            "",
        ]
    ) + "\n"


def build_benchmark_manifest(
    *,
    tasks_root: str | Path = "tasks/pilot",
    cards_root: str | Path = "docs/cards",
    data_manifests_root: str | Path = "docs/data_manifests/pilot_v0",
    output_root: str | Path = "docs/releases/pilot_v0",
) -> BenchmarkManifestBuildResult:
    output_path = Path(output_root)
    cards_result = build_task_cards(tasks_root=tasks_root, output_root=cards_root)
    data_result = build_data_manifests(
        tasks_root=tasks_root,
        output_root=data_manifests_root,
        workspace_root=".",
    )
    manual_audit_bundle = load_manual_audit_bundle(
        rubric_path=MANUAL_AUDIT_RUBRIC_PATH,
        subset_path=MANUAL_AUDIT_SUBSET_PATH,
        workspace_root=".",
    )
    manual_audit_workflow = build_manual_audit_workflow_artifacts(
        bundle=manual_audit_bundle,
        workspace_root=".",
    )
    external_agent_artifacts = build_external_agent_readiness_artifacts(
        registry_path=EXTERNAL_AGENT_REGISTRY_PATH,
        protocol_markdown_path=output_path / "external_agent_protocol.md",
        readiness_json_path=output_path / "external_agent_readiness.json",
        readiness_markdown_path=output_path / "external_agent_readiness.md",
    )
    registry_entries = json.loads(cards_result.registry_json_path.read_text(encoding="utf-8"))
    data_entries = {
        entry["task_id"]: entry
        for entry in json.loads(data_result.index_json_path.read_text(encoding="utf-8"))
    }
    tasks = [
        build_task_release_entry(entry, data_entry=data_entries.get(entry["task_id"]))
        for entry in registry_entries
    ]

    tracks: list[dict[str, Any]] = []
    grouped: dict[str, list[str]] = {}
    for task in tasks:
        grouped.setdefault(task["track"], []).append(task["task_id"])
    for track, task_ids in sorted(grouped.items()):
        tracks.append(
            {
                "track": track,
                "task_count": len(task_ids),
                "task_ids": sorted(task_ids),
            }
        )

    manifest = {
        "benchmark_id": BENCHMARK_ID,
        "benchmark_version": BENCHMARK_VERSION,
        "release_stage": RELEASE_STAGE,
        "release_build_command": PILOT_RELEASE_BUILD_COMMAND,
        "reference_results_path": f"{PILOT_RELEASE_DOCS_ROOT}/reference_results.md",
        "paper_artifacts_path": f"{PILOT_RELEASE_DOCS_ROOT}/paper_artifacts/README.md",
        "statistical_artifacts_path": f"{PILOT_RELEASE_DOCS_ROOT}/statistical_artifacts/README.md",
        "release_archive_path": RELEASE_ARCHIVE_PATH,
        "release_archive_manifest_json_path": RELEASE_ARCHIVE_MANIFEST_JSON_PATH,
        "release_archive_manifest_markdown_path": RELEASE_ARCHIVE_MANIFEST_MARKDOWN_PATH,
        "external_agents": {
            "registry_path": EXTERNAL_AGENT_REGISTRY_PATH,
            "protocol_markdown_path": EXTERNAL_AGENT_PROTOCOL_MARKDOWN_PATH,
            "handoff_markdown_path": str(external_agent_artifacts["handoff_markdown_path"]),
            "readiness_json_path": EXTERNAL_AGENT_READINESS_JSON_PATH,
            "readiness_markdown_path": EXTERNAL_AGENT_READINESS_MARKDOWN_PATH,
            "registration_validation_json_path": EXTERNAL_AGENT_REGISTRATION_VALIDATION_JSON_PATH,
            "registration_validation_markdown_path": EXTERNAL_AGENT_REGISTRATION_VALIDATION_MARKDOWN_PATH,
            "registration_validation_status": external_agent_artifacts["registration_validation"][
                "status"
            ],
            "readiness_status": external_agent_artifacts["readiness"]["status"],
            "ready_for_external_agent_claims": external_agent_artifacts["readiness"][
                "ready_for_external_agent_claims"
            ],
            "bundled_reference_agent_count": external_agent_artifacts["readiness"][
                "bundled_reference_agent_count"
            ],
            "external_agent_configuration_count": external_agent_artifacts["readiness"][
                "external_agent_configuration_count"
            ],
            "completed_external_agent_configuration_count": external_agent_artifacts["readiness"][
                "completed_external_agent_configuration_count"
            ],
            "external_task_coverage_count": external_agent_artifacts["readiness"][
                "external_task_coverage_count"
            ],
            "expected_task_count": external_agent_artifacts["readiness"]["expected_task_count"],
            "missing_external_task_ids": external_agent_artifacts["readiness"][
                "missing_external_task_ids"
            ],
            "blocking_items": external_agent_artifacts["readiness"]["blocking_items"],
        },
        "manual_audit": {
            "status": manual_audit_bundle.summary["status"],
            "rubric_path": MANUAL_AUDIT_RUBRIC_PATH,
            "subset_path": MANUAL_AUDIT_SUBSET_PATH,
            "readme_path": MANUAL_AUDIT_README_PATH,
            "reviews_readme_path": str(manual_audit_workflow["reviews_readme_path"]),
            "independent_reviewer_handoff_path": str(
                manual_audit_workflow["independent_reviewer_handoff_path"]
            ),
            "independent_reviewer_packet_manifest_json_path": str(
                manual_audit_workflow["independent_reviewer_packet_manifest_json_path"]
            ),
            "independent_reviewer_packet_manifest_markdown_path": str(
                manual_audit_workflow["independent_reviewer_packet_manifest_markdown_path"]
            ),
            "independent_reviewer_packet_manifest_status": manual_audit_workflow[
                "independent_reviewer_packet_manifest"
            ]["status"],
            "reviewer_1_seed_path": str(manual_audit_workflow["reviewer_1_seed_path"]),
            "reviewer_2_template_path": str(manual_audit_workflow["reviewer_2_template_path"]),
            "reviewer_2_shadow_path": str(manual_audit_workflow["reviewer_2_shadow_path"]),
            "agreement_report_json_path": str(manual_audit_workflow["agreement_json_path"]),
            "agreement_report_markdown_path": str(manual_audit_workflow["agreement_markdown_path"]),
            "adjudication_report_json_path": str(manual_audit_workflow["adjudication_json_path"]),
            "adjudication_report_markdown_path": str(manual_audit_workflow["adjudication_markdown_path"]),
            "reviewer_readiness_json_path": str(
                manual_audit_workflow["reviewer_readiness_json_path"]
            ),
            "reviewer_readiness_markdown_path": str(
                manual_audit_workflow["reviewer_readiness_markdown_path"]
            ),
            "independent_reviewer_packet_validation_json_path": str(
                manual_audit_workflow["independent_reviewer_packet_validation_json_path"]
            ),
            "independent_reviewer_packet_validation_markdown_path": str(
                manual_audit_workflow["independent_reviewer_packet_validation_markdown_path"]
            ),
            "reviewer_readiness_status": manual_audit_workflow["reviewer_readiness"]["status"],
            "ready_for_submission_claims": manual_audit_workflow["reviewer_readiness"][
                "ready_for_submission_claims"
            ],
            "independent_completed_reviewer_packet_count": manual_audit_workflow[
                "reviewer_readiness"
            ]["independent_completed_reviewer_packet_count"],
            "reviewer_readiness_blocking_items": manual_audit_workflow["reviewer_readiness"][
                "blocking_items"
            ],
            "agreement_status": manual_audit_workflow["agreement_summary"]["status"],
            "exploratory_agreement_status": manual_audit_workflow["agreement_summary"][
                "exploratory_status"
            ],
            "eligible_reviewer_packet_count": manual_audit_workflow["agreement_summary"][
                "eligible_reviewer_packet_count"
            ],
            "exploratory_eligible_reviewer_packet_count": manual_audit_workflow["agreement_summary"][
                "exploratory_eligible_reviewer_packet_count"
            ],
            "pairwise_agreement_count": len(manual_audit_workflow["agreement_summary"]["pairwise_agreement"]),
            "exploratory_pairwise_agreement_count": len(
                manual_audit_workflow["agreement_summary"]["exploratory_pairwise_agreement"]
            ),
            "adjudication_entry_count": manual_audit_workflow["adjudication_queue"]["entry_count"],
            "scope_tracks": manual_audit_bundle.rubric["task_scope"]["include_tracks"],
            "case_count": manual_audit_bundle.summary["case_count"],
            "reviewed_task_count": manual_audit_bundle.summary["reviewed_task_count"],
            "dimension_count": manual_audit_bundle.summary["dimension_count"],
            "dimension_ids": manual_audit_bundle.summary["dimension_ids"],
            "task_ids": manual_audit_bundle.summary["task_ids"],
            "run_types": manual_audit_bundle.summary["run_types"],
            "per_dimension_means": manual_audit_bundle.summary["per_dimension_means"],
            "score_range": manual_audit_bundle.summary["score_range"],
        },
        "tasks_root": "tasks/pilot",
        "cards_root": "docs/cards",
        "data_manifests_root": "docs/data_manifests/pilot_v0",
        "task_count": len(tasks),
        "runnable_task_count": sum(1 for task in tasks if task["runnable"]),
        "tracks": tracks,
        "tasks": tasks,
        "protocols": PILOT_PROTOCOLS,
    }
    submission_readiness_artifacts = build_submission_readiness_artifacts(
        manifest=manifest,
        output_json_path=output_path / "submission_readiness.json",
        output_markdown_path=output_path / "submission_readiness.md",
    )
    manifest["submission_readiness"] = {
        "json_path": SUBMISSION_READINESS_JSON_PATH,
        "markdown_path": SUBMISSION_READINESS_MARKDOWN_PATH,
        "status": submission_readiness_artifacts["report"]["status"],
        "ready_for_workshop_submission": submission_readiness_artifacts["report"][
            "ready_for_workshop_submission"
        ],
        "gate_count": submission_readiness_artifacts["report"]["gate_count"],
        "ready_gate_count": submission_readiness_artifacts["report"]["ready_gate_count"],
        "blocking_gate_count": submission_readiness_artifacts["report"]["blocking_gate_count"],
        "blocking_items": submission_readiness_artifacts["report"]["blocking_items"],
    }

    output_path.mkdir(parents=True, exist_ok=True)
    manifest_path = output_path / "manifest.json"
    readme_path = output_path / "README.md"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    readme_path.write_text(render_release_readme(manifest), encoding="utf-8")

    return BenchmarkManifestBuildResult(
        manifest_path=manifest_path,
        readme_path=readme_path,
        cards_index_path=cards_result.index_path,
        data_manifests_readme_path=data_result.readme_path,
    )
