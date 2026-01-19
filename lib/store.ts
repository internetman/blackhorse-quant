'use client';
import { create } from 'zustand';
import { MOCK_POSITIONS, MOCK_TRADES, type Position, type Trade } from './mock';

export type SysStatus = 'running' | 'paused' | 'kill';

interface ConfigParams {
  strategyName: string;
  maxPositions: number;
  maxDrawdown: number;
  // 可以扩展更多配置参数
}

interface AppState {
  // 系统状态
  sysStatus: SysStatus;
  setSysStatus: (status: SysStatus) => void;
  
  // 持仓数据
  positions: Position[];
  setPositions: (positions: Position[]) => void;
  updatePosition: (id: number, updates: Partial<Position>) => void;
  
  // 交易记录
  trades: Trade[];
  addTrade: (trade: Trade) => void;
  
  // 配置参数
  configParams: ConfigParams;
  updateConfigParams: (params: Partial<ConfigParams>) => void;
  
  // 统计数据
  totalPnl: number;
  setTotalPnl: (pnl: number) => void;
  
  // 今日盈亏
  todayPnl: number;
  setTodayPnl: (pnl: number) => void;
}

export const useStore = create<AppState>((set) => ({
  // 初始状态
  sysStatus: 'running',
  positions: [...MOCK_POSITIONS],
  trades: [...MOCK_TRADES],
  totalPnl: 12402,
  todayPnl: 58240.42,
  configParams: {
    strategyName: 'A股波动率均衡对冲策略',
    maxPositions: 30,
    maxDrawdown: 2.5,
  },
  
  // Actions
  setSysStatus: (status) => set({ sysStatus: status }),
  
  setPositions: (positions) => set({ positions }),
  
  updatePosition: (id, updates) => set((state) => ({
    positions: state.positions.map((pos) =>
      pos.id === id ? { ...pos, ...updates } : pos
    ),
  })),
  
  addTrade: (trade) => set((state) => ({
    trades: [trade, ...state.trades].slice(0, 100), // 最多保留100条
  })),
  
  updateConfigParams: (params) => set((state) => ({
    configParams: { ...state.configParams, ...params },
  })),
  
  setTotalPnl: (pnl) => set({ totalPnl: pnl }),
  
  setTodayPnl: (pnl) => set({ todayPnl: pnl }),
}));
