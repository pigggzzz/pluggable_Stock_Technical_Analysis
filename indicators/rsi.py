"""RSI（相对强弱指标）：Wilder 平滑近似，周期 6 / 14。"""

from __future__ import annotations

import numpy as np
import pandas as pd


def rsi(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100 - (100 / (1 + rs))
    return out.fillna(50.0)


def add_rsi_columns(df: pd.DataFrame, close_col: str = "close") -> pd.DataFrame:
    out = df.copy()
    c = out[close_col].astype(float)
    out["rsi6"] = rsi(c, 6)
    out["rsi14"] = rsi(c, 14)
    return out
