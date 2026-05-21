"""综合评分分布直方图（静态 matplotlib）。"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from config.settings import NEUTRAL_MIN, RECOMMENDED_MIN

# Windows 环境下尽量用系统中文字体，避免中文标注变方块。
plt.rcParams.setdefault("axes.unicode_minus", False)
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]


def _color_for_bin(mid: float) -> str:
    if mid >= RECOMMENDED_MIN:
        return "#2ca02c"  # green
    if mid >= NEUTRAL_MIN:
        return "#ffbf00"  # amber
    return "#d62728"  # red


def plot_distribution(
    scores: Sequence[float],
    symbols: Sequence[str],
    out_path: Path,
    *,
    bins: int = 20,
) -> None:
    """
    绘制 0–100 维度的分数直方图，并标注最高分/最低分/平均分。
    每个柱按所在区间底色区分推荐区、中性区、不推荐区。
    """
    vals = np.array(scores, dtype=float)
    if vals.size == 0:
        return

    bins_edges = np.linspace(0.0, 100.0, bins + 1)
    heights, edges = np.histogram(vals, bins=bins_edges)
    centers = (edges[:-1] + edges[1:]) / 2.0
    widths = np.diff(edges)
    colors = [_color_for_bin(float(c)) for c in centers]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(centers, heights, width=widths * 0.92, color=colors, edgecolor="#333333", linewidth=0.25, align="center")

    mean_v = float(np.mean(vals))
    ax.axvline(mean_v, color="#1f77b4", linestyle="--", linewidth=1.4)

    best_i = int(np.argmax(vals))
    worst_i = int(np.argmin(vals))
    best_sym, best_s = symbols[best_i], float(vals[best_i])
    worst_sym, worst_s = symbols[worst_i], float(vals[worst_i])

    ax.annotate(
        f"最高：{best_sym} {best_s:.2f}",
        xy=(best_s, heights.max() * 0.05 if heights.max() > 0 else 0.2),
        xytext=(best_s, (heights.max() or 1) * 0.35),
        arrowprops=dict(arrowstyle="->", color="black"),
        fontsize=9,
    )
    ax.annotate(
        f"最低：{worst_sym} {worst_s:.2f}",
        xy=(worst_s, heights.max() * 0.05 if heights.max() > 0 else 0.2),
        xytext=(worst_s, (heights.max() or 1) * 0.25),
        arrowprops=dict(arrowstyle="->", color="black"),
        fontsize=9,
    )

    ax.set_title("综合评分分布（Score Distribution）")
    ax.set_xlabel("综合评分（0–100）")
    ax.set_ylabel("股票数量")
    ax.set_xlim(0, 100)
    ax.grid(axis="y", linestyle=":", alpha=0.45)

    zone_handles = [
        mpatches.Patch(facecolor=_color_for_bin(RECOMMENDED_MIN + 10), edgecolor="#333333", label="≥75（推荐区）"),
        mpatches.Patch(facecolor=_color_for_bin(62), edgecolor="#333333", label="50–75（中性区）"),
        mpatches.Patch(facecolor=_color_for_bin(30), edgecolor="#333333", label="<50（不推荐区）"),
    ]
    avg_line_handle = mlines.Line2D(
        [], [], color="#1f77b4", linestyle="--", linewidth=1.4, label=f"平均分 {mean_v:.2f}"
    )

    ax.legend(handles=[*zone_handles, avg_line_handle], loc="upper right", framealpha=0.92)

    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
