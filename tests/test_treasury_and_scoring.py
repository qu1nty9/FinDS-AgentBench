from pathlib import Path

import pandas as pd

from finds_agentbench.scoring import score_yield_direction_treasury10y_submission
from finds_agentbench.treasury import (
    FEATURE_COLUMNS,
    train_yield_extra_trees_model,
    train_yield_previous_day_direction_baseline,
    train_yield_random_forest_model,
    write_yield_direction_task,
    write_yield_extra_trees_submission_artifacts,
    write_yield_logistic_submission_artifacts,
    write_yield_previous_day_direction_submission_artifacts,
    write_yield_random_forest_submission_artifacts,
)
from tests.treasury_test_utils import mock_treasury_source_frame


def test_write_yield_direction_task(tmp_path: Path):
    paths = write_yield_direction_task(
        output_dir=tmp_path / "public",
        private_dir=tmp_path / "private",
        source_frame=mock_treasury_source_frame(),
        observation_start="2017-01-03",
        observation_end="2022-03-31",
    )

    assert paths.train_public.exists()
    assert paths.private_holdout_features.exists()
    assert paths.sample_submission.exists()
    assert paths.answer_key.exists()

    holdout = pd.read_csv(paths.private_holdout_features)
    assert "next_day_yield_up" not in holdout.columns
    assert "next_day_change_bp" not in holdout.columns
    assert "next_day_directional_return" not in holdout.columns
    assert set(FEATURE_COLUMNS).issubset(holdout.columns)

    answer_key = pd.read_csv(paths.answer_key)
    assert {
        "row_id",
        "next_day_yield_up",
        "next_day_change_bp",
        "next_day_directional_return",
    }.issubset(answer_key.columns)


def test_write_yield_direction_task_reuses_matching_existing_snapshot(
    tmp_path: Path,
    monkeypatch,
):
    public_dir = tmp_path / "public"
    private_dir = tmp_path / "private"
    initial_paths = write_yield_direction_task(
        output_dir=public_dir,
        private_dir=private_dir,
        source_frame=mock_treasury_source_frame(),
        observation_start="2017-01-03",
        observation_end="2022-03-31",
        snapshot_date="2026-06-21",
    )
    metadata_before = initial_paths.metadata.read_text(encoding="utf-8")

    def fail_fetch(**kwargs):
        raise AssertionError(f"fetch_treasury_source_frame should not run: {kwargs}")

    monkeypatch.setattr("finds_agentbench.treasury.fetch_treasury_source_frame", fail_fetch)

    reused_paths = write_yield_direction_task(
        output_dir=public_dir,
        private_dir=private_dir,
        observation_start="2017-01-03",
        observation_end="2022-03-31",
        snapshot_date="2026-06-21",
    )

    assert reused_paths == initial_paths
    assert reused_paths.metadata.read_text(encoding="utf-8") == metadata_before


def test_score_yield_direction_submission(tmp_path: Path):
    paths = write_yield_direction_task(
        output_dir=tmp_path / "public",
        private_dir=tmp_path / "private",
        source_frame=mock_treasury_source_frame(),
        observation_start="2017-01-03",
        observation_end="2022-03-31",
    )

    holdout = pd.read_csv(paths.private_holdout_features)
    median_curve = float(holdout["curve_10y_2y"].median())
    predictions = pd.DataFrame(
        {
            "row_id": holdout["row_id"],
            "prediction": ["1" if value >= median_curve else "0" for value in holdout["curve_10y_2y"]],
            "probability": [
                "0.65" if value >= median_curve else "0.35" for value in holdout["curve_10y_2y"]
            ],
        }
    )
    submission_path = tmp_path / "predictions.csv"
    predictions.to_csv(submission_path, index=False)

    score = score_yield_direction_treasury10y_submission(
        submission_path=submission_path,
        answer_key_path=paths.answer_key,
    )

    assert score.task_id == "yield_direction_treasury10y_v0"
    assert score.execution_success == 1.0
    assert score.rows_scored > 0
    assert score.balanced_accuracy is not None
    assert 0.0 <= score.balanced_accuracy <= 1.0
    assert score.roc_auc is not None
    assert 0.0 <= score.roc_auc <= 1.0


def test_treasury_logistic_baseline_artifacts(tmp_path: Path):
    paths = write_yield_direction_task(
        output_dir=tmp_path / "public",
        private_dir=tmp_path / "private",
        source_frame=mock_treasury_source_frame(),
        observation_start="2017-01-03",
        observation_end="2022-03-31",
    )
    output_dir = tmp_path / "run"

    metadata = write_yield_logistic_submission_artifacts(
        train_public_path=paths.train_public,
        holdout_features_path=paths.private_holdout_features,
        output_dir=output_dir,
        random_state=29,
    )

    assert (output_dir / "predictions.csv").exists()
    assert (output_dir / "writeup.md").exists()
    assert (output_dir / "notebook.ipynb").exists()
    assert (output_dir / "baseline_metadata.json").exists()
    assert 0.0 <= metadata["public_validation_balanced_accuracy"] <= 1.0


def test_treasury_previous_day_baseline_artifacts(tmp_path: Path):
    paths = write_yield_direction_task(
        output_dir=tmp_path / "public",
        private_dir=tmp_path / "private",
        source_frame=mock_treasury_source_frame(),
        observation_start="2017-01-03",
        observation_end="2022-03-31",
    )

    metadata = write_yield_previous_day_direction_submission_artifacts(
        train_public_path=paths.train_public,
        holdout_features_path=paths.private_holdout_features,
        output_dir=tmp_path / "previous_day_run",
    )

    assert 0.0 <= metadata["probability_if_previous_day_up"] <= 1.0
    assert 0.0 <= metadata["probability_if_previous_day_nonpositive"] <= 1.0
    assert 0.0 <= metadata["public_validation_balanced_accuracy"] <= 1.0


def test_treasury_tree_baselines_train_and_write_artifacts(tmp_path: Path):
    paths = write_yield_direction_task(
        output_dir=tmp_path / "public",
        private_dir=tmp_path / "private",
        source_frame=mock_treasury_source_frame(),
        observation_start="2017-01-03",
        observation_end="2022-03-31",
    )

    _, rf_metadata = train_yield_random_forest_model(paths.train_public, random_state=29)
    _, extra_metadata = train_yield_extra_trees_model(paths.train_public, random_state=29)
    previous_day_metadata = train_yield_previous_day_direction_baseline(paths.train_public)

    rf_output_dir = tmp_path / "rf_run"
    extra_output_dir = tmp_path / "extra_run"
    write_yield_random_forest_submission_artifacts(
        train_public_path=paths.train_public,
        holdout_features_path=paths.private_holdout_features,
        output_dir=rf_output_dir,
        random_state=29,
    )
    write_yield_extra_trees_submission_artifacts(
        train_public_path=paths.train_public,
        holdout_features_path=paths.private_holdout_features,
        output_dir=extra_output_dir,
        random_state=29,
    )

    assert rf_metadata["baseline_family"] == "random_forest"
    assert extra_metadata["baseline_family"] == "extra_trees"
    assert previous_day_metadata["baseline_family"] == "previous_day_direction_rule"
    assert (rf_output_dir / "predictions.csv").exists()
    assert (extra_output_dir / "predictions.csv").exists()
