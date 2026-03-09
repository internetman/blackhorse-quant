'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, AlertCircle, Target, Clock, UserMinus, TrendingUp, TrendingDown, Newspaper } from 'lucide-react';
import type { Recommendation, Quote, NewsItem } from '@/lib/types';
import ActionBadge from './ActionBadge';
import ConfidenceDots from './ConfidenceDots';

interface Props {
  rec: Recommendation;
  index?: number;
  onUnfollow?: (symbol: string) => void;
  quote?: Quote | null;
  news?: NewsItem[];
}

export default function StockCard({ rec, index = 0, onUnfollow, quote, news }: Props) {
  const [expanded, setExpanded] = useState(false);
  const hasNews = news && news.length > 0;
  const pct = quote?.changePercent ?? 0;
  const pctClass = pct > 0 ? 'text-red-600' : pct < 0 ? 'text-emerald-600' : 'text-stone-500';

  return (
    <div
      className={`
        animate-card-in delay-${Math.min(index + 1, 8)}
        bg-white rounded-2xl border border-stone-200/60 shadow-sm transition-all duration-300 cursor-pointer
        hover:shadow-md group hover:border-stone-300
      `}
      onClick={() => setExpanded(!expanded)}
    >
      {/* Main content */}
      <div className="p-4 md:p-5">
        {/* Top row: stock info + action badge + unfollow */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-base font-semibold text-stone-900">
                {rec.name}
              </h3>
              <span className="text-xs text-stone-400 font-mono">
                {rec.symbol}
              </span>
            </div>

            <div className="flex items-center gap-2 mt-2 flex-wrap">
              <ActionBadge action={rec.action} />
              <ConfidenceDots level={rec.confidence} />
              {quote != null && (
                <span className={`text-sm font-medium flex items-center gap-0.5 ${pctClass}`}>
                  {pct > 0 ? <TrendingUp size={14} /> : pct < 0 ? <TrendingDown size={14} /> : null}
                  ¥{quote.latestPrice.toFixed(2)}
                  {pct !== 0 && (
                    <span className="text-xs">({pct > 0 ? '+' : ''}{pct.toFixed(2)}%)</span>
                  )}
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-1 shrink-0">
            {onUnfollow && (
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); onUnfollow(rec.symbol); }}
                className="p-1.5 rounded-lg text-stone-400 hover:text-red-500 hover:bg-red-50 transition-colors"
                title="取消关注"
              >
                <UserMinus size={16} />
              </button>
            )}
            <button className="p-1 rounded-lg text-stone-300 group-hover:text-stone-500 transition-colors">
              {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </button>
          </div>
        </div>

        {/* Summary + Price plan */}
        <p className="mt-3 text-sm text-stone-700 leading-relaxed">
          {rec.summary}
        </p>
        <p className="mt-1.5 text-xs text-stone-400 leading-relaxed">
          <Target size={11} className="inline mr-1 -mt-0.5" />
          {rec.pricePlan}
        </p>

        {/* 新闻摘要：首条或「暂无」 */}
        <div className="mt-3 pt-3 border-t border-stone-100">
          <h4 className="text-xs font-medium text-stone-500 mb-1 flex items-center gap-1">
            <Newspaper size={12} />
            相关新闻
          </h4>
          {hasNews ? (
            <ul className="space-y-1">
              {news!.slice(0, expanded ? undefined : 2).map((item, i) => (
                <li key={i} className="text-xs text-stone-600 leading-snug">
                  {item.title}
                  {item.date && <span className="text-stone-400 ml-1">{item.date}</span>}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-stone-400">暂无该股票相关新闻</p>
          )}
        </div>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="px-4 md:px-5 pb-4 md:pb-5 space-y-3 border-t border-stone-100 pt-3 expand-enter">
          {/* Reasons */}
          <div>
            <h4 className="text-xs font-medium text-stone-500 mb-1.5 uppercase tracking-wider">
              判断依据
            </h4>
            <ul className="space-y-1">
              {rec.reasons.map((r, i) => (
                <li key={i} className="text-sm text-stone-600 flex items-start gap-2">
                  <span className="text-emerald-400 mt-1 shrink-0">•</span>
                  {r}
                </li>
              ))}
            </ul>
          </div>

          {/* Risks */}
          {rec.risks.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-stone-500 mb-1.5 uppercase tracking-wider flex items-center gap-1">
                <AlertCircle size={12} />
                风险提示
              </h4>
              <ul className="space-y-1">
                {rec.risks.map((r, i) => (
                  <li key={i} className="text-sm text-red-600/80 flex items-start gap-2">
                    <span className="text-red-300 mt-1 shrink-0">•</span>
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between pt-2 border-t border-stone-50">
            <p className="text-xs text-stone-400">
              失效条件: {rec.invalidCondition}
            </p>
            <span className="text-xs text-stone-400 flex items-center gap-1">
              <Clock size={11} />
              {rec.reviewAt} 复查
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
