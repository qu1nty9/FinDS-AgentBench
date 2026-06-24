from __future__ import annotations

import numpy as np
import pandas as pd


def mock_treasury_source_frame() -> pd.DataFrame:
    dates = pd.bdate_range("2017-01-03", "2022-03-31")
    index = pd.Series(range(len(dates)), index=dates, dtype="float64")
    frame = pd.DataFrame(
        {
            "dgs10": 2.2 + 0.002 * index + 0.14 * (index / 9.0).map(np.sin),
            "dgs2": 1.9 + 0.0017 * index + 0.11 * (index / 11.0).map(np.sin),
            "dgs3mo": 1.4 + 0.0012 * index + 0.08 * (index / 13.0).map(np.cos),
            "dff": 1.3 + 0.0010 * index + 0.05 * (index / 15.0).map(np.sin),
        },
        index=dates,
    )
    frame.index.name = "date"
    return frame


def mock_usd_broad_source_frame() -> pd.DataFrame:
    dates = pd.bdate_range("2017-01-03", "2022-03-31")
    index = pd.Series(range(len(dates)), index=dates, dtype="float64")
    frame = pd.DataFrame(
        {
            "usd_broad": 100.0 + 0.018 * index + 1.10 * (index / 10.0).map(np.sin),
            "usd_afe": 98.0 + 0.015 * index + 0.95 * (index / 11.0).map(np.cos),
            "usd_eme": 96.0 + 0.012 * index + 0.90 * (index / 13.0).map(np.sin),
            "dgs2": 1.9 + 0.0017 * index + 0.11 * (index / 11.0).map(np.sin),
            "dgs10": 2.2 + 0.0020 * index + 0.14 * (index / 9.0).map(np.sin),
            "dff": 1.3 + 0.0010 * index + 0.05 * (index / 15.0).map(np.sin),
        },
        index=dates,
    )
    frame.index.name = "date"
    return frame
