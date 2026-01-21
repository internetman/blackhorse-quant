'use client';
import { create } from 'zustand';
import { apiClient, type Position, type Trade, type ConfigParams, type Stats } from './api';

export type SysStatus = 'running' | 'paused' | 'kill';

interface AppState {
  // 系统状态
  sysStatus: SysStatus;
  setSysStatus: (status: SysStatus) => Promise<void>;
  fetchStatus: () => Promise<void>;
  
  // 持仓数据
  positions: Position[];
  setPositions: (positions: Position[]) => void;
  fetchPositions: () => Promise<void>;
  updatePosition: (id: number, updates: Partial<Position>) => Promise<void>;
  clearPositions: () => Promise<void>;
  
  // 交易记录
  trades: Trade[];
  fetchTrades: () => Promise<void>;
  addTrade: (trade: Trade) => Promise<void>;
  
  // 配置参数
  configParams: ConfigParams | null;
  fetchConfig: () => Promise<void>;
  updateConfigParams: (params: Partial<ConfigParams>) => Promise<void>;
  
  // 统计数据
  stats: Stats | null;
  fetchStats: () => Promise<void>;
  
  // 加载状态
  loading: boolean;
  error: string | null;
}

export const useStore = create<AppState>((set, get) => ({
  // 初始状态
  sysStatus: 'running',
  positions: [],
  trades: [],
  configParams: null,
  stats: null,
  loading: false,
  error: null,
  
  // 系统状态
  fetchStatus: async () => {
    try {
      const status = await apiClient.getStatus();
      set({ sysStatus: status.status });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '获取状态失败' });
    }
  },
  
  setSysStatus: async (status) => {
    try {
      await apiClient.setStatus(status);
      set({ sysStatus: status });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '设置状态失败' });
    }
  },
  
  // 持仓数据
  setPositions: (positions) => set({ positions }),
  
  fetchPositions: async () => {
    try {
      set({ loading: true });
      const positions = await apiClient.getPositions();
      set({ positions, loading: false });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '获取持仓失败',
        loading: false 
      });
    }
  },
  
  updatePosition: async (id, updates) => {
    try {
      const updated = await apiClient.updatePosition(id, updates);
      set((state) => ({
        positions: state.positions.map((pos) =>
          pos.id === id ? updated : pos
        ),
      }));
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '更新持仓失败' });
    }
  },
  
  clearPositions: async () => {
    try {
      await apiClient.clearPositions();
      set({ positions: [] });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '清空持仓失败' });
    }
  },
  
  // 交易记录
  fetchTrades: async () => {
    try {
      const trades = await apiClient.getTrades();
      set({ trades });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '获取交易记录失败' });
    }
  },
  
  addTrade: async (trade) => {
    try {
      const newTrade = await apiClient.createTrade(trade);
      set((state) => ({
        trades: [newTrade, ...state.trades].slice(0, 100),
      }));
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '创建交易记录失败' });
    }
  },
  
  // 配置参数
  fetchConfig: async () => {
    try {
      const config = await apiClient.getConfig();
      set({ configParams: config });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '获取配置失败' });
    }
  },
  
  updateConfigParams: async (params) => {
    try {
      const config = await apiClient.updateConfig(params);
      set({ configParams: config });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '更新配置失败' });
    }
  },
  
  // 统计数据
  fetchStats: async () => {
    try {
      const stats = await apiClient.getStats();
      set({ stats });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '获取统计数据失败' });
    }
  },
}));
