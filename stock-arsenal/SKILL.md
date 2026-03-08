---
name: stock-arsenal
description: A股市场分析工具，提供涨停板预测、智能选股、游资跟踪、买入信号、跌停预警5个核心功能。当用户询问A股相关分析、选股、涨停预测、游资动向、买卖信号、风险预警等股市分析任务时使用此skill。
---

# A股武器库 (Stock Arsenal)

## Overview

基于GitHub开源项目（akshare、efinance、baostock）封装的A股分析工具，提供5个核心功能：涨停板预测、智能选股器、游资席位跟踪、买入信号分析、跌停板预警。帮助用户快速进行股市数据分析，发现投资机会和规避风险。

## 快速开始

### 首次使用

1. **检查环境**：确认Python 3.8+已安装
2. **安装依赖**：运行 `scripts/install_dependencies.py`
3. **验证安装**：运行 `python src/main.py` 测试

### 使用流程

当用户提出A股分析需求时：
1. 识别用户意图，匹配对应功能
2. 运行对应的分析脚本
3. 解析并呈现结果

## 核心功能

### 1. 涨停板预测

**触发场景：**
- "明天哪些股票会涨停？"
- "涨停预测"
- "今日强势股分析"
- "找出涨停潜力股"

**执行方式：**
```bash
python scripts/analyze_limit_up.py
```

**输出内容：**
- Top 20强势股排名
- 综合评分（涨幅+量比+换手+封单+技术面）
- 评级（5星到1星）
- 明日延续概率分析

---

### 2. 智能选股器

**触发场景：**
- "帮我选一些好股票"
- "低估值股票筛选"
- "智能选股"
- "找一些价值投资的股票"

**执行方式：**
```bash
python scripts/stock_screener.py
```

**筛选条件：**
- PE < 50（低估值）
- PB < 10（低估值）
- 涨跌幅 -2% ~ 5%（稳健）
- RSI 30-70（不超买不超卖）

**输出内容：**
- 符合条件的股票列表
- PE、PB、RSI等关键指标
- 通过条件数量

---

### 3. 游资席位跟踪

**触发场景：**
- "最近游资在买什么？"
- "游资动向"
- "龙虎榜分析"
- "知名游资席位"

**执行方式：**
```bash
python scripts/track_hot_money.py
```

**输出内容：**
- 最近5日龙虎榜游资统计
- 各席位净买入金额
- 上榜次数
- 操作风格分析

---

### 4. 买入信号

**触发场景：**
- "XX股票现在可以买吗？"
- "买入时机分析"
- "贵州茅台有买入信号吗？"
- "给出买入建议"

**执行方式：**
```bash
python scripts/check_buy_signal.py [股票代码]
```

**评分维度：**
- RSI超卖检测（30分）
- MACD金叉（25分）
- 放量上涨（25分）
- 均线多头（20分）

**输出内容：**
- 买入建议（强烈买入/可以买入/观望/不建议）
- 综合得分
- 信号详情

---

### 5. 跌停板预警

**触发场景：**
- "今日跌停风险"
- "持仓风险预警"
- "哪些股票有跌停风险？"
- "检查风险"

**执行方式：**
```bash
python scripts/check_limit_down_risk.py
```

**风险维度：**
- 跌幅（30分）
- 量比（20分）
- 技术面（25分）
- 质押风险（25分）

**输出内容：**
- 高风险股票列表
- 风险等级（极高风险/高风险/中风险）
- 风险因素详情

## 功能映射表

| 用户查询 | 对应功能 | 脚本 |
|---------|---------|------|
| 明天涨停股 | 涨停板预测 | analyze_limit_up.py |
| 选股/筛选股票 | 智能选股器 | stock_screener.py |
| 游资/龙虎榜 | 游资跟踪 | track_hot_money.py |
| 买入建议 | 买入信号 | check_buy_signal.py |
| 跌停风险 | 跌停预警 | check_limit_down_risk.py |
| 股市分析 | 全部功能 | main.py |

## 数据源说明

本项目使用三大数据源（智能路由）：
- **efinance**：东方财富官方数据，实时性最好（推荐）
- **akshare**：数据最全，功能丰富
- **baostock**：复权数据准确，适合历史分析

## 注意事项

1. **数据时效性**：实时数据在交易时间（9:30-15:00）最准确
2. **免责声明**：本工具仅供学习参考，不构成投资建议
3. **风险提示**：股市有风险，投资需谨慎
4. **数据限制**：非交易时间数据可能为空或延迟

## 故障排查

### 依赖安装问题
```bash
# 最小依赖（推荐）
pip install efinance rich pyyaml loguru pandas

# 完整依赖
pip install -r requirements.txt
```

### 数据为空
- 检查是否在交易时间
- 查看日志：`logs/stock_arsenal_error.log`

### 编码错误
```bash
export PYTHONIOENCODING=utf-8
```

## 资源文件

### scripts/
- `install_dependencies.py` - 依赖安装脚本
- `analyze_limit_up.py` - 涨停板预测
- `stock_screener.py` - 智能选股
- `track_hot_money.py` - 游资跟踪
- `check_buy_signal.py` - 买入信号
- `check_limit_down_risk.py` - 跌停预警

### references/
- `USER_GUIDE.md` - 详细使用指南
- `API_REFERENCE.md` - API参考文档
- `TROUBLESHOOTING.md` - 故障排查指南

## 使用技巧

1. **组合使用**：涨停预测 + 游资跟踪 = 找强势股
2. **风控第一**：先用跌停预警检查持仓风险
3. **时间选择**：
   - 盘前（9:00-9:25）：涨停预测
   - 盘中（10:00-14:00）：买入信号
   - 盘后（15:30-18:00）：智能选股

## 扩展开发

如需添加新功能，参考 `references/DEVELOPMENT.md` 中的扩展指南。

**核心原则：**
- 继承 `BaseModule` 基类
- 实现 `get_data()`、`analyze()`、`format_output()` 方法
- 在 `main_menu.py` 中注册新功能
