"""
使用 akshare 拉取沪深 A 股日线 OHLCV，并标准化字段名。
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

try:
    import akshare as ak
except ImportError as e:
    ak = None  # type: ignore
    _AK_IMPORT_ERROR = e
else:
    _AK_IMPORT_ERROR = None


# akshare stock_zh_a_hist 常见中文列 → 英文字段
_COL_MAP = {
    "日期": "date",
    "开盘": "open",
    "收盘": "close",
    "最高": "high",
    "最低": "low",
    "成交量": "volume",
    "成交额": "amount",
    # 备用英文名
    "date": "date",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "volume": "volume",
    "amount": "amount",
}


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

    raw = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=start_date or "20180101",
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
        # 兼容部分版本列名为英文大小写混合
        for old, new in _COL_MAP.items():
            if old in raw.columns and new not in df.columns:
                df[new] = raw[old]
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"数据列不完整 {symbol}: 缺少 {missing}")

    df["date"] = pd.to_datetime(df["date"])

    # 成交额可能缺失或为 0
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
