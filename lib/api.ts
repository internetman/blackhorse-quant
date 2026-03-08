const getApiBaseUrl = (): string => {
  const url = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  return url.replace(/\/+$/, '');
};

const API_BASE = getApiBaseUrl();

if (typeof window !== 'undefined') {
  console.log('🔗 API Base URL:', API_BASE);
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
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
  PrivatePosition, Circle, User
} from './types';

export const api = {
  health: () => request<{ status: string }>('/health'),

  getRecommendations: (date?: string) =>
    request<RecommendationsResponse>(date ? `/api/recommendations/?date=${date}` : '/api/recommendations/'),

  getWatchlist: () => request<WatchItem[]>('/api/watchlist/'),

  addWatchItem: (data: { symbol: string; name: string; reason: string }) =>
    request<WatchItem>('/api/watchlist/', { method: 'POST', body: JSON.stringify(data) }),

  removeWatchItem: (id: string) =>
    request<void>(`/api/watchlist/${id}`, { method: 'DELETE' }),

  getReviews: (type?: string) =>
    request<Review[]>(type ? `/api/reviews/?type=${type}` : '/api/reviews/'),

  getReviewStats: () => request<ReviewStats>('/api/reviews/stats/'),

  getPositions: () => request<PrivatePosition[]>('/api/positions/'),

  updatePosition: (id: string, data: Partial<PrivatePosition>) =>
    request<PrivatePosition>(`/api/positions/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  getCircle: () => request<Circle>('/api/circle/'),

  getMembers: () => request<User[]>('/api/admin/members/'),

  updateMemberRole: (userId: string, role: string) =>
    request<User>(`/api/admin/members/${userId}`, { method: 'PATCH', body: JSON.stringify({ role }) }),

  joinCircle: (data: { inviteCode: string; nickname: string }) =>
    request<{ user: User; circle: Circle }>('/api/auth/join/', { method: 'POST', body: JSON.stringify(data) }),

  getMe: () => request<User>('/api/auth/me/'),
};
