from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import nbformat
import pandas as pd

from finds_agentbench.treasury import (
    DEFAULT_REALTIME_SNAPSHOT_DATE,
    choose_threshold,
    clip_probability,
    fetch_fred_series,
    write_probability_predictions,
)


TASK_ID = "usd_broad_direction_v0"
ASSET_ID = "usd_nominal_broad_index"
DEFAULT_OBSERVATION_START = "2006-01-03"
DEFAULT_OBSERVATION_END = "2026-01-02"
SERIES_IDS = {
    "usd_broad": "DTWEXBGS",
    "usd_afe": "DTWEXAFEGS",
    "usd_eme": "DTWEXEMEGS",
    "dgs2": "DGS2",
    "dgs10": "DGS10",
    "dff": "DFF",
}
FEATURE_COLUMNS = [
    "usd_broad_level",
    "usd_afe_level",
    "usd_eme_level",
    "dgs2_level",
    "dgs10_level",
    "dff_level",
    "usd_broad_return_1d",
    "usd_broad_return_5d",
    "usd_afe_return_1d",
    "usd_eme_return_1d",
    "usd_afe_minus_eme",
    "usd_broad_minus_20d_mean",
    "usd_broad_vol_5d",
    "usd_broad_vol_20d",
    "term_spread_10y_2y",
    "front_end_spread",
]
TRAIN_END = date(2018, 12, 31)
PUBLIC_VALIDATION_END = date(2021, 12, 31)
PRIVATE_HOLDOUT_END = date(2025, 12, 31)


@dataclass(frozen=True)
class USDBroadTaskPaths:
    train_public: Path
    private_holdout_features: Path
    sample_submission: Path
    metadata: Path
    answer_key: Path


def split_for_date(value: date) -> str:
    if value <= TRAIN_END:
        return "train"
    if value <= PUBLIC_VALIDATION_END:
        return "public_validation"
    if value <= PRIVATE_HOLDOUT_END:
        return "private_temporal_holdout"
    return "excluded"


def fetch_usd_broad_source_frame(
    *,
    api_key: str | None = None,
    observation_start: str = DEFAULT_OBSERVATION_START,
    observation_end: str = DEFAULT_OBSERVATION_END,
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
) -> pd.DataFrame:
    usd_broad = fetch_fred_series(
        SERIES_IDS["usd_broad"],
        api_key=api_key,
        observation_start=observation_start,
        observation_end=observation_end,
        snapshot_date=snapshot_date,
    ).rename("usd_broad")
    frame = usd_broad.to_frame()

    for column_name, series_id in SERIES_IDS.items():
        if column_name == "usd_broad":
            continue
        series = fetch_fred_series(
            series_id,
            api_key=api_key,
            observation_start=observation_start,
            observation_end=observation_end,
            snapshot_date=snapshot_date,
        ).rename(column_name)
        frame = frame.join(series, how="left")

    frame[["dgs2", "dgs10", "dff"]] = frame[["dgs2", "dgs10", "dff"]].ffill(limit=5)
    frame = frame.dropna().sort_index()
    frame.index.name = "date"
    return frame


def build_usd_broad_direction_frame(source_frame: pd.DataFrame) -> pd.DataFrame:
    if source_frame.empty:
        raise ValueError("source_frame must contain observations.")

    frame = source_frame.copy().sort_index()
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise TypeError("source_frame index must be a pandas DatetimeIndex.")

    required_columns = set(SERIES_IDS)
    missing_columns = required_columns - set(frame.columns)
    if missing_columns:
        raise ValueError(f"source_frame is missing required columns: {sorted(missing_columns)}")

    frame["usd_broad_return_1d"] = frame["usd_broad"].pct_change(1)
    frame["usd_broad_return_5d"] = frame["usd_broad"].pct_change(5)
    frame["usd_afe_return_1d"] = frame["usd_afe"].pct_change(1)
    frame["usd_eme_return_1d"] = frame["usd_eme"].pct_change(1)
    frame["usd_afe_minus_eme"] = frame["usd_afe"] - frame["usd_eme"]
    daily_return = frame["usd_broad"].pct_change(1)
    frame["usd_broad_vol_5d"] = daily_return.rolling(5).std()
    frame["usd_broad_vol_20d"] = daily_return.rolling(20).std()
    frame["usd_broad_minus_20d_mean"] = frame["usd_broad"] - frame["usd_broad"].rolling(20).mean()
    frame["term_spread_10y_2y"] = frame["dgs10"] - frame["dgs2"]
    frame["front_end_spread"] = frame["dgs2"] - frame["dff"]
    frame["next_day_return"] = frame["usd_broad"].shift(-1) / frame["usd_broad"] - 1.0
    frame["next_day_usd_broad_up"] = (frame["next_day_return"] > 0.0).astype(int)
    frame["split"] = [split_for_date(timestamp.date()) for timestamp in frame.index]
    frame = frame.rename(
        columns={
            "usd_broad": "usd_broad_level",
            "usd_afe": "usd_afe_level",
            "usd_eme": "usd_eme_level",
            "dgs2": "dgs2_level",
            "dgs10": "dgs10_level",
            "dff": "dff_level",
        }
    )

    frame = frame.dropna(subset=FEATURE_COLUMNS + ["next_day_return"])
    frame = frame.loc[frame["split"] != "excluded"].copy()
    frame["asset_id"] = ASSET_ID
    frame["row_id"] = [
        f"{timestamp.date().isoformat()}_{ASSET_ID}" for timestamp in frame.index.to_pydatetime()
    ]
    frame["date"] = frame.index.strftime("%Y-%m-%d")

    ordered_columns = [
        "row_id",
        "date",
        "asset_id",
        "split",
        *FEATURE_COLUMNS,
        "next_day_usd_broad_up",
        "next_day_return",
    ]
    return frame.loc[:, ordered_columns]


def _format_numeric_frame(frame: pd.DataFrame) -> pd.DataFrame:
    formatted = frame.copy()
    for column in formatted.columns:
        if pd.api.types.is_float_dtype(formatted[column]):
            formatted[column] = formatted[column].map(lambda value: f"{value:.8f}")
        elif pd.api.types.is_integer_dtype(formatted[column]):
            formatted[column] = formatted[column].map(str)
    return formatted


def _resolve_source_mode(api_key: str | None, snapshot_date: str | None) -> str:
    if api_key or os.environ.get("FRED_API_KEY"):
        return "fred_api_realtime_snapshot" if snapshot_date is not None else "fred_api_current"
    if snapshot_date is not None:
        return "alfred_graph_vintage_snapshot"
    return "fred_graph_current"


def _resolve_existing_task_paths(
    output_path: Path,
    private_path: Path,
) -> USDBroadTaskPaths | None:
    candidate = USDBroadTaskPaths(
        train_public=output_path / "train_public.csv",
        private_holdout_features=output_path / "private_holdout_features.csv",
        sample_submission=output_path / "sample_submission.csv",
        metadata=output_path / "metadata.json",
        answer_key=private_path / "answer_key.csv",
    )
    required_paths = (
        candidate.train_public,
        candidate.private_holdout_features,
        candidate.sample_submission,
        candidate.metadata,
        candidate.answer_key,
    )
    if all(path.exists() for path in required_paths):
        return candidate
    return None


def _existing_task_matches_request(
    *,
    metadata_path: Path,
    observation_start: str,
    observation_end: str,
    snapshot_date: str | None,
) -> bool:
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return (
        metadata.get("task_id") == TASK_ID
        and metadata.get("observation_start") == observation_start
        and metadata.get("observation_end") == observation_end
        and metadata.get("snapshot_date") == snapshot_date
    )


def write_usd_broad_direction_task(
    *,
    output_dir: str | Path = "data/raw/usd_broad_direction_v0",
    private_dir: str | Path = "data/private/usd_broad_direction_v0",
    api_key: str | None = None,
    observation_start: str = DEFAULT_OBSERVATION_START,
    observation_end: str = DEFAULT_OBSERVATION_END,
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    source_frame: pd.DataFrame | None = None,
) -> USDBroadTaskPaths:
    output_path = Path(output_dir)
    private_path = Path(private_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    private_path.mkdir(parents=True, exist_ok=True)

    existing_paths = _resolve_existing_task_paths(output_path, private_path)
    if (
        source_frame is None
        and existing_paths is not None
        and _existing_task_matches_request(
            metadata_path=existing_paths.metadata,
            observation_start=observation_start,
            observation_end=observation_end,
            snapshot_date=snapshot_date,
        )
    ):
        return existing_paths

    source = source_frame if source_frame is not None else fetch_usd_broad_source_frame(
        api_key=api_key,
        observation_start=observation_start,
        observation_end=observation_end,
        snapshot_date=snapshot_date,
    )
    task_frame = build_usd_broad_direction_frame(source)
    formatted = _format_numeric_frame(task_frame)

    feature_columns = [
        "row_id",
        "date",
        "asset_id",
        "split",
        *FEATURE_COLUMNS,
    ]
    public_columns = feature_columns + ["next_day_usd_broad_up", "next_day_return"]
    answer_columns = [
        "row_id",
        "date",
        "asset_id",
        "next_day_usd_broad_up",
        "next_day_return",
    ]

    train_public = formatted.loc[formatted["split"] != "private_temporal_holdout", public_columns]
    holdout = formatted.loc[formatted["split"] == "private_temporal_holdout"]

    train_public_path = output_path / "train_public.csv"
    holdout_features_path = output_path / "private_holdout_features.csv"
    sample_submission_path = output_path / "sample_submission.csv"
    metadata_path = output_path / "metadata.json"
    answer_key_path = private_path / "answer_key.csv"

    train_public.to_csv(train_public_path, index=False)
    holdout.loc[:, feature_columns].to_csv(holdout_features_path, index=False)
    pd.DataFrame(
        {
            "row_id": holdout["row_id"],
            "prediction": "0",
            "probability": "0.5",
        }
    ).to_csv(sample_submission_path, index=False)
    holdout.loc[:, answer_columns].to_csv(answer_key_path, index=False)

    metadata = {
        "task_id": TASK_ID,
        "asset_id": ASSET_ID,
        "source_series": SERIES_IDS,
        "observation_start": observation_start,
        "observation_end": observation_end,
        "snapshot_date": snapshot_date,
        "source_mode": "provided_source_frame"
        if source_frame is not None
        else _resolve_source_mode(api_key, snapshot_date),
        "splits": {
            "train": {
                "start": str(task_frame.loc[task_frame["split"] == "train", "date"].min()),
                "end": str(task_frame.loc[task_frame["split"] == "train", "date"].max()),
            },
            "public_validation": {
                "start": str(task_frame.loc[task_frame["split"] == "public_validation", "date"].min()),
                "end": str(task_frame.loc[task_frame["split"] == "public_validation", "date"].max()),
            },
            "private_temporal_holdout": {
                "start": str(
                    task_frame.loc[task_frame["split"] == "private_temporal_holdout", "date"].min()
                ),
                "end": str(
                    task_frame.loc[task_frame["split"] == "private_temporal_holdout", "date"].max()
                ),
            },
        },
        "feature_columns": FEATURE_COLUMNS,
        "target": "next_day_usd_broad_up",
        "return_column": "next_day_return",
        "forbidden_private_columns": [
            "next_day_usd_broad_up",
            "next_day_return",
        ],
        "row_count": int(len(task_frame)),
        "private_holdout_row_count": int((task_frame["split"] == "private_temporal_holdout").sum()),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return USDBroadTaskPaths(
        train_public=train_public_path,
        private_holdout_features=holdout_features_path,
        sample_submission=sample_submission_path,
        metadata=metadata_path,
        answer_key=answer_key_path,
    )


def load_usd_broad_train_validation_rows(train_public_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = pd.read_csv(train_public_path)
    train_rows = frame.loc[frame["split"] == "train"].copy()
    validation_rows = frame.loc[frame["split"] == "public_validation"].copy()
    if train_rows.empty:
        raise ValueError("No train rows found in train_public data.")
    if validation_rows.empty:
        raise ValueError("No public_validation rows found in train_public data.")
    return train_rows, validation_rows


def train_usd_broad_sklearn_probability_model(
    train_public_path: Path,
    *,
    estimator,
    model_name: str,
    random_state: int,
) -> tuple[Any, dict[str, Any]]:
    train_rows, validation_rows = load_usd_broad_train_validation_rows(train_public_path)
    estimator.fit(train_rows[FEATURE_COLUMNS], train_rows["next_day_usd_broad_up"].astype(int))
    validation_probabilities = pd.Series(
        estimator.predict_proba(validation_rows[FEATURE_COLUMNS])[:, 1],
        index=validation_rows.index,
    )
    threshold, validation_balanced_accuracy = choose_threshold(
        validation_rows["next_day_usd_broad_up"],
        validation_probabilities,
    )
    return estimator, {
        "baseline_family": model_name,
        "feature_columns": FEATURE_COLUMNS,
        "random_state": random_state,
        "train_rows": int(len(train_rows)),
        "public_validation_rows": int(len(validation_rows)),
        "selected_threshold": threshold,
        "public_validation_balanced_accuracy": validation_balanced_accuracy,
    }


def write_usd_broad_baseline_writeup(
    output_path: Path,
    *,
    title: str,
    body_lines: list[str],
    metadata: dict[str, Any],
) -> None:
    lines = [f"# {title}", "", *body_lines, ""]
    if "selected_threshold" in metadata:
        lines.append(f"Selected threshold: `{metadata['selected_threshold']}`.")
    if "public_validation_balanced_accuracy" in metadata:
        lines.append(
            "Public validation balanced accuracy: "
            f"`{metadata['public_validation_balanced_accuracy']:.6f}`."
        )
    lines.extend(
        [
            "",
            "The baseline does not read private labels, answer keys, or future dollar-index moves during prediction generation.",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_usd_broad_baseline_notebook(output_path: Path) -> None:
    notebook = nbformat.v4.new_notebook()
    notebook.cells = [
        nbformat.v4.new_markdown_cell("# USD Broad Direction Baseline Submission Check"),
        nbformat.v4.new_code_cell(
            "\n".join(
                [
                    "from pathlib import Path",
                    "for path in ['predictions.csv', 'writeup.md', 'baseline_metadata.json']:",
                    "    assert Path(path).exists(), f'missing {path}'",
                    "print('USD broad direction baseline artifacts are present.')",
                ]
            )
        ),
    ]
    nbformat.write(notebook, output_path)


def finalize_usd_broad_submission_artifacts(
    *,
    output_dir: Path,
    metadata: dict[str, Any],
    title: str,
    body_lines: list[str],
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_usd_broad_baseline_writeup(
        output_dir / "writeup.md",
        title=title,
        body_lines=body_lines,
        metadata=metadata,
    )
    write_usd_broad_baseline_notebook(output_dir / "notebook.ipynb")
    (output_dir / "baseline_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metadata


def train_usd_broad_logistic_model(train_public_path: Path, *, random_state: int = 37):
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "The USD broad logistic baseline requires scikit-learn."
        ) from exc

    estimator = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=1000, random_state=random_state),
    )
    return train_usd_broad_sklearn_probability_model(
        train_public_path,
        estimator=estimator,
        model_name="logistic_regression",
        random_state=random_state,
    )


def train_usd_broad_random_forest_model(train_public_path: Path, *, random_state: int = 37):
    try:
        from sklearn.ensemble import RandomForestClassifier
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "The USD broad random forest baseline requires scikit-learn."
        ) from exc

    estimator = RandomForestClassifier(
        n_estimators=400,
        min_samples_leaf=5,
        random_state=random_state,
        n_jobs=1,
    )
    return train_usd_broad_sklearn_probability_model(
        train_public_path,
        estimator=estimator,
        model_name="random_forest",
        random_state=random_state,
    )


def train_usd_broad_extra_trees_model(train_public_path: Path, *, random_state: int = 37):
    try:
        from sklearn.ensemble import ExtraTreesClassifier
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "The USD broad extra trees baseline requires scikit-learn."
        ) from exc

    estimator = ExtraTreesClassifier(
        n_estimators=400,
        min_samples_leaf=5,
        random_state=random_state,
        n_jobs=1,
    )
    return train_usd_broad_sklearn_probability_model(
        train_public_path,
        estimator=estimator,
        model_name="extra_trees",
        random_state=random_state,
    )


def train_usd_broad_previous_day_direction_baseline(
    train_public_path: Path,
) -> dict[str, Any]:
    train_rows, validation_rows = load_usd_broad_train_validation_rows(train_public_path)
    train_indicator = train_rows["usd_broad_return_1d"] > 0
    train_rate = float(train_rows["next_day_usd_broad_up"].astype(int).mean())
    up_rate = clip_probability(
        float(train_rows.loc[train_indicator, "next_day_usd_broad_up"].astype(int).mean())
        if train_indicator.any()
        else train_rate
    )
    down_rate = clip_probability(
        float(train_rows.loc[~train_indicator, "next_day_usd_broad_up"].astype(int).mean())
        if (~train_indicator).any()
        else train_rate
    )
    validation_probabilities = pd.Series(
        [
            up_rate if indicator else down_rate
            for indicator in (validation_rows["usd_broad_return_1d"] > 0).tolist()
        ],
        index=validation_rows.index,
    )
    threshold, validation_balanced_accuracy = choose_threshold(
        validation_rows["next_day_usd_broad_up"],
        validation_probabilities,
    )
    return {
        "baseline_family": "previous_day_direction_rule",
        "feature_columns": ["usd_broad_return_1d"],
        "train_rows": int(len(train_rows)),
        "public_validation_rows": int(len(validation_rows)),
        "probability_if_previous_day_up": up_rate,
        "probability_if_previous_day_nonpositive": down_rate,
        "selected_threshold": threshold,
        "public_validation_balanced_accuracy": validation_balanced_accuracy,
    }


def write_usd_broad_logistic_predictions(
    model,
    *,
    holdout_features_path: Path,
    output_path: Path,
    threshold: float,
) -> None:
    frame = pd.read_csv(holdout_features_path)
    probabilities = pd.Series(model.predict_proba(frame[FEATURE_COLUMNS])[:, 1], index=frame.index)
    write_probability_predictions(
        row_ids=frame["row_id"],
        probabilities=probabilities,
        output_path=output_path,
        threshold=threshold,
    )


def write_usd_broad_random_forest_predictions(
    model,
    *,
    holdout_features_path: Path,
    output_path: Path,
    threshold: float,
) -> None:
    frame = pd.read_csv(holdout_features_path)
    probabilities = pd.Series(model.predict_proba(frame[FEATURE_COLUMNS])[:, 1], index=frame.index)
    write_probability_predictions(
        row_ids=frame["row_id"],
        probabilities=probabilities,
        output_path=output_path,
        threshold=threshold,
    )


def write_usd_broad_extra_trees_predictions(
    model,
    *,
    holdout_features_path: Path,
    output_path: Path,
    threshold: float,
) -> None:
    frame = pd.read_csv(holdout_features_path)
    probabilities = pd.Series(model.predict_proba(frame[FEATURE_COLUMNS])[:, 1], index=frame.index)
    write_probability_predictions(
        row_ids=frame["row_id"],
        probabilities=probabilities,
        output_path=output_path,
        threshold=threshold,
    )


def write_usd_broad_previous_day_direction_predictions(
    *,
    holdout_features_path: Path,
    output_path: Path,
    threshold: float,
    probability_if_previous_day_up: float,
    probability_if_previous_day_nonpositive: float,
) -> None:
    frame = pd.read_csv(holdout_features_path)
    probabilities = pd.Series(
        [
            probability_if_previous_day_up if value > 0 else probability_if_previous_day_nonpositive
            for value in frame["usd_broad_return_1d"]
        ],
        index=frame.index,
    )
    write_probability_predictions(
        row_ids=frame["row_id"],
        probabilities=probabilities,
        output_path=output_path,
        threshold=threshold,
    )


def write_usd_broad_logistic_submission_artifacts(
    *,
    train_public_path: Path,
    holdout_features_path: Path,
    output_dir: Path,
    random_state: int = 37,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    model, metadata = train_usd_broad_logistic_model(train_public_path, random_state=random_state)
    write_usd_broad_logistic_predictions(
        model,
        holdout_features_path=holdout_features_path,
        output_path=output_dir / "predictions.csv",
        threshold=float(metadata["selected_threshold"]),
    )
    return finalize_usd_broad_submission_artifacts(
        output_dir=output_dir,
        metadata=metadata,
        title="USD Broad Direction Logistic Regression Baseline",
        body_lines=[
            "This baseline trains a logistic regression model on the chronological train split only.",
            "Feature scaling is fit on the train split and reused on public validation and private holdout rows.",
            "The model mixes point-in-time broad dollar, AFE, EME, and short-rate context.",
        ],
    )


def write_usd_broad_random_forest_submission_artifacts(
    *,
    train_public_path: Path,
    holdout_features_path: Path,
    output_dir: Path,
    random_state: int = 37,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    model, metadata = train_usd_broad_random_forest_model(
        train_public_path,
        random_state=random_state,
    )
    write_usd_broad_random_forest_predictions(
        model,
        holdout_features_path=holdout_features_path,
        output_path=output_dir / "predictions.csv",
        threshold=float(metadata["selected_threshold"]),
    )
    return finalize_usd_broad_submission_artifacts(
        output_dir=output_dir,
        metadata=metadata,
        title="USD Broad Direction Random Forest Baseline",
        body_lines=[
            "This baseline trains a random forest classifier on the chronological train split only.",
            "It captures nonlinear interactions among broad-dollar dynamics, AFE and EME moves, and rates features.",
            "The classification threshold is selected on the public validation split only.",
        ],
    )


def write_usd_broad_extra_trees_submission_artifacts(
    *,
    train_public_path: Path,
    holdout_features_path: Path,
    output_dir: Path,
    random_state: int = 37,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    model, metadata = train_usd_broad_extra_trees_model(
        train_public_path,
        random_state=random_state,
    )
    write_usd_broad_extra_trees_predictions(
        model,
        holdout_features_path=holdout_features_path,
        output_path=output_dir / "predictions.csv",
        threshold=float(metadata["selected_threshold"]),
    )
    return finalize_usd_broad_submission_artifacts(
        output_dir=output_dir,
        metadata=metadata,
        title="USD Broad Direction Extra Trees Baseline",
        body_lines=[
            "This baseline trains an extra-trees ensemble on the chronological train split only.",
            "It preserves the point-in-time information set while adding stronger tree randomization than the random forest baseline.",
            "The classification threshold is selected on the public validation split only.",
        ],
    )


def write_usd_broad_previous_day_direction_submission_artifacts(
    *,
    train_public_path: Path,
    holdout_features_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = train_usd_broad_previous_day_direction_baseline(train_public_path)
    write_usd_broad_previous_day_direction_predictions(
        holdout_features_path=holdout_features_path,
        output_path=output_dir / "predictions.csv",
        threshold=float(metadata["selected_threshold"]),
        probability_if_previous_day_up=float(metadata["probability_if_previous_day_up"]),
        probability_if_previous_day_nonpositive=float(
            metadata["probability_if_previous_day_nonpositive"]
        ),
    )
    return finalize_usd_broad_submission_artifacts(
        output_dir=output_dir,
        metadata=metadata,
        title="USD Broad Direction Previous-Day Rule Baseline",
        body_lines=[
            "This baseline maps the previous day's broad dollar return direction into a validation-calibrated probability.",
            "The conditional probabilities are estimated on the train split only.",
            "The classification threshold is selected on the public validation split only.",
        ],
    )
