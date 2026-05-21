"""
OBV：量能斜率确认 + 简单量价背离（价新高 OBV 未新高）。
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from strategies.base import BaseStrategy, bundle_scores


class ObvStrategy(BaseStrategy):
    strategy_key = "obv"

    def analyze(self, tf: str, df: pd.DataFrame) -> Dict[str, Any]:
        name = "OBV 量价"
        min_n = 35
        if df.shape[0] < min_n:
            return bundle_scores(tf, 0.0, name, [])

        df = df.reset_index(drop=True)
        close = df["close"].astype(float)
        ma20 = df["ma20"].astype(float)
        obv_vals = df["obv"].astype(float).values
        dt = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d").values

        if np.isnan(obv_vals[-1]) or np.isnan(ma20.iloc[-1]):
            return bundle_scores(tf, 0.0, name, [])

        signals: List[Dict[str, Any]] = []
        total = 0.0
        idx = np.arange(len(obv_vals[-10:]))

        # 线性斜率近似“10 个工作日能量潮走高”
        obv_seg = obv_vals[-10:]
        if np.any(np.isnan(obv_seg)):
            slope = 0.0
        else:
            slope = float(np.polyfit(idx, obv_seg, deg=1)[0])

        above_ma20 = close.iloc[-1] > ma20.iloc[-1]
        vol_ok = slope > 0 and above_ma20
        pts = 10.0

        signals.append({
            "rule": "OBV 近十日斜率为正且在 MA20 上方",
            "triggered": vol_ok,
            "score": pts if vol_ok else 0,
            "reason": "资金流入与价格也站在中期均线之上，量能与趋势略一致（课程语境）",
            "date": dt[-1] if vol_ok else "",
        })
        if vol_ok:
            total += pts

        div_pts = -10.0
        diverge, dv_date = self._price_obv_div(df, window=20)
        signals.append({
            "rule": "股价阶段新高但 OBV 未创出对应新高（量价背离）",
            "triggered": diverge,
            "score": div_pts if diverge else 0,
            "reason": "价涨量不配合，追高需谨慎",
            "date": dv_date if diverge else "",
        })
        if diverge:
            total += div_pts

        return bundle_scores(tf, total, name, signals)

    def _price_obv_div(self, df: pd.DataFrame, window: int) -> Tuple[bool, str]:
        """最近收盘创 window 最高价，OBV 非 window 内最高视为背离。"""
        tail = df.iloc[-window:].copy()
        c = tail["close"].astype(float).values
        o = tail["obv"].astype(float).values
        d = pd.to_datetime(tail["date"]).dt.strftime("%Y-%m-%d").values
        if len(c) < 5 or np.isnan(o[-1]):
            return False, ""

        price_new_high = c[-1] >= c.max() - 1e-8
        obv_not_high = o[-1] < o.max() - 1e-6
        ok = price_new_high and obv_not_high
        return ok, str(d[-1]) if ok else ""
