from pydantic import BaseModel
from typing import Literal, Optional

# 持仓模型
class Position(BaseModel):
    id: int
    asset: str
    side: Literal['多', '空']
    amount: str
    entryPrice: str
    currentPrice: str
    pnl: str
    pnlValue: str

# 交易记录模型
class Trade(BaseModel):
    id: int
    time: str
    asset: str
    side: str
    price: str
    status: str
    reason: Optional[str] = None

# 系统状态模型
class SysStatus(BaseModel):
    status: Literal['running', 'paused', 'kill']

# 统计数据模型
class Stats(BaseModel):
    totalPnl: float
    todayPnl: float
    positionCount: int
    capitalUsage: float

# 配置参数模型
class ConfigParams(BaseModel):
    strategyName: str
    maxPositions: int
    maxDrawdown: float
