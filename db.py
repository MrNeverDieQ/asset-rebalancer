"""
数据库模块 - SQLite 存储持仓记录
"""
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict

import config as cfg

logger = logging.getLogger(__name__)


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(cfg.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fund_name TEXT NOT NULL,
            bank TEXT NOT NULL DEFAULT '',
            amount REAL NOT NULL,
            tag TEXT NOT NULL,
            record_date TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    return conn


def save_holdings(items: List[Dict], record_date: str = None) -> int:
    """
    保存一批持仓记录。

    Args:
        items: [{"name": "沪深300", "amount": 35000, "tag": "大盘"}, ...]
        record_date: 记录日期，默认今天

    Returns:
        插入的记录数
    """
    if not record_date:
        record_date = datetime.now().strftime("%Y-%m-%d")

    conn = _get_conn()
    try:
        conn.executemany(
            "INSERT INTO holdings (fund_name, bank, amount, tag, record_date) VALUES (?, ?, ?, ?, ?)",
            [(i["name"], i.get("bank", ""), float(i["amount"]), i["tag"], record_date) for i in items]
        )
        conn.commit()
        logger.info(f"保存 {len(items)} 条记录，日期 {record_date}")
        return len(items)
    finally:
        conn.close()


def get_latest_holdings() -> Dict[str, float]:
    """
    获取最新日期的持仓，按 tag 汇总金额。

    Returns:
        {tag: 汇总金额}
    """
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT tag, SUM(amount) as total FROM holdings "
            "WHERE record_date = (SELECT MAX(record_date) FROM holdings) "
            "GROUP BY tag"
        ).fetchall()
        return {r["tag"]: r["total"] for r in rows}
    finally:
        conn.close()


def get_all_records() -> List[Dict]:
    """获取所有历史记录"""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM holdings ORDER BY record_date DESC, id DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
