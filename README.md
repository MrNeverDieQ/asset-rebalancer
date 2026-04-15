# 资产配置再平衡管理工具

根据预设的资产配置比例基准，分析当前持仓是否需要再平衡。

## 基准配置

```
总资产
├── 现金 10%
└── 其他资产 90%
    ├── 股票 70%
    │   ├── 大盘 50%
    │   ├── 红利 30%
    │   └── 科创 20%
    └── 债券 30%
```

任一比例偏离基准超过 **5%** 即触发再平衡提醒。

## 输入 Excel 格式

| 基金名称 | 时间 | 金额 | 类型 |
|---------|------|------|------|
| 沪深300 | 2026-04-15 | 35000 | 大盘 |

类型可选值：`现金`、`债券`、`大盘`、`红利`、`科创`

## 使用方法

```bash
# 生成示例数据
python3 create_sample.py

# 运行分析
python3 main.py sample_portfolio.xlsx

# 指定输出路径
python3 main.py sample_portfolio.xlsx -o my_report.xlsx
```

## 依赖

```bash
pip install pandas openpyxl
```

## 项目结构

```
asset-rebalancer/
├── config.py         # 配置（基准比例、阈值、列名）
├── data_loader.py    # 数据加载
├── rebalancer.py     # 再平衡计算引擎
├── report.py         # 报表生成
├── main.py           # 主入口
└── create_sample.py  # 生成示例数据
```
