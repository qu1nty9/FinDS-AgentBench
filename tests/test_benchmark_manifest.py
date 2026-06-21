import json
from pathlib import Path

from finds_agentbench.benchmark_manifest import build_benchmark_manifest


def test_build_benchmark_manifest_generates_release_index(tmp_path: Path):
    cards_root = tmp_path / "cards"
    data_manifests_root = tmp_path / "data_manifests"
    output_root = tmp_path / "release"

    result = build_benchmark_manifest(
        tasks_root=Path("tasks/pilot"),
        cards_root=cards_root,
        data_manifests_root=data_manifests_root,
        output_root=output_root,
    )

    assert result.manifest_path.exists()
    assert result.readme_path.exists()
    assert result.cards_index_path.exists()
    assert result.data_manifests_readme_path.exists()

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    readme = result.readme_path.read_text(encoding="utf-8")

    assert manifest["benchmark_id"] == "finds_agentbench_pilot_v0"
    assert manifest["release_stage"] == "pilot"
    assert manifest["task_count"] >= 4
    assert manifest["runnable_task_count"] >= 3
    assert {"pilot_baseline_suite", "pilot_agent_suite", "pilot_protocol"}.issubset(
        {protocol["protocol_id"] for protocol in manifest["protocols"]}
    )

    etf_entry = next(task for task in manifest["tasks"] if task["task_id"] == "return_direction_etf_v0")
    market_entry = next(
        task for task in manifest["tasks"] if task["task_id"] == "synthetic_market_direction_v0"
    )
    assert etf_entry["runnable"] is False
    assert etf_entry["release_status"] == "spec_only_pending_data_review"
    assert market_entry["runnable"] is True
    assert market_entry["task_card_path"] == "docs/cards/tasks/synthetic_market_direction_v0.md"
    assert market_entry["data_manifest_path"] == "docs/data_manifests/pilot_v0/synthetic_market_direction_v0.json"
    assert "public_data_present" in market_entry
    assert "Canonical pilot release manifest for FinDS-AgentBench." in readme
    assert "../../cards/tasks/synthetic_market_direction_v0.md" in readme
    assert "../../data_manifests/pilot_v0/README.md" in readme
