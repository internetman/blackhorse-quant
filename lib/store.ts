'use client';

import { create } from 'zustand';
import type {
  Recommendation, WatchItem, Review, ReviewStats,
  PrivatePosition, DailySummary, Circle, User
} from './types';
import { api } from './api';
import {
  MOCK_RECOMMENDATIONS, MOCK_WATCHLIST, MOCK_REVIEWS,
  MOCK_REVIEW_STATS, MOCK_PRIVATE_POSITIONS, MOCK_DAILY_SUMMARY,
  MOCK_CIRCLE, MOCK_USERS
} from './mock-data';

interface RecommendationStore {
  date: string;
  summary: DailySummary;
  recommendations: Recommendation[];
  loading: boolean;
  error: string | null;
  useMock: boolean;
  fetch: (date?: string) => Promise<void>;
}

export const useRecommendationStore = create<RecommendationStore>((set) => ({
  date: new Date().toISOString().split('T')[0],
  summary: MOCK_DAILY_SUMMARY,
  recommendations: [],
  loading: false,
  error: null,
  useMock: false,

  fetch: async (date?: string) => {
    set({ loading: true, error: null });
    try {
      const data = await api.getRecommendations(date);
      set({
        date: data.date,
        summary: data.summary,
        recommendations: data.recommendations,
        loading: false,
        useMock: false,
      });
    } catch {
      set({
        recommendations: MOCK_RECOMMENDATIONS,
        summary: MOCK_DAILY_SUMMARY,
        loading: false,
        useMock: true,
        error: '使用演示数据',
      });
    }
  },
}));

interface WatchlistStore {
  items: WatchItem[];
  loading: boolean;
  error: string | null;
  fetch: () => Promise<void>;
  add: (data: { symbol: string; name: string; reason: string }) => Promise<void>;
  remove: (id: string) => Promise<void>;
}

export const useWatchlistStore = create<WatchlistStore>((set, get) => ({
  items: [],
  loading: false,
  error: null,

  fetch: async () => {
    set({ loading: true, error: null });
    try {
      const items = await api.getWatchlist();
      set({ items, loading: false });
    } catch {
      set({ items: MOCK_WATCHLIST, loading: false, error: '使用演示数据' });
    }
  },

  add: async (data) => {
    try {
      const item = await api.addWatchItem(data);
      set((s) => ({ items: [...s.items, item] }));
    } catch (e) {
      set({ error: e instanceof Error ? e.message : '添加失败' });
    }
  },

  remove: async (id) => {
    try {
      await api.removeWatchItem(id);
      set((s) => ({ items: s.items.filter((i) => i.id !== id) }));
    } catch (e) {
      set({ error: e instanceof Error ? e.message : '删除失败' });
    }
  },
}));

interface ReviewStore {
  reviews: Review[];
  stats: ReviewStats;
  loading: boolean;
  error: string | null;
  filterType: string | null;
  fetch: (type?: string) => Promise<void>;
  fetchStats: () => Promise<void>;
  setFilter: (type: string | null) => void;
}

export const useReviewStore = create<ReviewStore>((set) => ({
  reviews: [],
  stats: MOCK_REVIEW_STATS,
  loading: false,
  error: null,
  filterType: null,

  fetch: async (type?: string) => {
    set({ loading: true, error: null });
    try {
      const reviews = await api.getReviews(type);
      set({ reviews, loading: false });
    } catch {
      set({ reviews: MOCK_REVIEWS, loading: false, error: '使用演示数据' });
    }
  },

  fetchStats: async () => {
    try {
      const stats = await api.getReviewStats();
      set({ stats });
    } catch {
      set({ stats: MOCK_REVIEW_STATS });
    }
  },

  setFilter: (type) => set({ filterType: type }),
}));

interface PositionStore {
  positions: PrivatePosition[];
  loading: boolean;
  error: string | null;
  fetch: () => Promise<void>;
  update: (id: string, data: Partial<PrivatePosition>) => Promise<void>;
}

export const usePositionStore = create<PositionStore>((set) => ({
  positions: [],
  loading: false,
  error: null,

  fetch: async () => {
    set({ loading: true, error: null });
    try {
      const positions = await api.getPositions();
      set({ positions, loading: false });
    } catch {
      set({ positions: MOCK_PRIVATE_POSITIONS, loading: false, error: '使用演示数据' });
    }
  },

  update: async (id, data) => {
    try {
      const updated = await api.updatePosition(id, data);
      set((s) => ({
        positions: s.positions.map((p) => (p.id === id ? updated : p)),
      }));
    } catch (e) {
      set({ error: e instanceof Error ? e.message : '更新失败' });
    }
  },
}));

interface CircleStore {
  circle: Circle | null;
  members: User[];
  loading: boolean;
  fetch: () => Promise<void>;
  fetchMembers: () => Promise<void>;
}

export const useCircleStore = create<CircleStore>((set) => ({
  circle: MOCK_CIRCLE,
  members: [],
  loading: false,

  fetch: async () => {
    try {
      const circle = await api.getCircle();
      set({ circle });
    } catch {
      set({ circle: MOCK_CIRCLE });
    }
  },

  fetchMembers: async () => {
    set({ loading: true });
    try {
      const members = await api.getMembers();
      set({ members, loading: false });
    } catch {
      set({ members: MOCK_USERS, loading: false });
    }
  },
}));

interface AuthStore {
  user: User | null;
  setUser: (user: User | null) => void;
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
}));
