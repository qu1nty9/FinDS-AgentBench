import csv
import json
from pathlib import Path

from finds_agentbench.task_cards import build_task_cards


def test_build_task_cards_generates_cards_and_registry(tmp_path: Path):
    output_root = tmp_path / "cards"

    result = build_task_cards(
        tasks_root=Path("tasks/pilot"),
        output_root=output_root,
    )

    generated_task_ids = {path.stem for path in result.task_card_paths}
    expected_task_ids = {
        "leakage_audit_temporal_split_v0",
        "return_direction_etf_v0",
        "synthetic_event_response_v0",
        "synthetic_market_direction_v0",
    }

    assert expected_task_ids.issubset(generated_task_ids)
    assert expected_task_ids.issubset({path.stem for path in result.evaluation_card_paths})
    assert result.registry_json_path.exists()
    assert result.registry_csv_path.exists()
    assert result.index_path.exists()

    market_task_card = (output_root / "tasks" / "synthetic_market_direction_v0.md").read_text(
        encoding="utf-8"
    )
    market_eval_card = (
        output_root / "evaluations" / "synthetic_market_direction_v0.md"
    ).read_text(encoding="utf-8")
    index_text = result.index_path.read_text(encoding="utf-8")

    assert "# synthetic_market_direction_v0 Task Card" in market_task_card
    assert "Synthetic Market Next-Day Direction Prediction" in market_task_card
    assert "balanced_accuracy_on_private_temporal_holdout" in market_eval_card
    assert "[task](tasks/synthetic_market_direction_v0.md)" in index_text
    assert "[evaluation](evaluations/synthetic_market_direction_v0.md)" in index_text

    registry_entries = json.loads(result.registry_json_path.read_text(encoding="utf-8"))
    assert expected_task_ids.issubset({entry["task_id"] for entry in registry_entries})
    market_entry = next(
        entry for entry in registry_entries if entry["task_id"] == "synthetic_market_direction_v0"
    )
    assert market_entry["primary_metric"] == "balanced_accuracy_on_private_temporal_holdout"
    assert market_entry["data_access"] == "synthetic_generator"

    with result.registry_csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert expected_task_ids.issubset({row["task_id"] for row in rows})
