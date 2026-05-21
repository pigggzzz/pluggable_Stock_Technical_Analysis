"""MACD 指标：默认 (12, 26, 9)，快线、慢线为 EMA。"""

from __future__ import annotations

import pandas as pd


def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def add_macd(
    df: pd.DataFrame,
    close_col: str = "close",
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    out = df.copy()
    close = out[close_col].astype(float)
    ema_fast = _ema(close, fast)
    ema_slow = _ema(close, slow)
    dif = ema_fast - ema_slow
    dea = _ema(dif, signal)
    hist = dif - dea
    out["dif"] = dif
    out["dea"] = dea
    out["macd_hist"] = hist
    return out
