"""
再平衡计算引擎 - 对比当前配置与基准，判断是否需要调整
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, List

import config as cfg

logger = logging.getLogger(__name__)


@dataclass
class DeviationItem:
    """单条偏离记录"""
    layer: str          # 所属层级，如 "第一层：现金 vs 其他"
    name: str           # 比较项名称，如 "现金"
    current_ratio: float
    target_ratio: float
    deviation: float    # current - target
    need_rebalance: bool
    action: str         # "增加" / "减少" / "无需调整"


@dataclass
class ActionItem:
    """单条操作指令"""
    tag: str            # 资产类型
    action: str         # "买入" / "卖出"
    amount: float       # 操作金额（正数）
    current: float      # 当前金额
    target: float       # 目标金额
    current_ratio: float = 0.0   # 当前占总资产比例
    target_ratio: float = 0.0    # 目标占总资产比例
    formula: str = ""            # 目标比例计算公式


@dataclass
class RebalanceResult:
    """完整的再平衡分析结果"""
    total_amount: float
    amounts: Dict[str, float]
    deviations: List[DeviationItem] = field(default_factory=list)
    actions: List[ActionItem] = field(default_factory=list)

    @property
    def need_rebalance(self) -> bool:
        return any(d.need_rebalance for d in self.deviations)


def _check(layer: str, name: str, current: float, target: float) -> DeviationItem:
    """检查单个比例是否偏离超过阈值"""
    dev = current - target
    need = abs(dev) > cfg.REBALANCE_THRESHOLD
    if not need:
        action = "无需调整"
    elif dev > 0:
        action = "减少"
    else:
        action = "增加"
    return DeviationItem(layer, name, current, target, dev, need, action)


def analyze(amounts: Dict[str, float]) -> RebalanceResult:
    """
    分析当前持仓与基准的偏离情况。

    Args:
        amounts: {tag: 金额} 字典

    Returns:
        RebalanceResult 包含所有偏离项
    """
    total = sum(amounts.values())
    if total <= 0:
        raise ValueError("总资产为 0，无法计算比例")

    cash = amounts.get(cfg.TAG_CASH, 0)
    bond = amounts.get(cfg.TAG_BOND, 0)
    stock_large = amounts.get(cfg.TAG_STOCK_LARGE, 0)
    stock_div = amounts.get(cfg.TAG_STOCK_DIVIDEND, 0)
    stock_star = amounts.get(cfg.TAG_STOCK_STAR, 0)
    stock_consumer = amounts.get(cfg.TAG_STOCK_CONSUMER, 0)
    stock_total = stock_large + stock_div + stock_star + stock_consumer
    other = stock_total + bond  # 其他资产 = 股票 + 债券

    result = RebalanceResult(total_amount=total, amounts=amounts)

    # --- 第一层：现金 vs 其他资产 ---
    r_cash = cash / total
    r_other = other / total
    result.deviations.append(_check("第一层：现金 vs 其他", "现金", r_cash, cfg.TARGET_CASH_RATIO))
    result.deviations.append(_check("第一层：现金 vs 其他", "其他资产", r_other, cfg.TARGET_OTHER_RATIO))

    # --- 第二层：股票 vs 债券（在其他资产中） ---
    if other > 0:
        r_stock = stock_total / other
        r_bond = bond / other
    else:
        r_stock = r_bond = 0
    result.deviations.append(_check("第二层：股票 vs 债券", "股票", r_stock, cfg.TARGET_STOCK_IN_OTHER))
    result.deviations.append(_check("第二层：股票 vs 债券", "债券", r_bond, cfg.TARGET_BOND_IN_OTHER))

    # --- 第三层：大盘 vs 红利 vs 科创（在股票中） ---
    if stock_total > 0:
        r_large = stock_large / stock_total
        r_div = stock_div / stock_total
        r_star = stock_star / stock_total
        r_consumer = stock_consumer / stock_total
    else:
        r_large = r_div = r_star = r_consumer = 0
    result.deviations.append(_check("第三层：股票内部", "大盘", r_large, cfg.TARGET_LARGE_IN_STOCK))
    result.deviations.append(_check("第三层：股票内部", "红利", r_div, cfg.TARGET_DIVIDEND_IN_STOCK))
    result.deviations.append(_check("第三层：股票内部", "科创", r_star, cfg.TARGET_STAR_IN_STOCK))
    result.deviations.append(_check("第三层：股票内部", "消费", r_consumer, cfg.TARGET_CONSUMER_IN_STOCK))

    # --- 生成操作计划：计算每个 tag 的目标金额 ---
    if result.need_rebalance:
        # 目标金额 = 总资产 × 各层比例连乘
        target_amounts = {
            cfg.TAG_CASH: total * cfg.TARGET_CASH_RATIO,
            cfg.TAG_BOND: total * cfg.TARGET_OTHER_RATIO * cfg.TARGET_BOND_IN_OTHER,
            cfg.TAG_STOCK_LARGE: total * cfg.TARGET_OTHER_RATIO * cfg.TARGET_STOCK_IN_OTHER * cfg.TARGET_LARGE_IN_STOCK,
            cfg.TAG_STOCK_DIVIDEND: total * cfg.TARGET_OTHER_RATIO * cfg.TARGET_STOCK_IN_OTHER * cfg.TARGET_DIVIDEND_IN_STOCK,
            cfg.TAG_STOCK_STAR: total * cfg.TARGET_OTHER_RATIO * cfg.TARGET_STOCK_IN_OTHER * cfg.TARGET_STAR_IN_STOCK,
            cfg.TAG_STOCK_CONSUMER: total * cfg.TARGET_OTHER_RATIO * cfg.TARGET_STOCK_IN_OTHER * cfg.TARGET_CONSUMER_IN_STOCK,
        }
        # 计算公式说明
        formulas = {
            cfg.TAG_CASH: "10%（现金占总资产）",
            cfg.TAG_BOND: "90% × 30% = 27%（其他资产占比 × 债券在其他中占比）",
            cfg.TAG_STOCK_LARGE: "90% × 70% × 50% = 31.5%（其他 × 股票 × 大盘）",
            cfg.TAG_STOCK_DIVIDEND: "90% × 70% × 30% = 18.9%（其他 × 股票 × 红利）",
            cfg.TAG_STOCK_STAR: "90% × 70% × 15% = 9.45%（其他 × 股票 × 科创）",
            cfg.TAG_STOCK_CONSUMER: "90% × 70% × 5% = 3.15%（其他 × 股票 × 消费）",
        }
        for tag in [t for t in cfg.ALL_TAGS if t != cfg.TAG_CASH]:
            cur = amounts.get(tag, 0)
            tgt = target_amounts[tag]
            diff = tgt - cur
            if abs(diff) >= 1:  # 忽略 1 元以下的零头
                result.actions.append(ActionItem(
                    tag=tag,
                    action="买入" if diff > 0 else "卖出",
                    amount=abs(diff),
                    current=cur,
                    target=tgt,
                    current_ratio=cur / total,
                    target_ratio=tgt / total,
                    formula=formulas[tag],
                ))
        # 先买入后卖出排序
        result.actions.sort(key=lambda a: (0 if a.action == "买入" else 1, -a.amount))

    logger.info(f"分析完成，需要再平衡: {result.need_rebalance}")
    return result
