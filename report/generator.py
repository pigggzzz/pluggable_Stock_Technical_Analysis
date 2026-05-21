"""根据评分结果自动生成课程风格 Markdown 报告。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

_TF_CN = {"daily": "日线", "weekly": "周线", "monthly": "月线"}


def dataframe_to_md_table(df: pd.DataFrame) -> str:
    """不依赖第三方 tabulate：生成简易 Markdown 表。"""
    if df.empty:
        return "_（暂无数据）_"
    cols = list(df.columns)
    header = "| " + " | ".join(map(str, cols)) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    rows = []
    for _, r in df.iterrows():
        rows.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join([header, sep, *rows])


def write_report(
    out_path: Path,
    *,
    judgement_date: str,
    pool_desc: str,
    pool_symbols: List[str],
    rankings: pd.DataFrame,
    best_detail: Dict[str, Any],
    worst_detail: Dict[str, Any],
) -> None:
    """写入 report.md。"""
    lines: List[str] = []
    lines.append("# 沪深 A 股技术面研判报告（课程练习稿）")
    lines.append("")
    lines.append("## 1. 研判时间")
    lines.append(str(judgement_date))
    lines.append("")
    lines.append("## 2. 样本股票池说明")
    lines.append(pool_desc)
    symbols_line = ", ".join(pool_symbols)
    lines.append(f"本次维护代码：**{symbols_line}**。说明：筛选范围有限，只对样本负责，不构成投资建议。")
    lines.append("")
    lines.append("## 3. 综合评分最高（样本池内排名第一，视作相对更受关注标的）")
    lines.extend(_stock_detail_lines(best_detail))
    lines.append("")
    lines.append("## 4. 综合评分最低（样本池内排名垫底，视作相对更值得警惕标的）")
    lines.extend(_stock_detail_lines(worst_detail))
    lines.append("")
    lines.append("## 附：全部股票评分与排名表")
    table = dataframe_to_md_table(rankings.sort_values(["rank"]))
    lines.append(table)

    text = "\n".join(lines) + "\n"
    out_path.write_text(text, encoding="utf-8")


def _with_cn_tf(signal: Dict[str, Any]) -> Dict[str, Any]:
    tf = signal.get("timeframe", "") or ""
    s2 = dict(signal)
    s2["timeframe_cn"] = _TF_CN.get(tf, tf)
    return s2


def _gather_tf_sentence(strategies: List[Dict[str, Any]], tf_key: str) -> str:
    """把给定时间框架内的已触发要点串成一段话。"""
    pieces: List[str] = []
    for st in strategies or []:
        name = str(st.get("name", "") or "").strip()
        hits: List[str] = []
        for sraw in st.get("signals", []) or []:
            s = _with_cn_tf(sraw)
            if (sraw.get("timeframe") or "") != tf_key:
                continue
            if not s.get("triggered"):
                continue
            d = _fmt_dt(s.get("date"))
            hits.append(f"{s.get('rule')}（{_short_dt(d)}）：{s.get('reason','')}")
        if hits:
            pieces.append(name + "：" + "；".join(hits))
    if not pieces:
        return (
            "本周期所选规则多数是「旁观」状态——要么走势贴近均线窄幅震荡，要么动能指标未跨过阈值；课程上可解释为：暂无强信号。"
        )
    return " ".join(pieces)


def _rules_bullets(strategies: List[Dict[str, Any]], tf_key: str) -> List[str]:
    lines: List[str] = []
    for st in strategies or []:
        for sraw in st.get("signals", []) or []:
            if (sraw.get("timeframe") or "") != tf_key:
                continue
            s = _with_cn_tf(sraw)
            trig = bool(s.get("triggered"))
            tag = "已触发" if trig else "未触发"
            score = float(s.get("score") or 0)
            d = _fmt_dt(s.get("date")) if trig else ""
            suf = f"；触发日 {d}" if d else ""
            lines.append(f"- 【{st.get('name')}】{s.get('rule')}：**{tag}**，得分 **{score:+.2f}**{suf}。（{s.get('reason')}）")
    return lines


def _stock_detail_lines(payload: Dict[str, Any]) -> List[str]:
    sym = str(payload.get("symbol") or "").strip()
    cs = float(payload.get("composite_score") or 0)
    vd = str(payload.get("verdict") or "").strip()
    sts = payload.get("strategies") or []

    lines: List[str] = []
    lines.append(f"- **代码**：{sym}")
    lines.append(f"- **综合评分（归一化为 0~100）**：{cs:.2f}")
    lines.append(f"- **课程标签**：{vd}")
    lines.append("")
    lines.append(f"- **短期判断（日线）**：{_gather_tf_sentence(sts, 'daily')}")
    lines.append("")
    lines.append("- **触发规则列表（日线，含每条规则加减分解释）**：")
    for row in (_rules_bullets(sts, "daily") or ["- （无）"]):
        lines.append(f"  {row}")

    lines.append("")
    lines.append(f"- **中期判断（周线）**：{_gather_tf_sentence(sts, 'weekly')}")
    lines.append("")
    lines.append("- **触发规则列表（周线）：**")
    for row in (_rules_bullets(sts, "weekly") or ["- （无）"]):
        lines.append(f"  {row}")

    lines.append("")
    lines.append(f"- **长期判断（月线）**：{_gather_tf_sentence(sts, 'monthly')}")
    lines.append("")
    lines.append("- **触发规则列表（月线）：**")
    for row in (_rules_bullets(sts, "monthly") or ["- （无）"]):
        lines.append(f"  {row}")

    conclusion = payload.get("_conclusion")
    if not conclusion:
        if vd == "推荐":
            conclusion = (
                "从本次启用的几项经典规则综合来看，多空因素里「偏多一侧」更明显一些；日线图与更大周期方向上也没有明显打架。"
                "课程提醒：这是对样本的技术练习，不涉及业绩、政策或其他非技术因素。"
            )
        elif vd == "中性":
            conclusion = (
                "几项规则给出的信息偏「杂音」——有利好也有掣肘，合在一起就更像震荡市里的平常心状态；写法上可先描述观察点，再给谨慎结论。"
            )
        else:
            conclusion = (
                "规则层面偏空的触发项更多或在关键均线下方运行，因此被归到不推荐一侧；可作为课堂讨论「为何不重仓摸高」的案例素材。"
            )
    lines.append("")
    lines.append(f"- **结语（为何如此判定）**：{conclusion}")

    return lines


def _fmt_dt(x: Any) -> str:
    if not x:
        return ""
    return str(x)


def _short_dt(d: str) -> str:
    return d.strip()[:10]


def dataframe_for_export(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    """整理成适合保存 csv/xlsx 的排名表。"""
    out = pd.DataFrame(rows)
    cols = ["rank", "symbol", "composite_score", "verdict", "daily_raw", "weekly_raw", "monthly_raw", "weighted_raw"]
    cols = [c for c in cols if c in out.columns]
    return out[cols] if cols else out
