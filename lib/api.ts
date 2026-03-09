import { getStoredToken } from './auth';

const getApiBaseUrl = (): string => {
  const url = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  return url.replace(/\/+$/, '');
};

const API_BASE = getApiBaseUrl();

if (typeof window !== 'undefined') {
  console.log('API Base URL:', API_BASE);
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const token = getStoredToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        ...headers,
        ...options?.headers,
      },
    });

    if (!res.ok) {
      const text = await res.text().catch(() => res.statusText);
      throw new Error(`API ${res.status}: ${text}`);
    }

    return res.json();
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(`无法连接后端 (${API_BASE})，请检查 NEXT_PUBLIC_API_URL`);
    }
    throw error;
  }
}

import type {
  RecommendationsResponse, WatchItem, Review, ReviewStats,
  StockSearchItem, User
} from './types';

export const api = {
  health: () => request<{ status: string }>('/health'),

  login: (username: string, password: string) =>
    request<{ user: User; token: string }>('/api/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),

  logout: () =>
    request<{ message: string }>('/api/auth/logout/', { method: 'POST' }),

  getMe: () => request<User>('/api/auth/me/'),

  getRecommendations: (date?: string) =>
    request<RecommendationsResponse>(date ? `/api/recommendations/?date=${date}` : '/api/recommendations/'),

  getWatchlist: () => request<WatchItem[]>('/api/watchlist/'),

  addWatchItem: (data: { symbol: string; name?: string; reason?: string }) =>
    request<WatchItem>('/api/watchlist/', { method: 'POST', body: JSON.stringify(data) }),

  removeWatchItem: (symbol: string) =>
    request<{ message: string }>(`/api/watchlist/${encodeURIComponent(symbol)}`, { method: 'DELETE' }),

  searchStocks: (q: string, limit = 20) =>
    request<StockSearchItem[]>(`/api/stocks/search?q=${encodeURIComponent(q)}&limit=${limit}`),

  getQuote: (symbol: string) =>
    request<{ symbol: string; latestPrice: number; changePercent: number; volume: number; updatedAt: string }>(`/api/quote/?symbol=${encodeURIComponent(symbol)}`),

  getNews: (symbol: string, limit = 10) =>
    request<unknown[]>(`/api/news/?symbol=${encodeURIComponent(symbol)}&limit=${limit}`),

  getReviews: (type?: string) =>
    request<Review[]>(type ? `/api/reviews/?type=${type}` : '/api/reviews/'),

  getReviewStats: () => request<ReviewStats>('/api/reviews/stats/'),

  getMembers: () => request<User[]>('/api/admin/members/'),

  createUser: (data: { username: string; password: string; nickname: string; role: string }) =>
    request<User>('/api/admin/users/', { method: 'POST', body: JSON.stringify(data) }),

  updateMemberRole: (userId: string, role: string) =>
    request<User>(`/api/admin/members/${userId}`, { method: 'PATCH', body: JSON.stringify({ role }) }),
};
