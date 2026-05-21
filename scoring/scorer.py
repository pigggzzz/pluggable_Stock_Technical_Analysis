"""将各策略按时间框架汇总并归一成 0~100 综合评分。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import numpy as np
import pandas as pd

from config.settings import NEUTRAL_MIN, RECOMMENDED_MIN, TF_WEIGHTS
from indicators.ma import add_ma_columns
from indicators.macd import add_macd
from indicators.obv import add_obv
from indicators.rsi import add_rsi_columns


@dataclass
class StrategyScoreBounds:
    """单策略在某一时间维度上的理论上下界（与课程打分表一致）。"""

    high: float
    low: float


BOUNDS_REGISTRY: Dict[str, StrategyScoreBounds] = {
    "granville": StrategyScoreBounds(47.0, -47.0),
    "macd": StrategyScoreBounds(30.0, -30.0),
    "rsi": StrategyScoreBounds(20.0, -15.0),
    "obv": StrategyScoreBounds(10.0, -10.0),
}


def attach_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """在 OHLCV 上挂载 MA / MACD / RSI / OBV。"""
    out = df.copy()
    out = add_ma_columns(out)
    out = add_macd(out)
    out = add_rsi_columns(out)
    out = add_obv(out)
    return out


def merge_strategy_tf_results(parts: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """
    parts: 同一策略在 daily / weekly / monthly 分别调用 analyze 的返回，
    合并为单一的 daily_score / weekly_score / monthly_score 与扁平 signals。
    """
    plist = list(parts)
    if not plist:
        return {}
    merged: Dict[str, Any] = {
        "name": plist[0].get("name", ""),
        "daily_score": 0.0,
        "weekly_score": 0.0,
        "monthly_score": 0.0,
        "signals": [],
    }
    for r in plist:
        merged["daily_score"] += float(r.get("daily_score", 0) or 0)
        merged["weekly_score"] += float(r.get("weekly_score", 0) or 0)
        merged["monthly_score"] += float(r.get("monthly_score", 0) or 0)
        tf = str(r.get("tf_focus", "")).strip().lower()
        for s in r.get("signals", []) or []:
            s2 = dict(s)
            if tf:
                s2["timeframe"] = tf
            merged["signals"].append(s2)
    return merged


def compute_bounds(selected_keys: Sequence[str]) -> Tuple[float, float]:
    """加权后的理论最大值与最小值（每个时间框架可加总到同一上下界后再乘权重相加）。"""
    hi_tf = sum(BOUNDS_REGISTRY[k].high for k in selected_keys if k in BOUNDS_REGISTRY)
    lo_tf = sum(BOUNDS_REGISTRY[k].low for k in selected_keys if k in BOUNDS_REGISTRY)
    wsum = TF_WEIGHTS["daily"] + TF_WEIGHTS["weekly"] + TF_WEIGHTS["monthly"]
    hi = hi_tf * wsum
    lo = lo_tf * wsum
    return hi, lo


def weighted_raw(daily_raw: float, weekly_raw: float, monthly_raw: float) -> float:
    """未归一加权总分。"""
    return (
        TF_WEIGHTS["daily"] * daily_raw
        + TF_WEIGHTS["weekly"] * weekly_raw
        + TF_WEIGHTS["monthly"] * monthly_raw
    )


def normalize_score(raw_weighted: float, hi: float, lo: float) -> float:
    """映射到 [0, 100]，并截断边界。"""
    if hi <= lo:
        return 50.0
    pct = (raw_weighted - lo) / (hi - lo) * 100.0
    return float(np.clip(pct, 0.0, 100.0))


def summarize_stock_scores(
    symbol: str,
    strategy_payloads: List[Dict[str, Any]],
    selected_keys: Sequence[str],
) -> Dict[str, Any]:
    """
    strategy_payloads: 每个元素已是 merge_strategy_tf_results 后的单策略总分结构。
    返回一只股票的综合分、分项 raw、是否推荐标签等。
    """
    daily_raw = sum(float(p.get("daily_score") or 0) for p in strategy_payloads)
    weekly_raw = sum(float(p.get("weekly_score") or 0) for p in strategy_payloads)
    monthly_raw = sum(float(p.get("monthly_score") or 0) for p in strategy_payloads)
    raw_weighted = weighted_raw(daily_raw, weekly_raw, monthly_raw)
    hi, lo = compute_bounds(selected_keys)

    composite = normalize_score(raw_weighted, hi, lo)
    verdict = classify_verdict(composite)

    return {
        "symbol": symbol,
        "daily_raw": daily_raw,
        "weekly_raw": weekly_raw,
        "monthly_raw": monthly_raw,
        "weighted_raw": raw_weighted,
        "composite_score": composite,
        "verdict": verdict,
        "strategies": strategy_payloads,
        "bounds": {"high": hi, "low": lo},
    }


def classify_verdict(score_100: float) -> str:
    """≥75 推荐；50–75 中性；<50 不推荐。"""
    if score_100 >= RECOMMENDED_MIN:
        return "推荐"
    if score_100 >= NEUTRAL_MIN:
        return "中性"
    return "不推荐"
