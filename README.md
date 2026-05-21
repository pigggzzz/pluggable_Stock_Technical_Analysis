# 沪深 A 股技术面评分

轻量级 Python 小项目：给定**自拟股票池**，用经典技术指标与规则在日 / 周 / 月三个时间框架下打分，输出**排名**、**Markdown 研判报告**，以及一张**综合分分布直方图**。面向课程说明与可复现演示，**不是**量化实盘、不含回测与机器学习。

## 功能概览

- 数据来源：[AKShare](https://github.com/akfamily/akshare) **`stock_zh_a_daily`**（新浪财经日线），相对稳定。
- 将日线聚合为 **周线 / 月线**，字段统一：`date, open, high, low, close, volume, amount`。
- 指标：`MA5` / `MA20` / `MA60` / `MA120`、`MACD(12,26,9)`、`RSI6` / `RSI14`、累积 **OBV**。
- 策略（可勾选）：简化 **葛兰碧均线四类**、`MACD`、`RSI`、`OBV`。
- **综合分 0～100**：各策略在日/周/月原始分加权后线性归一化；标签阈值见 `config/settings.py`。
- **输出**：样本内综合分**最高 / 最低**各一只的解读（报告中）、全体排名 **CSV/XLSX**、`score_distribution.png`。

## 环境要求

- Python 3.10+（建议使用 venv / conda）
- 依赖见 `requirements.txt`

## 快速开始

```bash
cd stock_analysis
pip install -r requirements.txt
python main.py
```

成功后在 **`output/`** 目录生成：

| 文件 | 说明 |
|------|------|
| `report.md` | 研判时间、样本池说明、综合分最高/最低标的的规则叙述、附录排名表 |
| `rankings.csv` / `rankings.xlsx` | 排序、代码、综合分、标签、`daily_raw`/`weekly_raw`/`monthly_raw` 等 |
| `score_distribution.png` | 全体综合分分布直方图（分区着色及最高、最低与平均分示意） |

单只股票抓取失败时会打印 `[SKIP]` 并跳过，其余照常；若全部失败则提前退出。

## 项目结构

```text
stock_analysis/
├── main.py                  # 入口：策略勾选、遍历股票池、写报告与图
├── requirements.txt
├── README.md
├── config/
│   ├── settings.py          # 输出路径、起始日期、周期权重、推荐阈值等
│   └── stock_pool.py        # 六位股票代码列表（手动维护）
├── data/
│   ├── data_loader.py       # AKShare 日线 + 标准字段
│   └── timeframe.py         # 周线 / 月线聚合
├── indicators/              # MA / MACD / RSI / OBV（只做数值）
├── strategies/              # granville / macd / rsi / obv（继承 base）
├── scoring/
│   └── scorer.py            # 挂指标、多周期合并与 0～100 归一化
├── report/
│   └── generator.py         # Markdown 报告
├── visualization/
│   └── plotter.py           # matplotlib 分布图
└── output/                  # 运行产物（可自行加入 .gitignore）
```

## 常用配置

### 股票池（`config/stock_pool.py`）

在 **`STOCK_POOL`** 里维护 **`6`** 位代码（例：`600519`）。  
数据源为新浪：`6` 开头映射为 **`sh……`**，否则默认 **`sz……`**（北交所等需在 `data/data_loader.py` 中另行扩展前缀）。

### 数据跨度（`config/settings.py`）

- **`DEFAULT_START_DATE`**：形如 `YYYYMMDD`。月线、`MA120` 等依赖较长历史，不宜设得过晚。

### 推荐 / 中性 / 不推荐（`config/settings.py`）

- **`RECOMMENDED_MIN`**、**`NEUTRAL_MIN`**：作用于**归一化后**的综合分（0～100），可按任课要求修改。

### 周期权重（`config/settings.py`）

- **`TF_WEIGHTS`**：日线 / 周线 / 月线默认 **`0.35 / 0.35 / 0.30`**，与分项原始分加权后再归一化。

### 启用策略（`main.py`）

```python
SELECTED_STRATEGIES = ["granville", "macd", "rsi", "obv"]
```

只写上述四类 key；勾选结果与理论分值边界共同决定归一尺度，边界定义在 **`scoring/scorer.py`** 的 `BOUNDS_REGISTRY`。

## 设计说明（作业向）

- **指标层**：只计算序列；**策略层**：按规则判断是否触发、`signals` 里带规则名、是否触发、分数、解释与可选日期。
- **主流程**：`main.py` 串联加载 → 多周期指标 → 每策略在日/周/月各跑一次 → **scorer** 汇总 → 排名 → **report** + **plotter**。
- **报告表述**：写的是**当前股票池内**综合分排名第一与垫底标的，用词偏课程技术分析；**不构成投资建议**。

## 依赖一览

```
pandas numpy akshare matplotlib openpyxl
```

- **`openpyxl`**：`rankings.xlsx` 需要；环境中若缺失会提示警告，仍可得到 CSV/Markdown/图。
- **网络 / 代理**：`akshare` 需访问新浪等数据源；若出现 `ProxyError` 或与代理相关错误，请检查本机 **`HTTP_PROXY` / `HTTPS_PROXY`** 是否正常，或在可直连网络下重跑。

## 免责声明

本项目仅用于学习与课程作业。历史走势与技术指标不预示未来收益，请勿当作实盘下单依据。

---

若要改报告板式或话术，可读 **`report/generator.py`**；若要改打分规则，优先改 **`strategies/`** 对应类与 **`scoring/scorer.py`** 中的边界常量，保持勾选策略与边界一致。
