"""
RSI 策略：超买超卖的拐点 + RSI14 强势区加减分。
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd

from strategies.base import BaseStrategy, bundle_scores


class RsiStrategy(BaseStrategy):
    strategy_key = "rsi"

    def analyze(self, tf: str, df: pd.DataFrame) -> Dict[str, Any]:
        name = "RSI 超买超卖"
        if df.shape[0] < 20:
            return bundle_scores(tf, 0.0, name, [])

        df = df.reset_index(drop=True)
        r6 = df["rsi6"].astype(float).values
        r14 = df["rsi14"].astype(float).values
        dt = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d").values

        if np.isnan(r6[-1]):
            return bundle_scores(tf, 0.0, name, [])

        signals: List[Dict[str, Any]] = []
        total = 0.0
        i = len(r6) - 1

        oversold_turn = float(r6[i - 1]) < 20 and float(r6[i]) > float(r6[i - 1])
        overbought_turn = float(r6[i - 1]) > 80 and float(r6[i]) < float(r6[i - 1])

        p_turn = 15.0
        signals.append({
            "rule": "RSI6<20 后拐头向上",
            "triggered": oversold_turn,
            "score": p_turn if oversold_turn else 0,
            "reason": "极度超卖后短线有修复动能",
            "date": dt[i] if oversold_turn else "",
        })
        if oversold_turn:
            total += p_turn

        n_turn = -15.0
        signals.append({
            "rule": "RSI6>80 后拐头向下",
            "triggered": overbought_turn,
            "score": n_turn if overbought_turn else 0,
            "reason": "超买区回落，短线回吐压力上升",
            "date": dt[i] if overbought_turn else "",
        })
        if overbought_turn:
            total += n_turn

        strong = float(r14[i]) > 50
        p_mid = 5.0
        signals.append({
            "rule": "RSI14>50（中短线偏强）",
            "triggered": strong,
            "score": p_mid if strong else 0,
            "reason": "相对强弱居中轴之上，偏多氛围",
            "date": dt[i] if strong else "",
        })
        if strong:
            total += p_mid

        return bundle_scores(tf, total, name, signals)
