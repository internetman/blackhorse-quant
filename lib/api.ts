// API 客户端
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Position {
  id: number;
  asset: string;
  side: '多' | '空';
  amount: string;
  entryPrice: string;
  currentPrice: string;
  pnl: string;
  pnlValue: string;
}

export interface Trade {
  id: number;
  time: string;
  asset: string;
  side: string;
  price: string;
  status: string;
  reason?: string;
}

export interface SysStatus {
  status: 'running' | 'paused' | 'kill';
}

export interface Stats {
  totalPnl: number;
  todayPnl: number;
  positionCount: number;
  capitalUsage: number;
}

export interface ConfigParams {
  strategyName: string;
  maxPositions: number;
  maxDrawdown: number;
}

// API 客户端类
class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      // 网络错误或 CORS 错误
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error(`无法连接到后端服务 (${this.baseUrl})。请检查后端是否已部署并配置了 NEXT_PUBLIC_API_URL 环境变量。`);
      }
      throw error;
    }
  }

  // 持仓相关
  async getPositions(): Promise<Position[]> {
    return this.request<Position[]>('/api/positions');
  }

  async updatePosition(id: number, updates: Partial<Position>): Promise<Position> {
    return this.request<Position>(`/api/positions/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async clearPositions(): Promise<void> {
    return this.request<void>('/api/positions', {
      method: 'DELETE',
    });
  }

  // 交易记录
  async getTrades(limit: number = 100): Promise<Trade[]> {
    return this.request<Trade[]>(`/api/trades?limit=${limit}`);
  }

  async createTrade(trade: Trade): Promise<Trade> {
    return this.request<Trade>('/api/trades', {
      method: 'POST',
      body: JSON.stringify(trade),
    });
  }

  // 系统状态
  async getStatus(): Promise<SysStatus> {
    return this.request<SysStatus>('/api/status');
  }

  async setStatus(status: 'running' | 'paused' | 'kill'): Promise<SysStatus> {
    return this.request<SysStatus>('/api/status', {
      method: 'POST',
      body: JSON.stringify({ status }),
    });
  }

  // 统计数据
  async getStats(): Promise<Stats> {
    return this.request<Stats>('/api/stats');
  }

  // 配置参数
  async getConfig(): Promise<ConfigParams> {
    return this.request<ConfigParams>('/api/config');
  }

  async updateConfig(config: Partial<ConfigParams>): Promise<ConfigParams> {
    return this.request<ConfigParams>('/api/config', {
      method: 'PATCH',
      body: JSON.stringify(config),
    });
  }
}

export const apiClient = new ApiClient();
