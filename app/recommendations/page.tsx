'use client';

import { useEffect, useMemo } from 'react';
import { Sparkles, TrendingUp, Eye, AlertTriangle, Wifi, WifiOff } from 'lucide-react';
import AppShell from '@/components/layout/AppShell';
import StockCard from '@/components/stock/StockCard';
import { useRecommendationStore } from '@/lib/store';
import { MOCK_WATCHLIST } from '@/lib/mock-data';

export default function RecommendationsPage() {
  const { date, summary, recommendations, loading, useMock, fetch } = useRecommendationStore();

  useEffect(() => { fetch(); }, [fetch]);

  const watchlistMap = useMemo(() => {
    const map = new Map<string, { name: string; role: 'admin' | 'leader' | 'member' }>();
    for (const w of MOCK_WATCHLIST) {
      map.set(w.symbol, { name: w.addedByName, role: w.addedByRole });
    }
    return map;
  }, []);

  return (
    <AppShell>
      <div className="p-4 md:p-6 lg:p-8 max-w-5xl mx-auto space-y-6">
        {/* Page header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl md:text-2xl font-bold text-stone-900 flex items-center gap-2">
              <Sparkles size={22} className="text-amber-600" />
              每日建议
            </h2>
            <p className="text-sm text-stone-400 mt-0.5">{date}</p>
          </div>
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
        </div>

        {/* Summary stats */}
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

        {/* Loading */}
        {loading && (
          <div className="py-20 text-center">
            <div className="animate-pulse text-stone-400">加载建议中...</div>
          </div>
        )}

        {/* Stock cards */}
        {!loading && recommendations.length > 0 && (
          <div className="space-y-3">
            {recommendations.map((rec, i) => {
              const watcher = watchlistMap.get(rec.symbol);
              return (
                <StockCard
                  key={rec.id}
                  rec={rec}
                  addedByName={watcher?.name}
                  addedByRole={watcher?.role}
                  index={i}
                />
              );
            })}
          </div>
        )}

        {!loading && recommendations.length === 0 && (
          <div className="py-20 text-center">
            <Sparkles size={40} className="mx-auto text-stone-200 mb-3" />
            <p className="text-stone-400">暂无建议</p>
            <p className="text-xs text-stone-300 mt-1">建议会在每个交易日早间生成</p>
          </div>
        )}
      </div>
    </AppShell>
  );
}
