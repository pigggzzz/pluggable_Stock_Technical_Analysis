"""
将标准化日线 OHLCV 聚合成周线、月线。
字段：date, open, high, low, close, volume, amount
"""

from __future__ import annotations

import pandas as pd


def _with_dt_index(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    col = pd.to_datetime(out["date"])
    out = out.assign(date=col).set_index("date").sort_index()
    return out


def to_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """周线（周五对齐）。"""
    o = _with_dt_index(df)
    agg = (
        o.resample("W-FRI")
        .agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
                "amount": "sum",
            }
        )
        .dropna(subset=["close"])
        .reset_index()
    )
    first_col = agg.columns[0]
    if first_col != "date":
        agg = agg.rename(columns={first_col: "date"})
    return agg


def to_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """月线（月末）。"""
    o = _with_dt_index(df)
    agg = (
        o.resample("ME")
        .agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
                "amount": "sum",
            }
        )
        .dropna(subset=["close"])
        .reset_index()
    )
    first_col = agg.columns[0]
    if first_col != "date":
        agg = agg.rename(columns={first_col: "date"})
    return agg


def ensure_amount(df: pd.DataFrame) -> pd.DataFrame:
    """若无有效成交额则用 close × volume 近似。"""
    out = df.copy()
    if "amount" not in out.columns or out["amount"].fillna(0).eq(0).all():
        out["amount"] = (
            out["close"].astype(float) * out["volume"].astype(float)
        ).fillna(0.0)
    else:
        out["amount"] = out["amount"].fillna(out["close"] * out["volume"])
    return out
