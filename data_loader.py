"""
数据加载模块 - 读取 Excel 并按最新日期汇总各类资产金额
"""
import logging
from typing import Dict

import pandas as pd

import config as cfg

logger = logging.getLogger(__name__)


def load_portfolio(filepath: str) -> Dict[str, float]:
    """
    读取 Excel，返回最新日期各 tag 的汇总金额。

    Args:
        filepath: Excel 文件路径

    Returns:
        {tag: 汇总金额} 字典，如 {"现金": 10000, "债券": 30000, ...}
    """
    df = pd.read_excel(filepath)

    # 校验必要列
    required = list(cfg.COLUMN_MAP.values())
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Excel 缺少必要列: {missing}")

    # 取最新日期的数据
    col_date = cfg.COLUMN_MAP["date"]
    col_amount = cfg.COLUMN_MAP["amount"]
    col_tag = cfg.COLUMN_MAP["tag"]

    df[col_date] = pd.to_datetime(df[col_date])
    latest = df[col_date].max()
    df_latest = df[df[col_date] == latest]
    logger.info(f"使用日期: {latest.strftime('%Y-%m-%d')}，共 {len(df_latest)} 条记录")

    # 校验 tag 合法性
    invalid = set(df_latest[col_tag]) - set(cfg.ALL_TAGS)
    if invalid:
        raise ValueError(f"存在未知类型 tag: {invalid}")

    # 校验银行名称
    col_bank = cfg.COLUMN_MAP["bank"]
    if col_bank in df_latest.columns:
        invalid_banks = set(df_latest[col_bank]) - set(cfg.ALLOWED_BANKS)
        if invalid_banks:
            raise ValueError(f"存在未知银行/平台: {invalid_banks}，合法值: {cfg.ALLOWED_BANKS}")

    # 按 tag 汇总
    summary = df_latest.groupby(col_tag)[col_amount].sum().to_dict()
    # 确保所有 tag 都有值
    for tag in cfg.ALL_TAGS:
        summary.setdefault(tag, 0.0)

    logger.info(f"资产汇总: {summary}")
    return summary


def load_raw_items(filepath: str) -> list:
    """
    读取 Excel 最新日期数据，返回 db.save_holdings 所需格式。

    Returns:
        [{"name": "沪深300", "amount": 35000, "tag": "大盘"}, ...]
    """
    df = pd.read_excel(filepath)
    col_date, col_name = cfg.COLUMN_MAP["date"], cfg.COLUMN_MAP["fund_name"]
    col_amount, col_tag = cfg.COLUMN_MAP["amount"], cfg.COLUMN_MAP["tag"]
    col_bank = cfg.COLUMN_MAP["bank"]

    df[col_date] = pd.to_datetime(df[col_date])
    df_latest = df[df[col_date] == df[col_date].max()]

    return [{"name": r[col_name], "amount": float(r[col_amount]), "tag": r[col_tag],
             "bank": r.get(col_bank, "") if col_bank in df.columns else ""}
            for _, r in df_latest.iterrows()]