"""
课程作业用股票池：在此手动维护沪深 A 股代码列表。
akshare stock_zh_a_hist 使用 6 位代码，深市一般 0xxxxxx，沪市 6xxxxxx。
"""

import akshare as ak

# def get_csi500_symbols():
#     """
#     获取中证500成分股，返回 6 位代码列表
#     """
#     df = ak.index_stock_cons("000905")  # 中证500指数代码
#     symbols = df["品种代码"].astype(str).str.zfill(6).tolist()
#     return symbols

# # 替代原来的手动 STOCK_POOL
# STOCK_POOL = get_csi500_symbols()

def get_hs300_symbols():
    """
    获取沪深300成分股，返回 6 位代码列表
    """
    df = ak.index_stock_cons("000300")  # 沪深300指数代码
    symbols = df["品种代码"].astype(str).str.zfill(6).tolist()
    return symbols

# 替代原来的手动 STOCK_POOL
STOCK_POOL = get_hs300_symbols()