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
    │   ├── 科创 15%
    │   └── 消费 5%
    └── 债券 30%
```

任一比例偏离基准超过 **5%** 即触发再平衡。偏离按层级独立计算。

## 核心功能

- **三层偏离检查**：现金/其他、股票/债券、大盘/红利/科创/消费
- **最优操作计划**：直接计算每个 tag 的目标金额，合并多层级调整为最少操作次数
- **先买入后卖出**：考虑赎回时间差，优先建仓
- **现金自动推算**：非现金操作完成后，现金变动量自动计算
- **OCR 截图识别**：上传手机截图，自动识别基金名称和金额
- **SQLite 持久化**：持仓数据存入 DB，按日期+银行快照覆盖，防止重复
- **银行名称校验**：严格限制合法银行（招商银行、平安银行、民生银行）

## 输入 Excel 格式

| 基金名称 | 时间 | 金额 | 类型 | 银行/平台 |
|---------|------|------|------|----------|
| 沪深300 | 2026-04-15 | 35000 | 大盘 | 招商银行 |

- 类型可选值：`现金`、`债券`、`大盘`、`红利`、`科创`、`消费`
- 银行可选值：`招商银行`、`平安银行`、`民生银行`
- 多日期时仅使用最新日期，页面会提示

## 使用方法

### 方式一：Docker（推荐，无需关心 Python 版本）

```bash
git clone https://github.com/MrNeverDieQ/asset-rebalancer.git
cd asset-rebalancer
docker build -t asset-rebalancer .
docker run -p 40511:40511 asset-rebalancer
```

### 方式二：本地运行（需要 Python 3.8+）

```bash
git clone https://github.com/MrNeverDieQ/asset-rebalancer.git
cd asset-rebalancer
pip install -r requirements.txt
python3 app.py
```

浏览器打开 http://localhost:40511

两种数据录入方式：
1. **Excel 分析**：上传 Excel 文件
2. **截图识别**：上传手机截图 → OCR 识别 → 校验编辑 → 保存

## 项目结构

```
asset-rebalancer/
├── config.py         # 配置（基准比例、阈值、银行白名单）
├── data_loader.py    # Excel 数据加载与校验
├── rebalancer.py     # 偏离分析 + 操作计划生成
├── db.py             # SQLite 持仓存储
├── ocr.py            # OCR 截图识别
├── tagger.py         # 基金类型自动打标
├── app.py            # Flask Web 应用
├── templates/
│   ├── index.html    # Excel 分析页面
│   └── ocr.html      # 截图识别页面
└── create_sample.py  # 生成示例数据
```
