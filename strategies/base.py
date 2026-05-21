"""
策略抽象基类：子类对每个时间框架 dataframe 打分并输出统一结构。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

import pandas as pd

SignalDict = Dict[str, Any]


class BaseStrategy(ABC):
    strategy_key: str = "base"

    @abstractmethod
    def analyze(self, tf: str, df: pd.DataFrame) -> Dict[str, Any]:
        """
        tf: daily | weekly | monthly
        df: 已含指标列的 OHLCV+indicators

        每次只计算当前 tf 的贡献分；返回三个 score 字段，仅与 tf 对应的非零（其余为 0）。
        signals 为该时间框架规则触发列表。
        """

    def empty_result(self, tf: str, name: str) -> Dict[str, Any]:
        return bundle_scores(tf, 0.0, name, [])


def bundle_scores(tf: str, score: float, name: str, signals: List[SignalDict]) -> Dict[str, Any]:
    """把单次 timeframe 计算的 score 填入对应档位。"""
    d = {"daily": 0.0, "weekly": 0.0, "monthly": 0.0}
    if tf not in d:
        raise ValueError(tf)
    d[tf] = float(score)
    return {
        "name": name,
        "daily_score": d["daily"],
        "weekly_score": d["weekly"],
        "monthly_score": d["monthly"],
        "signals": signals,
        "tf_focus": tf,
    }
