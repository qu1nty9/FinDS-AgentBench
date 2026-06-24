from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

import nbformat
import pandas as pd

from finds_agentbench.scoring import balanced_accuracy


TASK_ID = "yield_direction_treasury10y_v0"
ASSET_ID = "us_treasury_10y"
DEFAULT_OBSERVATION_START = "2003-01-02"
DEFAULT_OBSERVATION_END = "2026-01-02"
DEFAULT_REALTIME_SNAPSHOT_DATE = "2026-06-21"
SERIES_IDS = {
    "dgs10": "DGS10",
    "dgs2": "DGS2",
    "dgs3mo": "DGS3MO",
    "dff": "DFF",
}
FEATURE_COLUMNS = [
    "dgs10_level",
    "dgs2_level",
    "dgs3mo_level",
    "dff_level",
    "curve_10y_2y",
    "curve_10y_3mo",
    "front_end_spread",
    "dgs10_change_1d",
    "dgs10_change_5d",
    "curve_10y_2y_change_5d",
    "dgs10_vol_5d",
    "dgs10_vol_20d",
    "dgs10_minus_20d_mean",
]
TRAIN_END = date(2018, 12, 31)
PUBLIC_VALIDATION_END = date(2021, 12, 31)
PRIVATE_HOLDOUT_END = date(2025, 12, 31)


@dataclass(frozen=True)
class TreasuryTaskPaths:
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


def _fred_api_frame(
    series_id: str,
    *,
    api_key: str,
    observation_start: str,
    observation_end: str,
    realtime_start: str | None = None,
    realtime_end: str | None = None,
) -> pd.DataFrame:
    query_params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": observation_start,
        "observation_end": observation_end,
    }
    if realtime_start is not None:
        query_params["realtime_start"] = realtime_start
    if realtime_end is not None:
        query_params["realtime_end"] = realtime_end
    query = urlencode(query_params)
    url = f"https://api.stlouisfed.org/fred/series/observations?{query}"
    with urlopen(url, timeout=30) as response:
        payload = json.load(response)
    observations = payload.get("observations", [])
    frame = pd.DataFrame(observations)
    if frame.empty:
        raise ValueError(f"No observations returned for {series_id}.")
    frame = frame.loc[:, ["date", "value"]].copy()
    frame["date"] = pd.to_datetime(frame["date"], format="%Y-%m-%d")
    frame["value"] = pd.to_numeric(frame["value"].replace(".", pd.NA), errors="coerce")
    return frame


def _fred_graph_frame(
    series_id: str,
    *,
    observation_start: str,
    observation_end: str,
    graph_host: str = "fred.stlouisfed.org",
    vintage_date: str | None = None,
) -> pd.DataFrame:
    query_params = {
        "id": series_id,
        "cosd": observation_start,
        "coed": observation_end,
    }
    if vintage_date is not None:
        query_params["vintage_date"] = vintage_date
    query = urlencode(query_params)
    graph_file = "alfredgraph.csv" if vintage_date is not None and graph_host.startswith("alfred") else "fredgraph.csv"
    url = f"https://{graph_host}/graph/{graph_file}?{query}"
    frame = pd.read_csv(url)
    if frame.empty:
        raise ValueError(f"No observations returned for {series_id}.")
    columns = list(frame.columns)
    if len(columns) != 2:
        raise ValueError(f"Unexpected fredgraph payload for {series_id}: {frame.columns.tolist()}")
    date_column, value_column = columns
    frame = frame.rename(columns={date_column: "date", value_column: "value"})
    frame["date"] = pd.to_datetime(frame["date"], format="%Y-%m-%d")
    frame["value"] = pd.to_numeric(frame["value"].replace(".", pd.NA), errors="coerce")
    return frame


def fetch_fred_series(
    series_id: str,
    *,
    api_key: str | None = None,
    observation_start: str = DEFAULT_OBSERVATION_START,
    observation_end: str = DEFAULT_OBSERVATION_END,
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
) -> pd.Series:
    resolved_api_key = api_key or os.environ.get("FRED_API_KEY")
    if resolved_api_key and snapshot_date is not None:
        frame = _fred_api_frame(
            series_id,
            api_key=resolved_api_key,
            observation_start=observation_start,
            observation_end=observation_end,
            realtime_start=snapshot_date,
            realtime_end=snapshot_date,
        )
    elif resolved_api_key:
        frame = _fred_api_frame(
            series_id,
            api_key=resolved_api_key,
            observation_start=observation_start,
            observation_end=observation_end,
        )
    elif snapshot_date is not None:
        frame = _fred_graph_frame(
            series_id,
            observation_start=observation_start,
            observation_end=observation_end,
            graph_host="alfred.stlouisfed.org",
            vintage_date=snapshot_date,
        )
    else:
        frame = _fred_graph_frame(
            series_id,
            observation_start=observation_start,
            observation_end=observation_end,
        )

    series = frame.set_index("date")["value"].sort_index()
    series.name = series_id
    return series


def fetch_treasury_source_frame(
    *,
    api_key: str | None = None,
    observation_start: str = DEFAULT_OBSERVATION_START,
    observation_end: str = DEFAULT_OBSERVATION_END,
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
) -> pd.DataFrame:
    dgs10 = fetch_fred_series(
        SERIES_IDS["dgs10"],
        api_key=api_key,
        observation_start=observation_start,
        observation_end=observation_end,
        snapshot_date=snapshot_date,
    ).rename("dgs10")
    frame = dgs10.to_frame()

    for column_name, series_id in SERIES_IDS.items():
        if column_name == "dgs10":
            continue
        series = fetch_fred_series(
            series_id,
            api_key=api_key,
            observation_start=observation_start,
            observation_end=observation_end,
            snapshot_date=snapshot_date,
        ).rename(column_name)
        frame = frame.join(series, how="left")

    frame[["dgs2", "dgs3mo", "dff"]] = frame[["dgs2", "dgs3mo", "dff"]].ffill(limit=5)
    frame = frame.dropna().sort_index()
    frame.index.name = "date"
    return frame


def build_treasury_direction_frame(source_frame: pd.DataFrame) -> pd.DataFrame:
    if source_frame.empty:
        raise ValueError("source_frame must contain observations.")

    frame = source_frame.copy().sort_index()
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise TypeError("source_frame index must be a pandas DatetimeIndex.")

    required_columns = set(SERIES_IDS)
    missing_columns = required_columns - set(frame.columns)
    if missing_columns:
        raise ValueError(f"source_frame is missing required columns: {sorted(missing_columns)}")

    frame["curve_10y_2y"] = frame["dgs10"] - frame["dgs2"]
    frame["curve_10y_3mo"] = frame["dgs10"] - frame["dgs3mo"]
    frame["front_end_spread"] = frame["dgs2"] - frame["dff"]
    frame["dgs10_change_1d"] = frame["dgs10"].diff(1)
    frame["dgs10_change_5d"] = frame["dgs10"].diff(5)
    frame["curve_10y_2y_change_5d"] = frame["curve_10y_2y"].diff(5)
    daily_change = frame["dgs10"].diff(1)
    frame["dgs10_vol_5d"] = daily_change.rolling(5).std()
    frame["dgs10_vol_20d"] = daily_change.rolling(20).std()
    frame["dgs10_minus_20d_mean"] = frame["dgs10"] - frame["dgs10"].rolling(20).mean()
    frame["next_day_change_bp"] = (frame["dgs10"].shift(-1) - frame["dgs10"]) * 100.0
    frame["next_day_directional_return"] = frame["next_day_change_bp"] / 10000.0
    frame["next_day_yield_up"] = (frame["next_day_change_bp"] > 0.0).astype(int)
    frame["split"] = [split_for_date(timestamp.date()) for timestamp in frame.index]
    frame = frame.rename(
        columns={
            "dgs10": "dgs10_level",
            "dgs2": "dgs2_level",
            "dgs3mo": "dgs3mo_level",
            "dff": "dff_level",
        }
    )

    frame = frame.dropna(
        subset=FEATURE_COLUMNS + ["next_day_change_bp", "next_day_directional_return"]
    )
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
        "dgs10_level",
        "dgs2_level",
        "dgs3mo_level",
        "dff_level",
        "curve_10y_2y",
        "curve_10y_3mo",
        "front_end_spread",
        "dgs10_change_1d",
        "dgs10_change_5d",
        "curve_10y_2y_change_5d",
        "dgs10_vol_5d",
        "dgs10_vol_20d",
        "dgs10_minus_20d_mean",
        "next_day_yield_up",
        "next_day_change_bp",
        "next_day_directional_return",
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


def _resolve_existing_task_paths(
    output_path: Path,
    private_path: Path,
) -> TreasuryTaskPaths | None:
    candidate = TreasuryTaskPaths(
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


def write_yield_direction_task(
    *,
    output_dir: str | Path = "data/raw/yield_direction_treasury10y_v0",
    private_dir: str | Path = "data/private/yield_direction_treasury10y_v0",
    api_key: str | None = None,
    observation_start: str = DEFAULT_OBSERVATION_START,
    observation_end: str = DEFAULT_OBSERVATION_END,
    snapshot_date: str | None = DEFAULT_REALTIME_SNAPSHOT_DATE,
    source_frame: pd.DataFrame | None = None,
) -> TreasuryTaskPaths:
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

    source = source_frame if source_frame is not None else fetch_treasury_source_frame(
        api_key=api_key,
        observation_start=observation_start,
        observation_end=observation_end,
        snapshot_date=snapshot_date,
    )
    task_frame = build_treasury_direction_frame(source)
    formatted = _format_numeric_frame(task_frame)

    feature_columns = [
        "row_id",
        "date",
        "asset_id",
        "split",
        *FEATURE_COLUMNS,
    ]
    public_columns = feature_columns + [
        "next_day_yield_up",
        "next_day_change_bp",
        "next_day_directional_return",
    ]
    answer_columns = [
        "row_id",
        "date",
        "asset_id",
        "next_day_yield_up",
        "next_day_change_bp",
        "next_day_directional_return",
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
        "source_mode": (
            "provided_source_frame"
            if source_frame is not None
            else (
                "fred_api_realtime_snapshot"
                if (api_key or os.environ.get("FRED_API_KEY")) and snapshot_date is not None
                else (
                    "alfred_graph_vintage_snapshot"
                    if snapshot_date is not None
                    else "fred_graph_current"
                )
            )
        ),
        "splits": {
            "train": {"start": str(task_frame.loc[task_frame["split"] == "train", "date"].min()), "end": str(task_frame.loc[task_frame["split"] == "train", "date"].max())},
            "public_validation": {
                "start": str(task_frame.loc[task_frame["split"] == "public_validation", "date"].min()),
                "end": str(task_frame.loc[task_frame["split"] == "public_validation", "date"].max()),
            },
            "private_temporal_holdout": {
                "start": str(task_frame.loc[task_frame["split"] == "private_temporal_holdout", "date"].min()),
                "end": str(task_frame.loc[task_frame["split"] == "private_temporal_holdout", "date"].max()),
            },
        },
        "feature_columns": FEATURE_COLUMNS,
        "target": "next_day_yield_up",
        "return_column": "next_day_directional_return",
        "forbidden_private_columns": [
            "next_day_yield_up",
            "next_day_change_bp",
            "next_day_directional_return",
        ],
        "row_count": int(len(task_frame)),
        "private_holdout_row_count": int((task_frame["split"] == "private_temporal_holdout").sum()),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return TreasuryTaskPaths(
        train_public=train_public_path,
        private_holdout_features=holdout_features_path,
        sample_submission=sample_submission_path,
        metadata=metadata_path,
        answer_key=answer_key_path,
    )


def choose_threshold(y_true: pd.Series, probabilities: pd.Series) -> tuple[float, float]:
    candidates = sorted({round(float(value), 6) for value in probabilities.to_list()} | {0.5})
    best_threshold = 0.5
    best_score = -1.0
    for threshold in candidates:
        predictions = [1 if probability >= threshold else 0 for probability in probabilities]
        score = balanced_accuracy(y_true.astype(int).tolist(), predictions)
        if score > best_score:
            best_threshold = threshold
            best_score = score
    return best_threshold, best_score


def clip_probability(value: float) -> float:
    return min(max(float(value), 0.03), 0.97)


def load_yield_train_validation_rows(train_public_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = pd.read_csv(train_public_path)
    train_rows = frame.loc[frame["split"] == "train"].copy()
    validation_rows = frame.loc[frame["split"] == "public_validation"].copy()
    if train_rows.empty:
        raise ValueError("No train rows found in train_public data.")
    if validation_rows.empty:
        raise ValueError("No public_validation rows found in train_public data.")
    return train_rows, validation_rows


def train_yield_sklearn_probability_model(
    train_public_path: Path,
    *,
    estimator,
    model_name: str,
    random_state: int,
) -> tuple[Any, dict[str, Any]]:
    train_rows, validation_rows = load_yield_train_validation_rows(train_public_path)
    estimator.fit(train_rows[FEATURE_COLUMNS], train_rows["next_day_yield_up"].astype(int))
    validation_probabilities = pd.Series(
        estimator.predict_proba(validation_rows[FEATURE_COLUMNS])[:, 1],
        index=validation_rows.index,
    )
    threshold, validation_balanced_accuracy = choose_threshold(
        validation_rows["next_day_yield_up"],
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


def write_probability_predictions(
    *,
    row_ids: pd.Series,
    probabilities: pd.Series,
    output_path: Path,
    threshold: float,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "row_id": row_ids,
            "prediction": ["1" if value >= threshold else "0" for value in probabilities],
            "probability": [f"{float(value):.8f}" for value in probabilities],
        }
    ).to_csv(output_path, index=False)


def write_treasury_baseline_writeup(
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
            "The baseline does not read private labels, answer keys, or future yield changes during prediction generation.",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_treasury_baseline_notebook(output_path: Path) -> None:
    notebook = nbformat.v4.new_notebook()
    notebook.cells = [
        nbformat.v4.new_markdown_cell("# Treasury Yield Direction Baseline Submission Check"),
        nbformat.v4.new_code_cell(
            "\n".join(
                [
                    "from pathlib import Path",
                    "for path in ['predictions.csv', 'writeup.md', 'baseline_metadata.json']:",
                    "    assert Path(path).exists(), f'missing {path}'",
                    "print('Treasury yield direction baseline artifacts are present.')",
                ]
            )
        ),
    ]
    nbformat.write(notebook, output_path)


def finalize_treasury_submission_artifacts(
    *,
    output_dir: Path,
    metadata: dict[str, Any],
    title: str,
    body_lines: list[str],
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_treasury_baseline_writeup(
        output_dir / "writeup.md",
        title=title,
        body_lines=body_lines,
        metadata=metadata,
    )
    write_treasury_baseline_notebook(output_dir / "notebook.ipynb")
    (output_dir / "baseline_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metadata


def train_yield_logistic_model(train_public_path: Path, *, random_state: int = 29):
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "The Treasury yield logistic baseline requires scikit-learn."
        ) from exc

    estimator = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=1000, random_state=random_state),
    )
    return train_yield_sklearn_probability_model(
        train_public_path,
        estimator=estimator,
        model_name="logistic_regression",
        random_state=random_state,
    )


def train_yield_random_forest_model(train_public_path: Path, *, random_state: int = 29):
    try:
        from sklearn.ensemble import RandomForestClassifier
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "The Treasury yield random forest baseline requires scikit-learn."
        ) from exc

    estimator = RandomForestClassifier(
        n_estimators=400,
        min_samples_leaf=5,
        random_state=random_state,
        n_jobs=1,
    )
    return train_yield_sklearn_probability_model(
        train_public_path,
        estimator=estimator,
        model_name="random_forest",
        random_state=random_state,
    )


def train_yield_extra_trees_model(train_public_path: Path, *, random_state: int = 29):
    try:
        from sklearn.ensemble import ExtraTreesClassifier
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "The Treasury yield extra trees baseline requires scikit-learn."
        ) from exc

    estimator = ExtraTreesClassifier(
        n_estimators=400,
        min_samples_leaf=5,
        random_state=random_state,
        n_jobs=1,
    )
    return train_yield_sklearn_probability_model(
        train_public_path,
        estimator=estimator,
        model_name="extra_trees",
        random_state=random_state,
    )


def train_yield_previous_day_direction_baseline(
    train_public_path: Path,
) -> dict[str, Any]:
    train_rows, validation_rows = load_yield_train_validation_rows(train_public_path)
    train_indicator = train_rows["dgs10_change_1d"] > 0
    train_rate = float(train_rows["next_day_yield_up"].astype(int).mean())
    up_rate = clip_probability(
        float(train_rows.loc[train_indicator, "next_day_yield_up"].astype(int).mean())
        if train_indicator.any()
        else train_rate
    )
    down_rate = clip_probability(
        float(train_rows.loc[~train_indicator, "next_day_yield_up"].astype(int).mean())
        if (~train_indicator).any()
        else train_rate
    )
    validation_probabilities = pd.Series(
        [
            up_rate if indicator else down_rate
            for indicator in (validation_rows["dgs10_change_1d"] > 0).tolist()
        ],
        index=validation_rows.index,
    )
    threshold, validation_balanced_accuracy = choose_threshold(
        validation_rows["next_day_yield_up"],
        validation_probabilities,
    )
    return {
        "baseline_family": "previous_day_direction_rule",
        "feature_columns": ["dgs10_change_1d"],
        "train_rows": int(len(train_rows)),
        "public_validation_rows": int(len(validation_rows)),
        "probability_if_previous_day_up": up_rate,
        "probability_if_previous_day_nonpositive": down_rate,
        "selected_threshold": threshold,
        "public_validation_balanced_accuracy": validation_balanced_accuracy,
    }


def write_yield_logistic_predictions(
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


def write_yield_random_forest_predictions(
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


def write_yield_extra_trees_predictions(
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


def write_yield_previous_day_direction_predictions(
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
            for value in frame["dgs10_change_1d"]
        ],
        index=frame.index,
    )
    write_probability_predictions(
        row_ids=frame["row_id"],
        probabilities=probabilities,
        output_path=output_path,
        threshold=threshold,
    )


def write_yield_logistic_submission_artifacts(
    *,
    train_public_path: Path,
    holdout_features_path: Path,
    output_dir: Path,
    random_state: int = 29,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    model, metadata = train_yield_logistic_model(train_public_path, random_state=random_state)
    write_yield_logistic_predictions(
        model,
        holdout_features_path=holdout_features_path,
        output_path=output_dir / "predictions.csv",
        threshold=float(metadata["selected_threshold"]),
    )
    return finalize_treasury_submission_artifacts(
        output_dir=output_dir,
        metadata=metadata,
        title="Treasury Yield Direction Logistic Regression Baseline",
        body_lines=[
            "This baseline trains a logistic regression model on the chronological train split only.",
            "Feature scaling is fit on the train split and reused on public validation and private holdout rows.",
            "The classification threshold is selected on the public validation split only.",
        ],
    )


def write_yield_random_forest_submission_artifacts(
    *,
    train_public_path: Path,
    holdout_features_path: Path,
    output_dir: Path,
    random_state: int = 29,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    model, metadata = train_yield_random_forest_model(train_public_path, random_state=random_state)
    write_yield_random_forest_predictions(
        model,
        holdout_features_path=holdout_features_path,
        output_path=output_dir / "predictions.csv",
        threshold=float(metadata["selected_threshold"]),
    )
    return finalize_treasury_submission_artifacts(
        output_dir=output_dir,
        metadata=metadata,
        title="Treasury Yield Direction Random Forest Baseline",
        body_lines=[
            "This baseline trains a random forest classifier on the chronological train split only.",
            "It captures nonlinear interactions among curve shape, rate levels, and recent yield dynamics.",
            "The classification threshold is selected on the public validation split only.",
        ],
    )


def write_yield_extra_trees_submission_artifacts(
    *,
    train_public_path: Path,
    holdout_features_path: Path,
    output_dir: Path,
    random_state: int = 29,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    model, metadata = train_yield_extra_trees_model(train_public_path, random_state=random_state)
    write_yield_extra_trees_predictions(
        model,
        holdout_features_path=holdout_features_path,
        output_path=output_dir / "predictions.csv",
        threshold=float(metadata["selected_threshold"]),
    )
    return finalize_treasury_submission_artifacts(
        output_dir=output_dir,
        metadata=metadata,
        title="Treasury Yield Direction Extra Trees Baseline",
        body_lines=[
            "This baseline trains an extra-trees ensemble on the chronological train split only.",
            "It injects stronger randomization than the random forest baseline while preserving point-in-time features.",
            "The classification threshold is selected on the public validation split only.",
        ],
    )


def write_yield_previous_day_direction_submission_artifacts(
    *,
    train_public_path: Path,
    holdout_features_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = train_yield_previous_day_direction_baseline(train_public_path)
    write_yield_previous_day_direction_predictions(
        holdout_features_path=holdout_features_path,
        output_path=output_dir / "predictions.csv",
        threshold=float(metadata["selected_threshold"]),
        probability_if_previous_day_up=float(metadata["probability_if_previous_day_up"]),
        probability_if_previous_day_nonpositive=float(
            metadata["probability_if_previous_day_nonpositive"]
        ),
    )
    return finalize_treasury_submission_artifacts(
        output_dir=output_dir,
        metadata=metadata,
        title="Treasury Yield Direction Previous-Day Rule Baseline",
        body_lines=[
            "This baseline maps the previous day's 10-year yield direction into a validation-calibrated probability.",
            "The conditional probabilities are estimated on the train split only.",
            "The classification threshold is selected on the public validation split only.",
        ],
    )
