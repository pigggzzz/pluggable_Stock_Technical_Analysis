"""
MACD 策略：金叉/死叉；红柱/绿柱连续扩大（简化：从柱体绝对值连续性判断）。
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd

from strategies.base import BaseStrategy, bundle_scores


class MacdStrategy(BaseStrategy):
    strategy_key = "macd"

    @staticmethod
    def _latest_date(df: pd.DataFrame) -> str:
        return pd.to_datetime(df.iloc[-1]["date"]).strftime("%Y-%m-%d")

    def analyze(self, tf: str, df: pd.DataFrame) -> Dict[str, Any]:
        name = "MACD 动能"
        if df.shape[0] < 30:
            return bundle_scores(tf, 0.0, name, [])

        signals: List[Dict[str, Any]] = []
        total = 0.0

        df = df.reset_index(drop=True)
        dif = df["dif"].astype(float).values
        dea = df["dea"].astype(float).values
        hist = df["macd_hist"].astype(float).values
        dates = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d").values

        if np.isnan(dif[-1]) or np.isnan(dea[-1]):
            return bundle_scores(tf, 0.0, name, [])

        i = len(dif) - 1
        golden_cross = dif[i - 1] <= dea[i - 1] and dif[i] > dea[i]
        dead_cross = dif[i - 1] >= dea[i - 1] and dif[i] < dea[i]

        dstr = dates[i]
        golden_pts = 20.0
        signals.append({
            "rule": "金叉 DIF 上穿 DEA",
            "triggered": golden_cross,
            "score": golden_pts if golden_cross else 0,
            "reason": "中期动能由弱转强的典型信号（需与其它指标共振）",
            "date": dstr if golden_cross else "",
        })
        if golden_cross:
            total += golden_pts

        dead_pts = -20.0
        signals.append({
            "rule": "死叉 DIF 下穿 DEA",
            "triggered": dead_cross,
            "score": dead_pts if dead_cross else 0,
            "reason": "中期动能拐头走弱",
            "date": dstr if dead_cross else "",
        })
        if dead_cross:
            total += dead_pts

        red_expand = False
        green_expand = False
        if len(hist) >= 4 and not np.isnan(hist[-4]):
            tail = hist[-4:]
            # 红柱扩大：柱状为正且最近 3 日严格递增（课程简化定义）
            if np.all(tail[1:] > 0):
                red_expand = bool(tail[1] > tail[0] and tail[2] > tail[1] and tail[3] > tail[2])
            # 绿柱扩大：柱状为负且绝对值递增
            if np.all(tail[1:] < 0):
                green_expand = bool(
                    tail[1] < tail[0] and tail[2] < tail[1] and tail[3] < tail[2]
                )

        rp = 10.0
        signals.append({
            "rule": "红柱连续三天扩大（多头动能增强）",
            "triggered": red_expand,
            "score": rp if red_expand else 0,
            "reason": "MACD 柱体红柱放大，趋势偏多一侧力量增强（课程简化）",
            "date": dstr if red_expand else "",
        })
        if red_expand:
            total += rp

        gp = -10.0
        signals.append({
            "rule": "绿柱连续三天扩大（空头动能增强）",
            "triggered": green_expand,
            "score": gp if green_expand else 0,
            "reason": "MACD 柱体绿柱放大，抛压加重（课程简化）",
            "date": dstr if green_expand else "",
        })
        if green_expand:
            total += gp

        return bundle_scores(tf, total, name, signals)
