# A股武器库 - 开发文档

**项目：** Stock Arsenal
**版本：** v1.0 Prototype
**开发周期：** 2026-01-29
**开发模式：** 原型验证

---

## 📋 目录

1. [开发概述](#开发概述)
2. [技术栈](#技术栈)
3. [架构设计](#架构设计)
4. [数据流设计](#数据流设计)
5. [模块说明](#模块说明)
6. [API文档](#api文档)
7. [扩展指南](#扩展指南)
8. [性能优化](#性能优化)

---

## 🎯 开发概述

### 开发目标

**核心目标：** 验证"将GitHub开源项目封装成Skill"的可行性

**具体目标：**
1. ✅ 实现三大数据源集成（akshare/efinance/baostock）
2. ✅ 实现5个核心功能（涨停预测/选股/游资/买入/跌停）
3. ✅ 验证模块化架构可扩展性
4. ✅ 提供用户友好的交互界面

### 开发原则

- **YAGNI** - You Aren't Gonna Need It（不做不需要的功能）
- **KISS** - Keep It Simple, Stupid（保持简单）
- **DRY** - Don't Repeat Yourself（不要重复代码）
- **模块化** - 每个功能独立模块

### 开发时间线

| 阶段 | 任务 | 时间 |
|-----|------|------|
| Phase 1 | 基础框架搭建 | 1小时 |
| Phase 2 | 数据层开发 | 2小时 |
| Phase 3 | 核心算法 | 1小时 |
| Phase 4 | 5个功能模块 | 3小时 |
| Phase 5 | 交互层开发 | 1小时 |
| **总计** | | **8小时** |

---

## 🛠️ 技术栈

### 核心依赖

```yaml
数据源:
  - akshare: 1.12.0          # 金融数据接口
  - efinance: 0.5.6          # 东方财富数据
  - baostock: 0.8.8          # 证券数据

数据处理:
  - pandas: 2.1.0            # 数据分析
  - numpy: 1.24.0            # 数值计算

界面:
  - rich: 13.7.0             # 终端美化

配置:
  - pyyaml: 6.0.1            # YAML配置

日志:
  - loguru: 0.7.2            # 日志管理

技术指标（可选）:
  - talib-binary: 0.4.28     # 技术指标库
```

### 开发工具

```yaml
IDE: VS Code / PyCharm
版本控制: Git
Python版本: 3.8+
```

---

## 🏗️ 架构设计

### 三层架构

```
┌─────────────────────────────────────────┐
│           Presentation Layer            │
│   (UI层 - 交互界面)                      │
│                                         │
│   - MainMenu (主菜单)                   │
│   - TableRenderer (表格渲染)            │
│   - ConfigMenu (配置菜单)               │
└─────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│          Business Logic Layer           │
│   (业务层 - 功能实现)                    │
│                                         │
│   - BaseModule (模块基类)               │
│   - TechnicalIndicators (技术指标)      │
│   - 5个核心功能模块                     │
└─────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│            Data Access Layer            │
│   (数据层 - 数据获取)                    │
│                                         │
│   - DataInterface (统一接口)            │
│   - 3个数据源适配器                     │
│   - CacheManager (缓存)                 │
│   - Storage (存储)                      │
└─────────────────────────────────────────┘
```

### 设计模式

**1. 单例模式（Singleton）**
```python
# 数据接口单例
_data_interface = None

def get_data_interface() -> DataInterface:
    global _data_interface
    if _data_interface is None:
        _data_interface = DataInterface()
    return _data_interface
```

**2. 适配器模式（Adapter）**
```python
# 统一接口，不同实现
class DataInterface:
    def get_stock_realtime(self, symbol):
        # 自动路由到最优数据源
        pass

class EFinanceAdapter:
    def get_realtime(self, symbol):
        # efinance实现
        pass
```

**3. 策略模式（Strategy）**
```python
# 不同功能模块统一接口
class BaseModule:
    def get_data(self): pass
    def analyze(self, data): pass
    def format_output(self, data): pass
```

**4. 工厂模式（Factory）**
```python
# 根据配置创建对应功能模块
modules = {
    '1': LimitUpPredictor(),
    '2': StockScreener(),
    ...
}
```

---

## 🔄 数据流设计

### 数据获取流程

```
用户请求
   ↓
MainMenu.execute_module()
   ↓
Module.run()
   ↓
Module.get_data()
   ↓
DataInterface.get_xxx()
   ↓
智能路由：选择数据源
   ↓
Adapter.get_xxx()
   ↓
检查缓存
   ↓ ├─ 命中 → 返回缓存数据
   ↓
   └─ 未命中 → 调用API
                   ↓
               存入缓存
                   ↓
               返回数据
```

### 错误处理流程

```
数据源调用
   ↓
异常捕获
   ↓
   ├─ 网络错误 → 切换备用数据源
   ├─ 数据不存在 → 返回空数据
   ├─ 停牌/退市 → 返回友好提示
   └─ 其他错误 → 记录日志 + 返回错误信息
```

### 缓存策略

```python
# 缓存键生成
key = md5(f"{func_name}_{args}_{kwargs}")

# 缓存层级
L1: 内存缓存（当前会话）
L2: SQLite存储（历史数据）

# TTL设置
实时数据（行情）: 5分钟
日级数据（财务）: 1天
历史数据（K线）: 永久
```

---

## 📦 模块说明

### 数据层模块

#### 1. DataInterface（统一接口）

**职责：**
- 智能路由到最优数据源
- 自动降级和容错
- 统一数据格式

**核心方法：**
```python
get_stock_realtime(symbol)      # 实时行情
get_stock_history(symbol)        # 历史K线
get_stock_list()                 # 股票列表
get_hot_money(date)              # 龙虎榜
get_limit_up(date)               # 涨停板
get_limit_down(date)             # 跌停板
```

#### 2. 适配器（Adapters）

**EFinanceAdapter**
- 优势：官方数据，实时性好
- 适用：实时行情、涨停跌停

**AkshareAdapter**
- 优势：数据最全
- 适用：财务数据、龙虎榜

**BaostockAdapter**
- 优势：复权准确
- 适用：历史K线

#### 3. CacheManager（缓存管理）

**功能：**
- 内存缓存管理
- TTL过期清理
- 缓存键生成

#### 4. Storage（存储管理）

**功能：**
- SQLite数据库操作
- 历史数据存储
- 游资数据统计

---

### 业务层模块

#### 1. BaseModule（模块基类）

**所有功能模块的基类**

```python
class BaseModule(ABC):
    @abstractmethod
    def get_data(self): pass

    @abstractmethod
    def analyze(self, data): pass

    @abstractmethod
    def format_output(self, data): pass

    def run(self):
        # 模板方法
        data = self.get_data()
        result = self.analyze(data)
        return self.format_output(result)
```

#### 2. TechnicalIndicators（技术指标）

**实现指标：**
- SMA/EMA（移动平均）
- RSI（相对强弱）
- MACD（指数平滑）
- Bollinger Bands（布林带）
- ATR（真实波幅）
- Volume Ratio（量比）

#### 3. 5个核心功能模块

**LimitUpPredictor（涨停预测）**
- 评分体系：涨幅+量比+换手+封单+技术面
- 输出：Top20强势股

**StockScreener（智能选股）**
- 多条件筛选：PE/PB/RSI/涨跌
- 输出：符合条件的股票列表

**HotMoneyTracker（游资跟踪）**
- 统计知名游资席位
- 输出：净买入排名

**BuySignal（买入信号）**
- 综合分析：RSI+MACD+量比+均线
- 输出：买入建议

**LimitDownPredictor（跌停预警）**
- 风险评估：跌幅+量比+技术+质押
- 输出：风险等级

---

### 交互层模块

#### 1. MainMenu（主菜单）

**功能：**
- Rich美化菜单
- 用户输入处理
- 模块调度

#### 2. TableRenderer（表格渲染）

**功能：**
- 彩色表格显示
- 数据分页
- 格式化输出

---

## 📖 API文档

### DataInterface API

```python
# 获取实时行情
data_interface.get_stock_realtime(symbol: str) -> Dict

# 返回格式
{
    'symbol': '600519.SH',
    'name': '贵州茅台',
    'price': 1800.5,
    'change': 0.025,
    'volume': 1234567,
    'amount': 1234567890,
    'timestamp': '2026-01-29 15:00:00'
}

# 获取历史K线
data_interface.get_stock_history(
    symbol: str,
    period: str = 'daily'
) -> pd.DataFrame

# period: 'daily', 'weekly', 'monthly'

# 获取涨停板
data_interface.get_limit_up(date: str = None) -> pd.DataFrame
```

### TechnicalIndicators API

```python
# RSI指标
TechnicalIndicators.rsi(
    close: pd.Series,
    period: int = 14
) -> pd.Series

# MACD指标
TechnicalIndicators.macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Dict

# 返回格式
{
    'macd': pd.Series,
    'signal': pd.Series,
    'histogram': pd.Series
}
```

### 模块扩展API

```python
# 创建新功能模块
class MyCustomModule(BaseModule):
    def __init__(self):
        super().__init__("我的功能")

    def get_data(self):
        # 获取数据
        pass

    def analyze(self, data):
        # 分析处理
        pass

    def format_output(self, data):
        # 格式化输出
        pass
```

---

## 🔧 扩展指南

### 添加新功能模块

**Step 1: 创建模块文件**

```bash
touch src/services/my_new_module.py
```

**Step 2: 继承BaseModule**

```python
from .base_module import BaseModule
import pandas as pd

class MyNewModule(BaseModule):
    def __init__(self):
        super().__init__("新功能名称")

    def get_data(self):
        # 获取数据逻辑
        return pd.DataFrame()

    def analyze(self, data):
        # 分析逻辑
        return data

    def format_output(self, data):
        # 格式化输出
        return "结果字符串"
```

**Step 3: 注册到菜单**

```python
# src/ui/main_menu.py
self.modules = {
    '1': LimitUpPredictor(),
    ...
    '6': MyNewModule(),  # 新增
}
```

**Step 4: 更新菜单显示**

```python
self.menu_items = {
    ...
    '6': ('🆕', '新功能', '功能描述')
}
```

### 添加新技术指标

```python
# src/services/technical_indicators.py

@staticmethod
def my_indicator(series: pd.Series, period: int = 20) -> pd.Series:
    """
    自定义指标
    """
    # 计算逻辑
    return result
```

### 添加新数据源

```python
# src/data/my_adapter.py

class MyAdapter:
    def __init__(self):
        pass

    def get_realtime(self, symbol):
        # 实现逻辑
        pass

# 注册到DataInterface
self._adapters[DataSource.MYSOURCE] = MyAdapter()
```

---

## ⚡ 性能优化

### 已实施优化

**1. 缓存机制**
- 实时数据5分钟缓存
- 避免重复API调用

**2. 懒加载**
- 按需加载数据源
- 减少启动时间

**3. 批量处理**
- 向量化操作（pandas）
- 减少循环

### 待优化项

**1. 并发请求**
```python
# 使用asyncio加速
import asyncio

async def fetch_multiple_stocks(symbols):
    tasks = [fetch_stock(s) for s in symbols]
    return await asyncio.gather(*tasks)
```

**2. 数据库优化**
```python
# 添加索引
CREATE INDEX idx_symbol_date ON stock_daily(symbol, date);

# 使用连接池
from sqlalchemy.pool import QueuePool
```

**3. 增量更新**
```python
# 只更新新数据
def update_daily(symbol):
    last_date = get_last_update_date(symbol)
    new_data = fetch_since(symbol, last_date)
    append_to_db(new_data)
```

---

## 📊 性能基准

### 当前性能

| 操作 | 响应时间 | 数据量 |
|-----|---------|--------|
| 获取实时行情 | <1s | 单只 |
| 涨停预测 | 5-10s | Top20 |
| 智能选股 | 10-30s | 100只样本 |
| 游资跟踪 | 3-5s | 5日数据 |
| 买入信号 | 5-10s | 50只样本 |

### 性能目标

| 操作 | 目标时间 |
|-----|---------|
| 实时行情 | <0.5s |
| 涨停预测 | <3s |
| 智能选股 | <10s |
| 游资跟踪 | <2s |
| 买入信号 | <5s |

---

## 🧪 测试指南

### 单元测试

```python
# tests/test_technical_indicators.py
import pytest
from src.services.technical_indicators import TechnicalIndicators

def test_rsi():
    import pandas as pd
    data = pd.Series([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])
    rsi = TechnicalIndicators.rsi(data)
    assert 0 <= rsi.iloc[-1] <= 100
```

### 集成测试

```python
# tests/test_integration.py
def test_limit_up_predictor():
    from src.services.limit_up_predictor import LimitUpPredictor
    module = LimitUpPredictor()
    result = module.run()
    assert "涨停板预测" in result
```

### 手动测试

```bash
# 测试单个功能
python -m src.services.limit_up_predictor

# 测试完整流程
python src/main.py
```

---

## 📝 代码规范

### Python代码风格

```python
# 1. 遵循PEP 8
# 2. 使用类型提示
def get_data(symbol: str) -> Dict[str, Any]:
    pass

# 3. 添加文档字符串
def analyze(self, data: pd.DataFrame) -> pd.DataFrame:
    """
    分析数据

    Args:
        data: 输入数据

    Returns:
        分析结果
    """
    pass

# 4. 使用常量
MAX_PE = 50
MIN_MARKET_CAP = 20
```

### Git提交规范

```bash
# 格式
git commit -m "type: description"

# type类型
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试
chore: 构建/工具

# 示例
git commit -m "feat: 添加跌停板预警功能"
git commit -m "fix: 修复efinance适配器编码问题"
```

---

## 🚀 部署指南

### 本地部署

```bash
# 克隆项目
git clone <repo-url>
cd stock-arsenal

# 安装依赖
pip install -r requirements.txt

# 运行
python src/main.py
```

### Docker部署

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "src/main.py"]
```

```bash
# 构建镜像
docker build -t stock-arsenal .

# 运行容器
docker run -it stock-arsenal
```

### 打包发布

```bash
# 构建
python setup.py sdist bdist_wheel

# 上传到PyPI
twine upload dist/*
```

---

## 📚 参考资料

### 开源项目

- [akshare](https://github.com/akfamily/akshare) - 金融数据接口
- [efinance](https://github.com/efinancea/efinance) - 东方财富数据
- [baostock](https://github.com/baostock/baostock) - 证券数据
- [rich](https://github.com/Textualize/rich) - 终端美化

### 技术文档

- [Python官方文档](https://docs.python.org/)
- [Pandas文档](https://pandas.pydata.org/docs/)
- [技术指标说明](https://www.investopedia.com/)

### 股票知识

- [道氏理论](https://www.investopedia.com/terms/d/dowtheory.asp)
- [波浪理论](https://www.investopedia.com/terms/e/elliotwavetheory.asp)
- [K线图](https://www.investopedia.com/terms/c/candlestick.asp)

---

## 🎓 学习资源

### Python进阶

- 设计模式
- 算法与数据结构
- 异步编程

### 量化交易

- 技术分析基础
- 量化策略开发
- 回测系统

### 项目管理

- 敏捷开发
- 代码审查
- 持续集成

---

**版本：** v1.0
**最后更新：** 2026-01-29
**维护者：** Stock Arsenal Team
