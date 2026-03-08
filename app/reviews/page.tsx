'use client';

import { useEffect } from 'react';
import { BarChart3, CheckCircle2, HelpCircle, XCircle } from 'lucide-react';
import AppShell from '@/components/layout/AppShell';
import ReviewCard from '@/components/stock/ReviewCard';
import { useReviewStore } from '@/lib/store';

export default function ReviewsPage() {
  const { reviews, stats, loading, filterType, fetch, fetchStats, setFilter } = useReviewStore();

  useEffect(() => { fetch(); fetchStats(); }, [fetch, fetchStats]);

  const filters = [
    { label: '全部', value: null },
    { label: 'T+1', value: 'T+1' },
    { label: 'T+3', value: 'T+3' },
    { label: 'T+5', value: 'T+5' },
  ];

  const filteredReviews = filterType
    ? reviews.filter((r) => r.reviewType === filterType)
    : reviews;

  return (
    <AppShell>
      <div className="p-4 md:p-6 lg:p-8 max-w-5xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h2 className="text-xl md:text-2xl font-bold text-stone-900 flex items-center gap-2">
            <BarChart3 size={22} className="text-stone-600" />
            复盘记录
          </h2>
          <p className="text-sm text-stone-400 mt-0.5">建议效果追踪与验证</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-white rounded-xl p-4 border border-stone-200/60 shadow-sm">
            <p className="text-2xl font-bold text-stone-900">{stats.total}</p>
            <p className="text-xs text-stone-400 mt-0.5">累计复盘</p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-stone-200/60 shadow-sm">
            <p className="text-2xl font-bold text-emerald-600 flex items-center gap-1">
              <CheckCircle2 size={18} />
              {stats.effective}
            </p>
            <p className="text-xs text-stone-400 mt-0.5">有效</p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-stone-200/60 shadow-sm">
            <p className="text-2xl font-bold text-amber-600 flex items-center gap-1">
              <HelpCircle size={18} />
              {stats.neutral}
            </p>
            <p className="text-xs text-stone-400 mt-0.5">一般</p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-stone-200/60 shadow-sm">
            <p className="text-2xl font-bold text-red-600 flex items-center gap-1">
              <XCircle size={18} />
              {stats.ineffective}
            </p>
            <p className="text-xs text-stone-400 mt-0.5">失效</p>
          </div>
        </div>

        {/* Accuracy bar */}
        <div className="bg-white rounded-xl p-4 border border-stone-200/60 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-stone-700">建议有效率</span>
            <span className="text-lg font-bold text-emerald-600">{(stats.effectiveRate * 100).toFixed(0)}%</span>
          </div>
          <div className="h-2 bg-stone-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-emerald-500 rounded-full transition-all duration-700"
              style={{ width: `${stats.effectiveRate * 100}%` }}
            />
          </div>
        </div>

        {/* Filter tabs */}
        <div className="flex gap-2">
          {filters.map((f) => (
            <button
              key={f.label}
              onClick={() => { setFilter(f.value); if (f.value) fetch(f.value); else fetch(); }}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                filterType === f.value
                  ? 'bg-stone-900 text-white'
                  : 'bg-stone-100 text-stone-500 hover:bg-stone-200'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Reviews */}
        {loading && <div className="py-20 text-center animate-pulse text-stone-400">加载中...</div>}

        {!loading && (
          <div className="space-y-3">
            {filteredReviews.map((review, i) => (
              <ReviewCard key={review.id} review={review} index={i} />
            ))}
          </div>
        )}

        {!loading && filteredReviews.length === 0 && (
          <div className="py-20 text-center">
            <BarChart3 size={40} className="mx-auto text-stone-200 mb-3" />
            <p className="text-stone-400">暂无复盘记录</p>
          </div>
        )}
      </div>
    </AppShell>
  );
}
