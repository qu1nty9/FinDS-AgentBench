from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from finds_agentbench.task_cards import build_task_cards, markdown_table


BENCHMARK_ID = "finds_agentbench_pilot_v0"
BENCHMARK_VERSION = "0.1.0"
RELEASE_STAGE = "pilot"

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
    "return_direction_etf_v0": {
        "runnable": False,
        "release_status": "spec_only_pending_data_review",
        "blocked_reason": "License-safe public data source is still pending review.",
        "default_commands": [
            "PYTHONPATH=src python scripts/validate_task.py tasks/pilot/return_direction_etf_v0.yaml",
        ],
    },
    "synthetic_event_response_v0": {
        "runnable": True,
        "release_status": "runnable_public_pilot",
        "blocked_reason": None,
        "default_commands": [
            "PYTHONPATH=src python scripts/generate_synthetic_event_response_v0.py --seed 23",
            "PYTHONPATH=src python scripts/run_synthetic_event_response_rule_pipeline.py",
            "PYTHONPATH=src python scripts/run_synthetic_event_response_agent_suite.py --agent-id event_rule_env_agent --agent-version 0.1.0 --agent-command \"python agents/examples/event_rule_env_agent.py\" --repeat 3 --seed 23 --run-label-prefix pilot_event_agent",
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
            "PYTHONPATH=src python scripts/run_synthetic_market_agent_suite.py --agent-id momentum_env_agent --agent-version 0.1.0 --agent-command \"python agents/examples/momentum_env_agent.py\" --repeat 3 --seed 11 --run-label-prefix pilot_agent",
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
        ],
        "runs_root": "runs/suites/pilot_baselines_v0",
        "command": "PYTHONPATH=src python scripts/run_pilot_baseline_suite.py --repeat 3 --market-seed 11 --event-seed 23 --run-label-prefix pilot",
    },
    {
        "protocol_id": "pilot_agent_suite",
        "status": "active",
        "run_types": ["agent"],
        "task_ids": [
            "synthetic_market_direction_v0",
            "synthetic_event_response_v0",
        ],
        "runs_root": "runs/suites/pilot_agents_v0",
        "command": "PYTHONPATH=src python scripts/run_pilot_agent_suite.py --repeat 3 --market-seed 11 --event-seed 23 --run-label-prefix pilot_agent",
    },
    {
        "protocol_id": "pilot_protocol",
        "status": "active",
        "run_types": ["baseline", "agent"],
        "task_ids": [
            "synthetic_market_direction_v0",
            "synthetic_event_response_v0",
        ],
        "runs_root": "runs/suites/pilot_protocol_v0",
        "command": "PYTHONPATH=src python scripts/run_pilot_protocol.py --repeat 3 --market-seed 11 --event-seed 23 --run-label-prefix pilot_protocol",
    },
]


@dataclass(frozen=True)
class BenchmarkManifestBuildResult:
    manifest_path: Path
    readme_path: Path
    cards_index_path: Path


def build_task_release_entry(entry: dict[str, Any]) -> dict[str, Any]:
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
    }


def render_release_readme(manifest: dict[str, Any]) -> str:
    task_rows = [
        [
            task["task_id"],
            task["track"],
            task["status"],
            task["release_status"],
            "yes" if task["runnable"] else "no",
            f"[task](../../cards/tasks/{task['task_id']}.md)",
            f"[evaluation](../../cards/evaluations/{task['task_id']}.md)",
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
                ["Task ID", "Track", "Spec Status", "Release Status", "Runnable", "Task Card", "Evaluation Card"],
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
    output_root: str | Path = "docs/releases/pilot_v0",
) -> BenchmarkManifestBuildResult:
    cards_result = build_task_cards(tasks_root=tasks_root, output_root=cards_root)
    registry_entries = json.loads(cards_result.registry_json_path.read_text(encoding="utf-8"))
    tasks = [build_task_release_entry(entry) for entry in registry_entries]

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
        "tasks_root": str(tasks_root),
        "cards_root": str(cards_root),
        "task_count": len(tasks),
        "runnable_task_count": sum(1 for task in tasks if task["runnable"]),
        "tracks": tracks,
        "tasks": tasks,
        "protocols": PILOT_PROTOCOLS,
    }

    output_path = Path(output_root)
    output_path.mkdir(parents=True, exist_ok=True)
    manifest_path = output_path / "manifest.json"
    readme_path = output_path / "README.md"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    readme_path.write_text(render_release_readme(manifest), encoding="utf-8")

    return BenchmarkManifestBuildResult(
        manifest_path=manifest_path,
        readme_path=readme_path,
        cards_index_path=cards_result.index_path,
    )
