"""
报表生成模块 - 将再平衡分析结果输出为 Excel 报表
"""
import logging

import pandas as pd

import config as cfg
from rebalancer import RebalanceResult

logger = logging.getLogger(__name__)


def generate(result: RebalanceResult, output_path: str = cfg.OUTPUT_REPORT) -> str:
    """
    生成再平衡报表 Excel。

    Args:
        result: 再平衡分析结果
        output_path: 输出文件路径

    Returns:
        输出文件路径
    """
    # 构建偏离明细表
    rows = []
    for d in result.deviations:
        rows.append({
            "层级": d.layer,
            "项目": d.name,
            "当前比例": f"{d.current_ratio:.2%}",
            "目标比例": f"{d.target_ratio:.2%}",
            "偏离": f"{d.deviation:+.2%}",
            "是否需要调整": "是" if d.need_rebalance else "否",
            "操作建议": d.action,
        })
    df_detail = pd.DataFrame(rows)

    # 构建资产汇总表
    summary_rows = [{"类型": tag, "金额": result.amounts.get(tag, 0)} for tag in cfg.ALL_TAGS]
    summary_rows.append({"类型": "合计", "金额": result.total_amount})
    df_summary = pd.DataFrame(summary_rows)

    # 构建操作计划表
    action_rows = []
    for i, a in enumerate(result.actions, 1):
        action_rows.append({
            "步骤": i,
            "操作": a.action,
            "类型": a.tag,
            "金额": f"¥{a.amount:,.2f}",
            "当前金额": f"¥{a.current:,.2f}",
            "目标金额": f"¥{a.target:,.2f}",
        })
    df_actions = pd.DataFrame(action_rows)

    # 写入 Excel（三个 sheet）
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df_summary.to_excel(writer, sheet_name="资产汇总", index=False)
        df_detail.to_excel(writer, sheet_name="偏离分析", index=False)
        if not df_actions.empty:
            df_actions.to_excel(writer, sheet_name="操作计划", index=False)

    logger.info(f"报表已生成: {output_path}")
    return output_path
