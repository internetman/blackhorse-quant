'use client';

import { useState, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import {
  Sparkles, List, BarChart3, Lock, Settings,
  Menu, X, ChevronRight
} from 'lucide-react';
import { getStoredUser, isAdmin, type StoredUser } from '@/lib/auth';
import { useCircleStore } from '@/lib/store';

const NAV_ITEMS = [
  { href: '/recommendations', label: '每日建议', icon: Sparkles, description: 'AI 每日荐股' },
  { href: '/watchlist', label: '自选股池', icon: List, description: '圈子关注的股票' },
  { href: '/reviews', label: '复盘记录', icon: BarChart3, description: '建议效果验证' },
  { href: '/positions', label: '我的持仓', icon: Lock, description: '私有持仓记录' },
];

const ADMIN_ITEM = {
  href: '/admin', label: '圈子管理', icon: Settings, description: '成员与邀请管理'
};

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [user, setUser] = useState<StoredUser | null>(null);
  const circle = useCircleStore((s) => s.circle);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    setUser(getStoredUser());
  }, []);

  const navItems = isAdmin(user)
    ? [...NAV_ITEMS, ADMIN_ITEM]
    : NAV_ITEMS;

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex flex-col w-60 bg-sidebar text-sidebar-text shrink-0">
        {/* Brand */}
        <div className="p-6 pb-2">
          <h1 className="text-xl font-bold text-white tracking-wide">
            <span className="text-amber-400">黑马</span>自选
          </h1>
          <p className="text-xs text-stone-400 mt-1">
            {circle?.name || '我的黑马圈'} · {circle?.memberCount || 0}人
          </p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + '/');
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`
                  flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all duration-200
                  ${active
                    ? 'bg-white/10 text-white font-medium'
                    : 'text-stone-400 hover:bg-white/5 hover:text-stone-200'
                  }
                `}
              >
                <Icon size={18} strokeWidth={active ? 2 : 1.5} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* User info */}
        <div className="p-4 border-t border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-amber-700/30 flex items-center justify-center text-amber-400 text-sm font-medium">
              {user?.nickname?.charAt(0) || '?'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-white truncate">{user?.nickname || '未登录'}</p>
              <p className="text-xs text-stone-500 capitalize">{user?.role || ''}</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile header */}
        <header className="lg:hidden flex items-center justify-between px-4 h-14 bg-white border-b border-stone-200 shrink-0">
          <div>
            <h1 className="text-base font-bold text-stone-900">
              <span className="text-amber-700">黑马</span>自选
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-stone-400">
              {circle?.name || '黑马圈'}
            </span>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg hover:bg-stone-100 transition-colors"
            >
              {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </header>

        {/* Mobile slide menu */}
        {mobileMenuOpen && (
          <div className="lg:hidden fixed inset-0 z-50 flex">
            <div
              className="absolute inset-0 bg-black/30"
              onClick={() => setMobileMenuOpen(false)}
            />
            <div className="relative ml-auto w-64 bg-white h-full shadow-2xl animate-card-in">
              <div className="p-4 border-b border-stone-100">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-amber-50 flex items-center justify-center text-amber-700 font-medium">
                    {user?.nickname?.charAt(0) || '?'}
                  </div>
                  <div>
                    <p className="font-medium text-stone-900">{user?.nickname || '未登录'}</p>
                    <p className="text-xs text-stone-400 capitalize">{user?.role || ''}</p>
                  </div>
                </div>
              </div>
              <nav className="p-2 space-y-0.5">
                {navItems.map((item) => {
                  const active = pathname === item.href || pathname.startsWith(item.href + '/');
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`
                        flex items-center justify-between px-3 py-3 rounded-xl text-sm transition-colors
                        ${active
                          ? 'bg-stone-100 text-stone-900 font-medium'
                          : 'text-stone-600 hover:bg-stone-50'
                        }
                      `}
                    >
                      <div className="flex items-center gap-3">
                        <Icon size={18} />
                        <div>
                          <span>{item.label}</span>
                          <p className="text-xs text-stone-400">{item.description}</p>
                        </div>
                      </div>
                      <ChevronRight size={14} className="text-stone-300" />
                    </Link>
                  );
                })}
              </nav>
            </div>
          </div>
        )}

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>

        {/* Mobile bottom tab bar */}
        <nav className="lg:hidden flex items-center justify-around h-16 bg-white/80 backdrop-blur-xl border-t border-stone-200 shrink-0 pb-safe">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + '/');
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`
                  flex flex-col items-center gap-0.5 py-1 px-3 rounded-lg transition-colors
                  ${active ? 'text-amber-700' : 'text-stone-400'}
                `}
              >
                <Icon size={20} strokeWidth={active ? 2 : 1.5} />
                <span className="text-[10px] font-medium">{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
