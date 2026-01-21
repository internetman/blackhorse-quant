# 内存存储（模拟数据库）
from app.models import Position, Trade, Stats, ConfigParams
from app.mock_data import INITIAL_POSITIONS, INITIAL_TRADES, INITIAL_STATS, INITIAL_CONFIG
from typing import Literal

# 全局状态存储
class Store:
    def __init__(self):
        self.positions: list[Position] = INITIAL_POSITIONS.copy()
        self.trades: list[Trade] = INITIAL_TRADES.copy()
        self.stats: Stats = INITIAL_STATS
        self.config: ConfigParams = INITIAL_CONFIG
        self.sys_status: Literal['running', 'paused', 'kill'] = 'running'
    
    def get_positions(self) -> list[Position]:
        return self.positions
    
    def update_position(self, position_id: int, updates: dict) -> Position | None:
        for i, pos in enumerate(self.positions):
            if pos.id == position_id:
                updated = pos.model_copy(update=updates)
                self.positions[i] = updated
                return updated
        return None
    
    def set_positions(self, positions: list[Position]):
        self.positions = positions
    
    def get_trades(self, limit: int = 100) -> list[Trade]:
        return self.trades[:limit]
    
    def add_trade(self, trade: Trade):
        self.trades.insert(0, trade)
        # 最多保留100条
        if len(self.trades) > 100:
            self.trades = self.trades[:100]
    
    def get_stats(self) -> Stats:
        return self.stats
    
    def update_stats(self, **kwargs):
        self.stats = self.stats.model_copy(update=kwargs)
    
    def get_config(self) -> ConfigParams:
        return self.config
    
    def update_config(self, **kwargs):
        self.config = self.config.model_copy(update=kwargs)
    
    def get_status(self) -> Literal['running', 'paused', 'kill']:
        return self.sys_status
    
    def set_status(self, status: Literal['running', 'paused', 'kill']):
        self.sys_status = status

# 全局单例
store = Store()
