"""
葛兰碧简化版：四类典型规则 — BUY1/BUY2/SELL1/SELL2（基于收盘价与 MA20 关系）。
只观察最近几根 K 线与 MA20 形态，给出可解释的触发与分值。
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd

from strategies.base import BaseStrategy, bundle_scores


def _latest_date(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    return pd.to_datetime(df.iloc[-1]["date"]).strftime("%Y-%m-%d")


class GranvilleStrategy(BaseStrategy):
    strategy_key = "granville"

    def analyze(self, tf: str, df: pd.DataFrame) -> Dict[str, Any]:
        name = "葛兰碧（均线四类）"
        min_rows = {"daily": 125, "weekly": 70, "monthly": 60}.get(tf, 125)
        if df.shape[0] < min_rows:
            return bundle_scores(tf, 0.0, name, [
                self._sig(
                    f"样本不足(需要约{min_rows}根)，跳过葛兰碧",
                    False,
                    0,
                    "当前周期可用于均线结构判断的历史不足",
                    "",
                ),
            ])

        df = df.reset_index(drop=True)
        signals: List[Dict[str, Any]] = []
        total = 0.0

        # 索引 -1 为最新闭合 bar（假定数据已按交易日排序且含当日）
        i = len(df) - 1
        ma20_now = df["ma20"].iloc[i]
        ma20_prev = df["ma20"].iloc[i - 1]
        if np.isnan(ma20_now) or np.isnan(ma20_prev):
            return bundle_scores(tf, 0.0, name, signals)

        close = df["close"].astype(float)

        slope = ma20_now - ma20_prev
        ma_slope_up = slope > 1e-6 * abs(ma20_prev)
        ma_slope_dn = slope < -1e-6 * abs(ma20_prev)
        ma_flat = not ma_slope_up and not ma_slope_dn

        prev_close = close.iloc[i - 1]
        last_close = close.iloc[i]

        # BUY1: MA20 走平或上行；收盘从下向上突破 MA20
        crossed_up = prev_close <= ma20_prev and last_close > ma20_now
        buy1_cond = crossed_up and (ma_flat or ma_slope_up)
        s1_pts = 25.0
        signals.append(self._sig("BUY1 突破均线", buy1_cond, s1_pts if buy1_cond else 0,
            "收盘价自下而上穿越 MA20，且 MA20 未明显下移", _latest_date(df) if buy1_cond else ""))
        if buy1_cond:
            total += s1_pts

        # SELL1: MA20 走平转弱或下行；收盘向下跌破 MA20
        crossed_dn = prev_close >= ma20_prev and last_close < ma20_now
        sell1_cond = crossed_dn and (ma_slope_dn or ma_flat)
        ns1 = -25.0
        signals.append(self._sig("SELL1 跌破均线", sell1_cond, ns1 if sell1_cond else 0,
            "收盘价向下跌破 MA20，均线走平或下移", _latest_date(df) if sell1_cond else ""))
        if sell1_cond:
            total += ns1

        # BUY2：上升趋势回调未有效跌破 MA20 后再上行（回看窗口）
        buy2_pts = 22.0
        buy2, reason_b2 = self._detect_buy2(df, window=25)
        signals.append(self._sig("BUY2 回踩支撑再上行", buy2, buy2_pts if buy2 else 0, reason_b2,
            _latest_date(df) if buy2 else ""))
        if buy2:
            total += buy2_pts

        # SELL2：下降趋势反弹不过 MA20 再回落
        sell2_pts = -22.0
        sell2, reason_s2 = self._detect_sell2(df, window=25)
        signals.append(self._sig("SELL2 反弹受压再走弱", sell2, sell2_pts if sell2 else 0, reason_s2,
            _latest_date(df) if sell2 else ""))
        if sell2:
            total += sell2_pts

        return bundle_scores(tf, total, name, signals)

    @staticmethod
    def _sig(rule: str, triggered: bool, score: float, reason: str, date: str) -> Dict[str, Any]:
        return {
            "rule": rule,
            "triggered": triggered,
            "score": score,
            "reason": reason,
            "date": date if triggered else "",
        }

    def _detect_buy2(self, df: pd.DataFrame, window: int):
        """近 window 日内：先有 MA20 上方运行，回落至 MA20 附近仍收于 MA20 之上或略微刺破后立即收回再上。"""
        if len(df) < window + 2:
            return False, ""

        tail = df.iloc[-window:].copy()
        c = tail["close"].astype(float)
        ma = tail["ma20"].astype(float)
        if ma.isna().any():
            return False, ""

        above_ratio = float((c > ma * 0.995).mean())  # 略放宽“在均线上方偏多”
        if above_ratio < 0.45:
            return False, "近段未表现出持续在均线之上的上升结构"

        # 最近一次：低点接近 MA20 后收盘重新走高
        last = tail.iloc[-5:]
        lows_touch = float(last["low"].astype(float).min()) <= float(last["ma20"].astype(float).min()) * 1.02
        rec_up = c.iloc[-1] > ma.iloc[-1] and c.iloc[-1] > c.iloc[-3]

        touched = lows_touch or (c.iloc[-4:-1].min() < ma.iloc[-4:-1].max())
        ok = touched and rec_up and ma.iloc[-1] >= ma.iloc[-8] - 1e-6 * abs(ma.iloc[-8])

        msg = ok and "股价在均线上方区间震荡后回踩未有效破位，近两日再度走强" or "未观察到典型回踩支撑形态"
        return ok, msg

    def _detect_sell2(self, df: pd.DataFrame, window: int):
        """近窗口：偏弱运行为主，冲高接近/略过 MA20 后回落收于 MA20 下方。"""
        if len(df) < window + 2:
            return False, ""

        tail = df.iloc[-window:].copy()
        c = tail["close"].astype(float)
        ma = tail["ma20"].astype(float)
        below_ratio = float((c < ma * 1.005).mean())
        if below_ratio < 0.45:
            return False, "近段主要在均线上方运行，不似典型弱势反弹受压"

        # 最近有高不过 MA20
        hh = tail["high"].astype(float)
        recent_peak = hh.iloc[-6:].max()
        recent_ma_peak = ma.iloc[-6:].max()
        fail = recent_peak <= recent_ma_peak * 1.02 and c.iloc[-1] < ma.iloc[-1]

        ma_weak = ma.iloc[-1] <= ma.iloc[-8] + 1e-6 * abs(ma.iloc[-8])
        ok = fail and ma_weak
        msg = ok and "反弹高点接近均线但未能站稳，现价回落至 MA20 之下" or "未发现清晰反弹受压再走弱结构"
        return ok, msg
