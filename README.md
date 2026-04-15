# 资产配置再平衡管理工具

根据预设的资产配置比例基准，分析当前持仓偏离情况，生成最优操作计划。

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

任一比例偏离基准超过 **5%** 即触发再平衡。偏离按层级独立计算。

## 核心功能

- **三层偏离检查**：现金/其他、股票/债券、大盘/红利/科创
- **最优操作计划**：直接计算每个 tag 的目标金额，合并多层级调整为最少操作次数
- **先买入后卖出**：考虑赎回时间差，优先建仓
- **现金自动推算**：非现金操作完成后，现金变动量自动计算，无需单独操作

## 输入 Excel 格式

| 基金名称 | 时间 | 金额 | 类型 |
|---------|------|------|------|
| 沪深300 | 2026-04-15 | 35000 | 大盘 |

类型可选值：`现金`、`债券`、`大盘`、`红利`、`科创`

## 使用方法

### Web 界面（推荐）

```bash
python3 app.py
# 浏览器打开 http://localhost:40511
```

上传 Excel → 查看偏离分析 + 操作计划

### 命令行

```bash
python3 main.py portfolio.xlsx
python3 main.py portfolio.xlsx -o my_report.xlsx
```

### 生成示例数据

```bash
python3 create_sample.py
```

## 依赖

```bash
pip install pandas openpyxl flask
```

## 项目结构

```
asset-rebalancer/
├── config.py         # 配置（基准比例、阈值、列名）
├── data_loader.py    # Excel 数据加载
├── rebalancer.py     # 偏离分析 + 操作计划生成
├── report.py         # Excel 报表生成（CLI 模式）
├── app.py            # Flask Web 应用
├── templates/
│   └── index.html    # Web 界面
├── main.py           # CLI 入口
└── create_sample.py  # 生成示例数据
```
