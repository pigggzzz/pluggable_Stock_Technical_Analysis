"""均线：MA5/MA20/MA60/MA120（收盘价的简单移动平均）。"""

from __future__ import annotations

import pandas as pd


def add_ma_columns(df: pd.DataFrame, close_col: str = "close") -> pd.DataFrame:
    out = df.copy()
    c = out[close_col].astype(float)
    out["ma5"] = c.rolling(5).mean()
    out["ma20"] = c.rolling(20).mean()
    out["ma60"] = c.rolling(60).mean()
    out["ma120"] = c.rolling(120).mean()
    return out
