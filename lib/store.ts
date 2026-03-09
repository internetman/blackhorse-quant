'use client';

import { create } from 'zustand';
import type {
  Recommendation, WatchItem, Review, ReviewStats,
  DailySummary, User
} from './types';
import { api } from './api';
import {
  MOCK_RECOMMENDATIONS, MOCK_WATCHLIST, MOCK_REVIEWS,
  MOCK_REVIEW_STATS, MOCK_DAILY_SUMMARY, MOCK_USERS
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
  remove: (symbol: string) => Promise<void>;
}

export const useWatchlistStore = create<WatchlistStore>((set) => ({
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

  remove: async (symbol) => {
    try {
      await api.removeWatchItem(symbol);
      set((s) => ({ items: s.items.filter((i) => i.symbol !== symbol) }));
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

interface AdminStore {
  members: User[];
  loading: boolean;
  fetchMembers: () => Promise<void>;
}

export const useAdminStore = create<AdminStore>((set) => ({
  members: [],
  loading: false,

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
