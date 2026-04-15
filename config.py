"""
资产配置再平衡 - 配置文件
"""

# ============ Excel 列名映射 ============
COLUMN_MAP = {
    "fund_name": "基金名称",
    "date": "时间",
    "amount": "金额",
    "tag": "类型",
    "bank": "银行/平台",
}

# ============ 资产类型 tag ============
# Excel 中"类型"列的合法值
TAG_CASH = "现金"
TAG_BOND = "债券"
TAG_STOCK_LARGE = "大盘"
TAG_STOCK_DIVIDEND = "红利"
TAG_STOCK_STAR = "科创"
TAG_STOCK_CONSUMER = "消费"

ALL_STOCK_TAGS = [TAG_STOCK_LARGE, TAG_STOCK_DIVIDEND, TAG_STOCK_STAR, TAG_STOCK_CONSUMER]
ALL_TAGS = [TAG_CASH, TAG_BOND] + ALL_STOCK_TAGS

# ============ 基准配置（目标比例） ============
# 第一层：现金 vs 其他资产 = 1:9
TARGET_CASH_RATIO = 0.10       # 现金占总资产 10%
TARGET_OTHER_RATIO = 0.90      # 其他资产占总资产 90%

# 第二层：其他资产中，股票 vs 债券 = 7:3
TARGET_STOCK_IN_OTHER = 0.70   # 股票占其他资产 70%
TARGET_BOND_IN_OTHER = 0.30    # 债券占其他资产 30%

# 第三层：股票中，大盘:红利:科创:消费 = 5:3:1.5:0.5
TARGET_LARGE_IN_STOCK = 0.50
TARGET_DIVIDEND_IN_STOCK = 0.30
TARGET_STAR_IN_STOCK = 0.15
TARGET_CONSUMER_IN_STOCK = 0.05

# ============ 再平衡阈值 ============
REBALANCE_THRESHOLD = 0.05     # 偏离 5% 触发再平衡

# ============ 输出 ============
OUTPUT_REPORT = "rebalance_report.xlsx"

# ============ 数据库 ============
DB_PATH = "portfolio.db"