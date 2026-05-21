"""OBV（能量潮）：按涨跌累计成交量变化。"""

from __future__ import annotations

import numpy as np
import pandas as pd


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    c = close.astype(float)
    v = volume.astype(float)
    direction = np.sign(c.diff().fillna(0))
    return (direction * v).cumsum()


def add_obv(df: pd.DataFrame, close_col: str = "close", vol_col: str = "volume") -> pd.DataFrame:
    out = df.copy()
    out["obv"] = obv(out[close_col], out[vol_col])
    return out
