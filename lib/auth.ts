'use client';

const STORAGE_KEY = 'heima_user';

export interface StoredUser {
  id: string;
  nickname: string;
  role: 'admin' | 'leader' | 'member';
  joinedAt: string;
}

export function getStoredUser(): StoredUser | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setStoredUser(user: StoredUser): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
}

export function clearStoredUser(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(STORAGE_KEY);
}

export function isAdmin(user: StoredUser | null): boolean {
  return user?.role === 'admin';
}

export function isLeader(user: StoredUser | null): boolean {
  return user?.role === 'leader' || user?.role === 'admin';
}
