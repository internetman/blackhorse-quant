# Mock 数据
from app.models import Position, Trade, Stats, ConfigParams

# 初始持仓数据
INITIAL_POSITIONS: list[Position] = [
    Position(
        id=1,
        asset='贵州茅台 (600519)',
        side='多',
        amount='200',
        entryPrice='1,650.00',
        currentPrice='1,682.50',
        pnl='+1.97%',
        pnlValue='+¥6,500'
    ),
    Position(
        id=2,
        asset='宁德时代 (300750)',
        side='多',
        amount='1500',
        entryPrice='158.20',
        currentPrice='162.10',
        pnl='+2.46%',
        pnlValue='+¥5,850'
    ),
    Position(
        id=3,
        asset='隆基绿能 (601012)',
        side='多',
        amount='2000',
        entryPrice='22.50',
        currentPrice='20.10',
        pnl='-10.67%',
        pnlValue='-¥4,800'
    ),
    Position(
        id=4,
        asset='比亚迪 (002594)',
        side='空',
        amount='800',
        entryPrice='210.50',
        currentPrice='205.80',
        pnl='+2.23%',
        pnlValue='+¥3,760'
    ),
]

# 初始交易记录
INITIAL_TRADES: list[Trade] = [
    Trade(
        id=101,
        time='14:20:01',
        asset='招商银行 (600036)',
        side='买入',
        price='32.50',
        status='正常成交',
        reason='均线金叉信号触发'
    ),
    Trade(
        id=102,
        time='13:45:12',
        asset='中国平安 (601318)',
        side='卖出',
        price='41.80',
        status='风控拒绝',
        reason='RSI 超买信号'
    )
]

# 初始统计数据
INITIAL_STATS = Stats(
    totalPnl=12402.0,
    todayPnl=58240.42,
    positionCount=4,
    capitalUsage=65.4
)

# 初始配置参数
INITIAL_CONFIG = ConfigParams(
    strategyName='A股波动率均衡对冲策略',
    maxPositions=30,
    maxDrawdown=2.5
)
