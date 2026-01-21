// API 客户端
// 移除尾随斜杠，避免 URL 拼接时出现双斜杠
const getApiBaseUrl = () => {
  const url = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  return url.replace(/\/+$/, ''); // 移除所有尾随斜杠
};

const API_BASE_URL = getApiBaseUrl();

// 调试：在浏览器控制台显示当前 API 地址
if (typeof window !== 'undefined') {
  console.log('🔗 API Base URL:', API_BASE_URL);
  console.log('🔗 Environment Variable:', process.env.NEXT_PUBLIC_API_URL || '未设置（使用默认值）');
}

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
    // 移除尾随斜杠，避免 URL 拼接时出现双斜杠
    this.baseUrl = baseUrl.replace(/\/+$/, '');
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    // 确保 endpoint 以 / 开头，baseUrl 不以 / 结尾（已在构造函数中处理）
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = `${this.baseUrl}${cleanEndpoint}`;
    
    // 调试信息
    if (typeof window !== 'undefined') {
      console.log(`🌐 API Request: ${url}`);
    }
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      if (!response.ok) {
        const errorText = await response.text().catch(() => response.statusText);
        console.error(`❌ API Error [${response.status}]:`, errorText);
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      // 网络错误或 CORS 错误
      if (error instanceof TypeError) {
        const errorMsg = error.message.includes('fetch') 
          ? `无法连接到后端服务 (${this.baseUrl})。请检查：1) 后端是否已部署 2) NEXT_PUBLIC_API_URL 环境变量是否正确设置 3) Vercel 是否已重新部署`
          : error.message;
        console.error('❌ Network Error:', error);
        throw new Error(errorMsg);
      }
      console.error('❌ Request Error:', error);
      throw error;
    }
  }

  // 持仓相关
  async getPositions(): Promise<Position[]> {
    return this.request<Position[]>('/api/positions/');
  }

  async updatePosition(id: number, updates: Partial<Position>): Promise<Position> {
    return this.request<Position>(`/api/positions/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async clearPositions(): Promise<void> {
    return this.request<void>('/api/positions/', {
      method: 'DELETE',
    });
  }

  // 交易记录
  async getTrades(limit: number = 100): Promise<Trade[]> {
    return this.request<Trade[]>(`/api/trades/?limit=${limit}`);
  }

  async createTrade(trade: Trade): Promise<Trade> {
    return this.request<Trade>('/api/trades/', {
      method: 'POST',
      body: JSON.stringify(trade),
    });
  }

  // 系统状态
  async getStatus(): Promise<SysStatus> {
    return this.request<SysStatus>('/api/status/');
  }

  async setStatus(status: 'running' | 'paused' | 'kill'): Promise<SysStatus> {
    return this.request<SysStatus>('/api/status/', {
      method: 'POST',
      body: JSON.stringify({ status }),
    });
  }

  // 统计数据
  async getStats(): Promise<Stats> {
    return this.request<Stats>('/api/stats/');
  }

  // 配置参数
  async getConfig(): Promise<ConfigParams> {
    return this.request<ConfigParams>('/api/config/');
  }

  async updateConfig(config: Partial<ConfigParams>): Promise<ConfigParams> {
    return this.request<ConfigParams>('/api/config/', {
      method: 'PATCH',
      body: JSON.stringify(config),
    });
  }
}

export const apiClient = new ApiClient();
