"""
标签模块 - 根据基金名称 rule-based 自动打 tag
"""
import config as cfg

# 关键词 → tag 映射（优先级从上到下，先匹配先命中）
TAG_RULES = [
    # 现金类
    (cfg.TAG_CASH, ["货币", "现金", "余额", "活期", "零钱"]),
    # 债券类
    (cfg.TAG_BOND, ["债", "国债", "信用", "利率", "纯债", "固收"]),
    # 科创类
    (cfg.TAG_STOCK_STAR, ["科创", "科技创新", "双创"]),
    # 消费类
    (cfg.TAG_STOCK_CONSUMER, ["消费", "白酒", "食品", "医药", "家电"]),
    # 红利类
    (cfg.TAG_STOCK_DIVIDEND, ["红利", "高股息", "股息", "分红"]),
    # 大盘类（兜底，宽基指数）
    (cfg.TAG_STOCK_LARGE, ["沪深300", "上证50", "中证500", "中证1000", "创业板",
                           "大盘", "指数", "ETF", "LOF"]),
]


def auto_tag(fund_name: str) -> str:
    """
    根据基金名称自动匹配 tag。

    Args:
        fund_name: 基金名称

    Returns:
        匹配到的 tag，未匹配返回空字符串
    """
    for tag, keywords in TAG_RULES:
        if any(kw in fund_name for kw in keywords):
            return tag
    return ""
