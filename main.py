"""
资产配置再平衡管理工具 - 主入口

用法: python3 main.py <portfolio.xlsx> [--output report.xlsx]
"""
import argparse
import logging
import sys

import config as cfg
import data_loader
import rebalancer
import report

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="资产配置再平衡分析工具")
    parser.add_argument("input", help="持仓 Excel 文件路径")
    parser.add_argument("--output", "-o", default=cfg.OUTPUT_REPORT, help="输出报表路径")
    args = parser.parse_args()

    # 1. 加载数据
    logger.info(f"读取文件: {args.input}")
    amounts = data_loader.load_portfolio(args.input)

    # 2. 分析偏离
    result = rebalancer.analyze(amounts)

    # 3. 打印摘要
    print("\n" + "=" * 50)
    print("  资产配置再平衡分析报告")
    print("=" * 50)
    print(f"总资产: ¥{result.total_amount:,.2f}\n")

    for d in result.deviations:
        flag = "⚠️" if d.need_rebalance else "✅"
        print(f"  {flag} [{d.layer}] {d.name}: "
              f"{d.current_ratio:.2%} → 目标 {d.target_ratio:.2%} "
              f"(偏离 {d.deviation:+.2%}) {d.action}")

    if result.need_rebalance:
        print(f"\n⚠️  需要再平衡！")
        print(f"\n{'─' * 50}")
        print("  操作计划（先买入后卖出）")
        print(f"{'─' * 50}")
        for i, a in enumerate(result.actions, 1):
            emoji = "🟢" if a.action == "买入" else "🔴"
            print(f"  {i}. {emoji} {a.action} [{a.tag}] ¥{a.amount:,.2f}"
                  f"  (¥{a.current:,.2f} → ¥{a.target:,.2f})")
    else:
        print(f"\n✅ 当前配置在合理范围内，无需调整。")

    # 4. 生成报表
    out = report.generate(result, args.output)
    print(f"\n报表已保存: {out}\n")


if __name__ == "__main__":
    main()
