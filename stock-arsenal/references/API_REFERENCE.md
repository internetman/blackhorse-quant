# A股武器库 - API参考

## 核心模块API

### LimitUpPredictor (涨停板预测)

```python
from src.services.limit_up_predictor import LimitUpPredictor

module = LimitUpPredictor()
result = module.run()  # 返回分析结果
```

**输出格式：**
```
🔥 涨停板预测 (Top 20)
====================================
⭐⭐⭐⭐⭐ 极强    600519    贵州茅台    ...
...
```

---

### StockScreener (智能选股)

```python
from src.services.stock_screener import StockScreener

module = StockScreener()
result = module.run()  # 返回符合条件的股票
```

**筛选条件：**
- PE < 50
- PB < 10
- RSI 30-70
- 涨跌幅 -2% ~ 5%

---

### HotMoneyTracker (游资跟踪)

```python
from src.services.hot_money_tracker import HotMoneyTracker

module = HotMoneyTracker()
result = module.run(days=5)  # 最近5日数据
```

---

### BuySignal (买入信号)

```python
from src.services.buy_signal import BuySignal

module = BuySignal()

# 分析指定股票
result = module.run(symbols=['600519.SH', '000001.SZ'])

# 分析市场热门股
result = module.run()
```

**评分体系：**
- RSI超卖 (30分)
- MACD金叉 (25分)
- 放量上涨 (25分)
- 均线多头 (20分)

---

### LimitDownPredictor (跌停预警)

```python
from src.services.limit_down_predictor import LimitDownPredictor

module = LimitDownPredictor()
result = module.run()  # 返回高风险股票
```

**风险等级：**
- 🔴 极高风险 (80分以上)
- 🟠 高风险 (60-80分)
- 🟡 中风险 (40-60分)

---

## 数据层API

### DataInterface (统一数据接口)

```python
from src.data.interface import get_data_interface

interface = get_data_interface()

# 获取实时行情
data = interface.get_stock_realtime('600519.SH')

# 获取历史K线
history = interface.get_stock_history('600519.SH', period='daily')

# 获取涨停板
limit_up = interface.get_limit_up(date='2026-01-29')
```

---

## 技术指标API

### TechnicalIndicators

```python
from src.services.technical_indicators import TechnicalIndicators

# RSI指标
rsi = TechnicalIndicators.rsi(close_series, period=14)

# MACD指标
macd_data = TechnicalIndicators.macd(close_series)
# 返回: {'macd': ..., 'signal': ..., 'histogram': ...}

# 布林带
bb = TechnicalIndicators.bollinger_bands(close_series)
# 返回: {'upper': ..., 'middle': ..., 'lower': ...}
```

---

## 使用示例

### 示例1：涨停预测

```python
python scripts/analyze_limit_up.py
```

### 示例2：智能选股

```python
python scripts/stock_screener.py
```

### 示例3：买入信号（指定股票）

```python
python scripts/check_buy_signal.py 600519.SH 000001.SZ
```

### 示例4：游资跟踪

```python
python scripts/track_hot_money.py
```

### 示例5：跌停预警

```python
python scripts/check_limit_down_risk.py
```

---

## 数据格式说明

### 股票代码格式

- **上海交易所**：600519.SH（贵州茅台）
- **深圳交易所**：000001.SZ（平安银行）

### 返回数据格式

所有模块返回格式化的字符串，包含：
- 表格化数据
- emoji图标标识
- 明确的评级/建议

### 错误处理

遇到错误时返回：
```
❌ 执行失败: [功能名称]
错误信息: [具体错误]
```
