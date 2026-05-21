"""
使用 akshare 拉取沪深 A 股日线 OHLCV，并标准化字段名。

日线接口使用 `stock_zh_a_daily`（新浪财经），相较东财 `stock_zh_a_hist` 通常更稳一些。
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

import pandas as pd

try:
    import akshare as ak
except ImportError as e:
    ak = None  # type: ignore
    _AK_IMPORT_ERROR = e
else:
    _AK_IMPORT_ERROR = None


# 兼容部分列名为中文或英文（版本差异）
_COL_MAP = {
    "日期": "date",
    "开盘": "open",
    "收盘": "close",
    "最高": "high",
    "最低": "low",
    "成交量": "volume",
    "成交额": "amount",
    "date": "date",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "volume": "volume",
    "amount": "amount",
}


def _to_sina_symbol(code: str) -> str:
    """
    将 6 位股票代码转为新浪格式：沪市 sh600519，深市 sz000858 / sz300750。

    说明：不含北交所（bjxxx）、沪市 5 开头的基金/ETF 等；若需可自行扩展映射。
    """
    s = str(code).strip()
    if not s.isdigit() or len(s) != 6:
        raise ValueError(f"股票代码应为 6 位数字，收到: {code!r}")
    if s.startswith("6"):
        return f"sh{s}"
    return f"sz{s}"


def load_daily_ohlcv(
    symbol: str,
    start_date: Optional[str] = None,
    adjust: str = "qfq",
) -> pd.DataFrame:
    """
    加载单只股票日线。
    symbol: 6 位代码，如 600519
    adjust: qfq 前复权 / hfq 后复权 / "" 不复权
    """
    if ak is None:
        raise ImportError(f"请先安装 akshare: pip install akshare. 原因: {_AK_IMPORT_ERROR}")

    sina_sym = _to_sina_symbol(symbol)
    start = start_date or "20180101"
    end = dt.date.today().strftime("%Y%m%d")

    raw = ak.stock_zh_a_daily(
        symbol=sina_sym,
        start_date=start,
        end_date=end,
        adjust=adjust,
    )
    if raw is None or raw.empty:
        return pd.DataFrame(
            columns=["date", "open", "high", "low", "close", "volume", "amount"]
        )

    df = raw.rename(columns=lambda c: _COL_MAP.get(str(c).strip(), str(c).strip().lower()))

    required = {"date", "open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        for old, new in _COL_MAP.items():
            if old in raw.columns and new not in df.columns:
                df[new] = raw[old]
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"数据列不完整 {symbol}: 缺少 {missing}")

    df["date"] = pd.to_datetime(df["date"])

    if "amount" not in df.columns:
        df["amount"] = pd.to_numeric(df["close"], errors="coerce") * pd.to_numeric(
            df["volume"], errors="coerce"
        )
    else:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df[["date", "open", "high", "low", "close", "volume", "amount"]].sort_values(
        "date"
    )
    df = df.dropna(subset=["close"]).reset_index(drop=True)
    return df
