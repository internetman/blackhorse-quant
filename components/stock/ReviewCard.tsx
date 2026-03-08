'use client';

import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { Review } from '@/lib/types';

const VERDICT_CONFIG = {
  '有效': { icon: TrendingUp, className: 'text-emerald-700 bg-emerald-50 border-emerald-200' },
  '一般': { icon: Minus, className: 'text-amber-700 bg-amber-50 border-amber-200' },
  '失效': { icon: TrendingDown, className: 'text-red-700 bg-red-50 border-red-200' },
};

export default function ReviewCard({ review, index = 0 }: { review: Review; index?: number }) {
  const { icon: Icon, className } = VERDICT_CONFIG[review.verdict];
  const isPositive = review.priceChange.startsWith('+');

  return (
    <div className={`animate-card-in delay-${Math.min(index + 1, 8)} bg-white rounded-2xl border border-stone-200/60 shadow-sm p-4 md:p-5`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-stone-900">{review.name}</h3>
            <span className="text-xs text-stone-400 font-mono">{review.symbol}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${className}`}>
              <Icon size={11} className="inline mr-0.5 -mt-0.5" />
              {review.verdict}
            </span>
          </div>

          <div className="flex items-center gap-4 mt-2 text-xs text-stone-400">
            <span>原建议: {review.originalAction}</span>
            <span>{review.reviewType}</span>
            <span>{review.reviewDate}</span>
          </div>
        </div>

        <div className="text-right shrink-0">
          <p className={`text-lg font-semibold ${isPositive ? 'text-emerald-600' : 'text-red-600'}`}>
            {review.priceChange}
          </p>
          <p className="text-[10px] text-stone-400 mt-0.5">
            {review.priceAtRecommend} → {review.priceAtReview}
          </p>
        </div>
      </div>

      <p className="mt-3 text-sm text-stone-600">{review.explanation}</p>

      <p className="mt-2 text-xs text-stone-400 italic">
        "{review.originalSummary}"
      </p>
    </div>
  );
}
