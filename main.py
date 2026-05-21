"""
课程作业入口：抓取数据 → 指标 → 多周期策略打分 → 报告与分布图。
运行方式（在项目根目录 stock_analysis/ 下）：
    pip install -r requirements.txt
    python main.py
"""
from __future__ import annotations
import datetime as dt
import traceback
import pandas as pd
from typing import Dict, List, Type
from config.settings import (
    DEFAULT_START_DATE,
    RANK_CSV,
    RANK_XLSX,
    REPORT_MD,
    SCORE_DIST_PNG,
)
from config.stock_pool import STOCK_POOL
from data.data_loader import load_daily_ohlcv
from data.timeframe import ensure_amount, to_monthly, to_weekly
from report.generator import dataframe_for_export, write_report
from scoring.scorer import attach_indicators, merge_strategy_tf_results, summarize_stock_scores
from strategies.base import BaseStrategy
from strategies.granville import GranvilleStrategy
from strategies.macd_strategy import MacdStrategy
from strategies.obv_strategy import ObvStrategy
from strategies.rsi_strategy import RsiStrategy
from visualization.plotter import plot_distribution
# 在此处手动勾选要纳入总分的策略（支持只开部分）。
SELECTED_STRATEGIES = ["granville", "macd", "rsi", "obv"]
STRATEGY_MAP: Dict[str, Type[BaseStrategy]] = {
    "granville": GranvilleStrategy,
    "macd": MacdStrategy,
    "rsi": RsiStrategy,
    "obv": ObvStrategy,
}
def _run_one(symbol: str, *, start_date: str) -> Dict[str, object]:
    """单只股票全流程；失败时抛出异常交由上层跳过。"""
    daily = ensure_amount(load_daily_ohlcv(symbol, start_date=start_date))
    if daily.empty:
        raise RuntimeError(f"{symbol}: 未取得日线数据")
    weekly = ensure_amount(to_weekly(daily))
    monthly = ensure_amount(to_monthly(daily))
    dd = attach_indicators(daily)
    ww = attach_indicators(weekly)
    mm = attach_indicators(monthly)
    frames = {
        "daily": dd,
        "weekly": ww,
        "monthly": mm,
    }
    merged_payloads = []
    for key in SELECTED_STRATEGIES:
        cls = STRATEGY_MAP.get(key)
        if cls is None:
            continue
        strat = cls()
        parts = [strat.analyze(tf, frames[tf]) for tf in ("daily", "weekly", "monthly")]
        merged_payloads.append(merge_strategy_tf_results(parts))
    summary = summarize_stock_scores(symbol, merged_payloads, tuple(SELECTED_STRATEGIES))
    return summary
def main() -> None:
    start_date = DEFAULT_START_DATE
    results: List[Dict[str, object]] = []
    for sym in STOCK_POOL:
        try:
            results.append(_run_one(sym, start_date=start_date))
            print(f"[OK] {sym}")
        except Exception as exc:  # noqa: BLE001（课程脚本：容错继续）
            print(f"[SKIP] {sym}: {exc}")
            traceback.print_exc()
    if not results:
        print("没有可用的股票结果，终止。")
        return
    # 分数最高 = 课堂意义上的「本期最推荐」，最低 = 「最不推荐」
    ranked = sorted(results, key=lambda r: float(r["composite_score"]), reverse=True)
    for idx, row in enumerate(ranked, start=1):
        row["rank"] = idx  # type: ignore[assignment]
    best = ranked[0]
    worst = ranked[-1]
    judgement = dt.date.today().strftime("%Y-%m-%d")
    df_export = dataframe_for_export(ranked)  # type: ignore[arg-type]
    df_export.to_csv(RANK_CSV, index=False, encoding="utf-8-sig")
    try:
        df_export.to_excel(RANK_XLSX, index=False)
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] Excel 写出失败（可忽略或检查 openpyxl）：{exc}")
    write_report(
        REPORT_MD,
        judgement_date=judgement,
        pool_desc="本表的代码列表来自项目的 `config/stock_pool.py`，属于课程自拟样本，并非全行业扫描。",
        pool_symbols=list(STOCK_POOL),
        rankings=df_export,
        best_detail=best,
        worst_detail=worst,
    )
    plot_distribution(
        [float(r["composite_score"]) for r in ranked],
        [str(r["symbol"]) for r in ranked],
        SCORE_DIST_PNG,
    )
    print(f"报告：{REPORT_MD}")
    print(f"排名表 CSV：{RANK_CSV}")
    print(f"排名表 XLSX：{RANK_XLSX}")
    print(f"分布图 PNG：{SCORE_DIST_PNG}")
    print(f"本期（样本内）最高分：{best['symbol']} {float(best['composite_score']):.2f}")
    print(f"本期（样本内）最低分：{worst['symbol']} {float(worst['composite_score']):.2f}")


if __name__ == "__main__":
    main()
