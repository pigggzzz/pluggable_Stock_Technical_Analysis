"""全局配置：路径、阈值、权重等。"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REPORT_MD = OUTPUT_DIR / "report.md"
RANK_CSV = OUTPUT_DIR / "rankings.csv"
RANK_XLSX = OUTPUT_DIR / "rankings.xlsx"
SCORE_DIST_PNG = OUTPUT_DIR / "score_distribution.png"

# 数据起始日（月线 MA120 等需要足够历史）
DEFAULT_START_DATE = "20130101"

# 时间框架加权
TF_WEIGHTS = {
    "daily": 0.35,
    "weekly": 0.35,
    "monthly": 0.30,
}

# 推荐阈值（0~100 综合分）
RECOMMENDED_MIN = 70.0
NEUTRAL_MIN = 50.0
