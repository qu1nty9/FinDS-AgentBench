from pathlib import Path

import pandas as pd

from finds_agentbench.scoring import score_front_end_spread_widening_submission
from finds_agentbench.treasury import write_yield_direction_task
from finds_agentbench.front_end import (
    FEATURE_COLUMNS,
    train_front_end_extra_trees_model,
    train_front_end_previous_day_direction_baseline,
    train_front_end_random_forest_model,
    write_front_end_extra_trees_submission_artifacts,
    write_front_end_logistic_submission_artifacts,
    write_front_end_previous_day_direction_submission_artifacts,
    write_front_end_random_forest_submission_artifacts,
    write_front_end_spread_widening_task,
)
from tests.treasury_test_utils import mock_treasury_source_frame


def test_write_front_end_spread_widening_task(tmp_path: Path):
    paths = write_front_end_spread_widening_task(
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
    assert "next_day_front_end_widening" not in holdout.columns
    assert "next_day_front_end_change_bp" not in holdout.columns
    assert "next_day_directional_return" not in holdout.columns
    assert set(FEATURE_COLUMNS).issubset(holdout.columns)

    answer_key = pd.read_csv(paths.answer_key)
    assert {
        "row_id",
        "next_day_front_end_widening",
        "next_day_front_end_change_bp",
        "next_day_directional_return",
    }.issubset(answer_key.columns)


def test_write_front_end_task_reuses_existing_treasury_snapshot(
    tmp_path: Path,
    monkeypatch,
):
    treasury_public = tmp_path / "treasury_public"
    treasury_private = tmp_path / "treasury_private"
    treasury_paths = write_yield_direction_task(
        output_dir=treasury_public,
        private_dir=treasury_private,
        source_frame=mock_treasury_source_frame(),
        observation_start="2017-01-03",
        observation_end="2022-03-31",
        snapshot_date="2026-06-21",
    )

    def fail_fetch(**kwargs):
        raise AssertionError(f"fetch_treasury_source_frame should not run: {kwargs}")

    monkeypatch.setattr("finds_agentbench.front_end.fetch_treasury_source_frame", fail_fetch)

    paths = write_front_end_spread_widening_task(
        output_dir=tmp_path / "curve_public",
        private_dir=tmp_path / "curve_private",
        observation_start="2017-01-03",
        observation_end="2022-03-31",
        snapshot_date="2026-06-21",
        treasury_train_public_path=treasury_paths.train_public,
        treasury_holdout_features_path=treasury_paths.private_holdout_features,
        treasury_metadata_path=treasury_paths.metadata,
    )

    metadata = pd.read_json(paths.metadata, typ="series")
    assert metadata["source_mode"] == "derived_from_existing_treasury_snapshot"
    assert paths.train_public.exists()
    assert paths.answer_key.exists()


def test_score_front_end_spread_widening_submission(tmp_path: Path):
    paths = write_front_end_spread_widening_task(
        output_dir=tmp_path / "public",
        private_dir=tmp_path / "private",
        source_frame=mock_treasury_source_frame(),
        observation_start="2017-01-03",
        observation_end="2022-03-31",
    )

    holdout = pd.read_csv(paths.private_holdout_features)
    median_front_end = float(holdout["front_end_spread"].median())
    predictions = pd.DataFrame(
        {
            "row_id": holdout["row_id"],
            "prediction": [
                "1" if value >= median_front_end else "0" for value in holdout["front_end_spread"]
            ],
            "probability": [
                "0.65" if value >= median_front_end else "0.35"
                for value in holdout["front_end_spread"]
            ],
        }
    )
    submission_path = tmp_path / "predictions.csv"
    predictions.to_csv(submission_path, index=False)

    score = score_front_end_spread_widening_submission(
        submission_path=submission_path,
        answer_key_path=paths.answer_key,
    )

    assert score.task_id == "front_end_spread_widening_v0"
    assert score.execution_success == 1.0
    assert score.rows_scored > 0
    assert score.balanced_accuracy is not None
    assert 0.0 <= score.balanced_accuracy <= 1.0
    assert score.roc_auc is not None
    assert 0.0 <= score.roc_auc <= 1.0


def test_front_end_logistic_baseline_artifacts(tmp_path: Path):
    paths = write_front_end_spread_widening_task(
        output_dir=tmp_path / "public",
        private_dir=tmp_path / "private",
        source_frame=mock_treasury_source_frame(),
        observation_start="2017-01-03",
        observation_end="2022-03-31",
    )
    output_dir = tmp_path / "run"

    metadata = write_front_end_logistic_submission_artifacts(
        train_public_path=paths.train_public,
        holdout_features_path=paths.private_holdout_features,
        output_dir=output_dir,
        random_state=41,
    )

    assert (output_dir / "predictions.csv").exists()
    assert (output_dir / "writeup.md").exists()
    assert (output_dir / "notebook.ipynb").exists()
    assert (output_dir / "baseline_metadata.json").exists()
    assert 0.0 <= metadata["public_validation_balanced_accuracy"] <= 1.0


def test_front_end_previous_day_baseline_artifacts(tmp_path: Path):
    paths = write_front_end_spread_widening_task(
        output_dir=tmp_path / "public",
        private_dir=tmp_path / "private",
        source_frame=mock_treasury_source_frame(),
        observation_start="2017-01-03",
        observation_end="2022-03-31",
    )

    metadata = write_front_end_previous_day_direction_submission_artifacts(
        train_public_path=paths.train_public,
        holdout_features_path=paths.private_holdout_features,
        output_dir=tmp_path / "previous_day_run",
    )

    assert 0.0 <= metadata["probability_if_previous_day_widened"] <= 1.0
    assert 0.0 <= metadata["probability_if_previous_day_nonpositive"] <= 1.0
    assert 0.0 <= metadata["public_validation_balanced_accuracy"] <= 1.0


def test_front_end_tree_baselines_train_and_write_artifacts(tmp_path: Path):
    paths = write_front_end_spread_widening_task(
        output_dir=tmp_path / "public",
        private_dir=tmp_path / "private",
        source_frame=mock_treasury_source_frame(),
        observation_start="2017-01-03",
        observation_end="2022-03-31",
    )

    _, rf_metadata = train_front_end_random_forest_model(paths.train_public, random_state=41)
    _, extra_metadata = train_front_end_extra_trees_model(paths.train_public, random_state=41)
    previous_day_metadata = train_front_end_previous_day_direction_baseline(paths.train_public)

    rf_output_dir = tmp_path / "rf_run"
    extra_output_dir = tmp_path / "extra_run"
    write_front_end_random_forest_submission_artifacts(
        train_public_path=paths.train_public,
        holdout_features_path=paths.private_holdout_features,
        output_dir=rf_output_dir,
        random_state=41,
    )
    write_front_end_extra_trees_submission_artifacts(
        train_public_path=paths.train_public,
        holdout_features_path=paths.private_holdout_features,
        output_dir=extra_output_dir,
        random_state=41,
    )

    assert rf_metadata["baseline_family"] == "random_forest"
    assert extra_metadata["baseline_family"] == "extra_trees"
    assert previous_day_metadata["baseline_family"] == "previous_day_direction_rule"
    assert (rf_output_dir / "predictions.csv").exists()
    assert (extra_output_dir / "predictions.csv").exists()
