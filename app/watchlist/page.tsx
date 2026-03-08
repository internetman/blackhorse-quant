'use client';

import { useEffect, useState } from 'react';
import { List, Plus, Trash2, X, Star } from 'lucide-react';
import AppShell from '@/components/layout/AppShell';
import LeaderBadge from '@/components/stock/LeaderBadge';
import { useWatchlistStore } from '@/lib/store';

export default function WatchlistPage() {
  const { items, loading, fetch, add, remove } = useWatchlistStore();
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ symbol: '', name: '', reason: '' });

  useEffect(() => { fetch(); }, [fetch]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.symbol || !form.name) return;
    await add(form);
    setForm({ symbol: '', name: '', reason: '' });
    setShowAdd(false);
  };

  return (
    <AppShell>
      <div className="p-4 md:p-6 lg:p-8 max-w-5xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl md:text-2xl font-bold text-stone-900 flex items-center gap-2">
              <List size={22} className="text-stone-600" />
              自选股池
            </h2>
            <p className="text-sm text-stone-400 mt-0.5">{items.length} 只关注中</p>
          </div>
          <button
            onClick={() => setShowAdd(true)}
            className="flex items-center gap-1.5 px-4 py-2 bg-amber-700 text-white text-sm font-medium rounded-xl hover:bg-amber-800 active:scale-[0.98] transition-all"
          >
            <Plus size={16} />
            添加
          </button>
        </div>

        {/* Add form modal */}
        {showAdd && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/20" onClick={() => setShowAdd(false)}>
            <form
              onClick={(e) => e.stopPropagation()}
              onSubmit={handleAdd}
              className="bg-white rounded-2xl border border-stone-200 shadow-xl w-full max-w-sm p-6 space-y-4 animate-card-in"
            >
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-stone-900">添加自选股</h3>
                <button type="button" onClick={() => setShowAdd(false)} className="p-1 rounded-lg hover:bg-stone-100">
                  <X size={18} className="text-stone-400" />
                </button>
              </div>
              <div>
                <label className="block text-xs font-medium text-stone-500 mb-1">股票代码</label>
                <input
                  value={form.symbol}
                  onChange={(e) => setForm({ ...form, symbol: e.target.value })}
                  placeholder="如 600519.SH"
                  className="w-full px-3 py-2 rounded-xl border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-amber-200 bg-stone-50/50"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-stone-500 mb-1">股票名称</label>
                <input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="如 贵州茅台"
                  className="w-full px-3 py-2 rounded-xl border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-amber-200 bg-stone-50/50"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-stone-500 mb-1">关注理由</label>
                <input
                  value={form.reason}
                  onChange={(e) => setForm({ ...form, reason: e.target.value })}
                  placeholder="为什么关注这只股票"
                  className="w-full px-3 py-2 rounded-xl border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-amber-200 bg-stone-50/50"
                />
              </div>
              <button
                type="submit"
                className="w-full py-2.5 bg-amber-700 text-white rounded-xl text-sm font-medium hover:bg-amber-800 transition-colors"
              >
                确认添加
              </button>
            </form>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="py-20 text-center animate-pulse text-stone-400">加载中...</div>
        )}

        {/* Watchlist grid */}
        {!loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {items.map((item, i) => (
              <div
                key={item.id}
                className={`
                  animate-card-in delay-${Math.min(i + 1, 8)}
                  bg-white rounded-2xl border p-4 group transition-all
                  ${item.addedByRole === 'leader' || item.addedByRole === 'admin'
                    ? 'border-amber-200/80 leader-glow'
                    : 'border-stone-200/60 shadow-sm'
                  }
                `}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-stone-900">{item.name}</h3>
                      <span className="text-xs text-stone-400 font-mono">{item.symbol}</span>
                    </div>
                    <p className="text-sm text-stone-500 mt-1">{item.reason}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <LeaderBadge name={item.addedByName} role={item.addedByRole} />
                      <span className="text-[10px] text-stone-300">{item.addedAt}</span>
                    </div>
                  </div>
                  <button
                    onClick={() => remove(item.id)}
                    className="p-1.5 rounded-lg text-stone-300 hover:text-red-500 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition-all"
                    title="移除"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && items.length === 0 && (
          <div className="py-20 text-center">
            <Star size={40} className="mx-auto text-stone-200 mb-3" />
            <p className="text-stone-400">还没有自选股</p>
            <p className="text-xs text-stone-300 mt-1">点击上方"添加"按钮开始关注股票</p>
          </div>
        )}
      </div>
    </AppShell>
  );
}
