'use client';

import { useEffect, useState, useCallback } from 'react';
import { Sparkles, TrendingUp, Eye, AlertTriangle, Wifi, WifiOff, Plus, X } from 'lucide-react';
import AppShell from '@/components/layout/AppShell';
import StockCard from '@/components/stock/StockCard';
import { useRecommendationStore, useWatchlistStore } from '@/lib/store';
import { api } from '@/lib/api';
import type { StockSearchItem } from '@/lib/types';

const DEBOUNCE_MS = 300;

export default function RecommendationsPage() {
  const { date, summary, recommendations, loading, useMock, fetch: fetchRecs } = useRecommendationStore();
  const { items: watchlist, fetch: fetchWatchlist, add: addWatchItem, remove: removeWatchItem } = useWatchlistStore();

  const [showAdd, setShowAdd] = useState(false);
  const [searchQ, setSearchQ] = useState('');
  const [searchResults, setSearchResults] = useState<StockSearchItem[]>([]);
  const [searching, setSearching] = useState(false);
  const [adding, setAdding] = useState(false);

  const load = useCallback(() => {
    fetchWatchlist();
    fetchRecs();
  }, [fetchWatchlist, fetchRecs]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (searchQ.trim().length < 2) {
      setSearchResults([]);
      return;
    }
    const t = setTimeout(async () => {
      setSearching(true);
      try {
        const list = await api.searchStocks(searchQ.trim(), 20);
        setSearchResults(list);
      } catch {
        setSearchResults([]);
      } finally {
        setSearching(false);
      }
    }, DEBOUNCE_MS);
    return () => clearTimeout(t);
  }, [searchQ]);

  const handleAdd = async (item: StockSearchItem) => {
    if (adding) return;
    const already = watchlist.some((w) => w.symbol === item.symbol);
    if (already) {
      setShowAdd(false);
      setSearchQ('');
      return;
    }
    setAdding(true);
    try {
      await addWatchItem({ symbol: item.symbol, name: item.name, reason: '' });
      setShowAdd(false);
      setSearchQ('');
      setSearchResults([]);
      load();
    } finally {
      setAdding(false);
    }
  };

  const handleUnfollow = async (symbol: string) => {
    try {
      await removeWatchItem(symbol);
      load();
    } catch {
      // error already in store
    }
  };

  return (
    <AppShell>
      <div className="p-4 md:p-6 lg:p-8 max-w-5xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl md:text-2xl font-bold text-stone-900 flex items-center gap-2">
              <Sparkles size={22} className="text-amber-600" />
              我的关注
            </h2>
            <p className="text-sm text-stone-400 mt-0.5">
              {date} · 共 {watchlist.length} 只
            </p>
          </div>
          <div className="flex items-center gap-2">
            {useMock && (
              <span className="flex items-center gap-1.5 text-xs text-amber-600 bg-amber-50 px-3 py-1.5 rounded-full border border-amber-200/60">
                <WifiOff size={12} />
                演示模式
              </span>
            )}
            {!useMock && !loading && (
              <span className="flex items-center gap-1.5 text-xs text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-full border border-emerald-200/60">
                <Wifi size={12} />
                实时
              </span>
            )}
            <button
              onClick={() => setShowAdd(true)}
              className="flex items-center gap-1.5 px-4 py-2 bg-amber-700 text-white text-sm font-medium rounded-xl hover:bg-amber-800 active:scale-[0.98] transition-all"
            >
              <Plus size={16} />
              添加关注
            </button>
          </div>
        </div>

        {/* Add modal with stock search */}
        {showAdd && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/20" onClick={() => setShowAdd(false)}>
            <div
              className="bg-white rounded-2xl border border-stone-200 shadow-xl w-full max-w-md overflow-hidden animate-card-in"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-4 border-b border-stone-100 flex items-center justify-between">
                <h3 className="font-semibold text-stone-900">添加关注</h3>
                <button type="button" onClick={() => setShowAdd(false)} className="p-1 rounded-lg hover:bg-stone-100">
                  <X size={18} className="text-stone-400" />
                </button>
              </div>
              <div className="p-4">
                <label className="block text-xs font-medium text-stone-500 mb-1">输入代码、名称或首字母</label>
                <input
                  value={searchQ}
                  onChange={(e) => setSearchQ(e.target.value)}
                  placeholder="如 600519、贵州、GZMT"
                  className="w-full px-3 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-amber-200 bg-stone-50/50"
                  autoFocus
                />
                {searchQ.trim().length > 0 && searchQ.trim().length < 2 && (
                  <p className="text-xs text-stone-400 mt-1.5">至少输入 2 个字符</p>
                )}
                <div className="mt-2 max-h-48 overflow-y-auto rounded-xl border border-stone-100">
                  {searching && <div className="p-3 text-sm text-stone-400">搜索中...</div>}
                  {!searching && searchResults.length === 0 && searchQ.trim().length >= 2 && (
                    <div className="p-3 text-sm text-stone-400">未找到匹配股票</div>
                  )}
                  {!searching && searchResults.map((item) => {
                    const isAdded = watchlist.some((w) => w.symbol === item.symbol);
                    return (
                      <button
                        key={item.symbol}
                        type="button"
                        onClick={() => !isAdded && handleAdd(item)}
                        disabled={isAdded}
                        className="w-full flex items-center justify-between px-3 py-2.5 text-left text-sm hover:bg-stone-50 disabled:opacity-50 disabled:cursor-default"
                      >
                        <span className="font-medium text-stone-900">{item.name}</span>
                        <span className="text-stone-400 font-mono text-xs">{item.symbol}</span>
                        {isAdded && <span className="text-xs text-amber-600">已关注</span>}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-white rounded-xl p-4 border border-stone-200/60 shadow-sm">
            <p className="text-2xl font-bold text-stone-900">{summary.total}</p>
            <p className="text-xs text-stone-400 mt-0.5">关注总数</p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-stone-200/60 shadow-sm">
            <p className="text-2xl font-bold text-emerald-600 flex items-center gap-1">
              <TrendingUp size={18} />
              {summary.tradable}
            </p>
            <p className="text-xs text-stone-400 mt-0.5">可交易</p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-stone-200/60 shadow-sm">
            <p className="text-2xl font-bold text-amber-600 flex items-center gap-1">
              <Eye size={18} />
              {summary.watch}
            </p>
            <p className="text-xs text-stone-400 mt-0.5">观望</p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-stone-200/60 shadow-sm">
            <p className="text-2xl font-bold text-red-600 flex items-center gap-1">
              <AlertTriangle size={18} />
              {summary.risky}
            </p>
            <p className="text-xs text-stone-400 mt-0.5">风险</p>
          </div>
        </div>

        {loading && (
          <div className="py-20 text-center">
            <div className="animate-pulse text-stone-400">加载中...</div>
          </div>
        )}

        {!loading && recommendations.length > 0 && (
          <div className="space-y-3">
            {recommendations.map((rec, i) => (
              <StockCard
                key={rec.id}
                rec={rec}
                index={i}
                onUnfollow={handleUnfollow}
              />
            ))}
          </div>
        )}

        {!loading && recommendations.length === 0 && (
          <div className="py-20 text-center">
            <Sparkles size={40} className="mx-auto text-stone-200 mb-3" />
            <p className="text-stone-400">暂无关注或暂无建议</p>
            <p className="text-xs text-stone-300 mt-1">点击「添加关注」添加股票，建议会在每个交易日生成</p>
          </div>
        )}
      </div>
    </AppShell>
  );
}
