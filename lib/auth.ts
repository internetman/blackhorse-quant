'use client';

const USER_KEY = 'heima_user';
const TOKEN_KEY = 'heima_token';

export interface StoredUser {
  id: string;
  username: string;
  nickname: string;
  role: 'admin' | 'leader' | 'member';
  joinedAt: string;
}

export function getStoredUser(): StoredUser | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredUserAndToken(user: StoredUser, token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearStoredUser(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(TOKEN_KEY);
}

export function isAdmin(user: StoredUser | null): boolean {
  return user?.role === 'admin';
}

export function isLeader(user: StoredUser | null): boolean {
  return user?.role === 'leader' || user?.role === 'admin';
}
