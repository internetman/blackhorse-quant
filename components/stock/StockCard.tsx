'use client';

import { useState, useRef, useEffect } from 'react';
import {
  ChevronDown, ChevronUp, AlertCircle, Target, Clock,
  UserMinus, TrendingUp, TrendingDown, Minus, Newspaper,
  ArrowUpCircle, ArrowDownCircle, PauseCircle
} from 'lucide-react';
import type { Recommendation, Quote, NewsItem, ActionType, BiasType } from '@/lib/types';
import ConfidenceDots from './ConfidenceDots';

interface Props {
  rec: Recommendation;
  index?: number;
  onUnfollow?: (symbol: string) => void;
  quote?: Quote | null;
  news?: NewsItem[];
}

type TradeAdvice = '买入' | '卖出' | '观望';
type Sentiment = '看涨' | '看跌' | '中性';

function deriveAdvice(action: ActionType): TradeAdvice {
  if (action === '可交易') return '买入';
  if (action === '风险升高' || action === '不建议交易') return '卖出';
  return '观望';
}

function deriveSentiment(bias: BiasType): Sentiment {
  if (bias === '偏低吸' || bias === '偏突破') return '看涨';
  if (bias === '偏减仓') return '看跌';
  return '中性';
}

const ADVICE_STYLE: Record<TradeAdvice, string> = {
  '买入': 'bg-red-600 text-white',
  '卖出': 'bg-emerald-600 text-white',
  '观望': 'bg-amber-500 text-white',
};

const SENTIMENT_STYLE: Record<Sentiment, { className: string; icon: typeof TrendingUp }> = {
  '看涨': { className: 'text-red-600 bg-red-50 border-red-200', icon: ArrowUpCircle },
  '看跌': { className: 'text-emerald-700 bg-emerald-50 border-emerald-200', icon: ArrowDownCircle },
  '中性': { className: 'text-amber-700 bg-amber-50 border-amber-200', icon: PauseCircle },
};

export default function StockCard({ rec, index = 0, onUnfollow, quote, news }: Props) {
  const [expanded, setExpanded] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);
  const [contentHeight, setContentHeight] = useState(0);

  const effectiveQuote = quote ?? rec.quote;
  const effectiveNews = news ?? rec.news ?? [];
  const hasNews = effectiveNews.length > 0;
  const pct = effectiveQuote?.changePercent ?? 0;
  const pctClass = pct > 0 ? 'text-red-600' : pct < 0 ? 'text-emerald-600' : 'text-stone-500';
  const volumeText = effectiveQuote
    ? effectiveQuote.volume >= 100000000
      ? `${(effectiveQuote.volume / 100000000).toFixed(2)}亿`
      : effectiveQuote.volume >= 10000
        ? `${(effectiveQuote.volume / 10000).toFixed(0)}万`
        : `${effectiveQuote.volume}`
    : '--';

  const advice = deriveAdvice(rec.action);
  const sentiment = deriveSentiment(rec.bias);
  const SentimentIcon = SENTIMENT_STYLE[sentiment].icon;

  useEffect(() => {
    if (contentRef.current) {
      setContentHeight(contentRef.current.scrollHeight);
    }
  }, [expanded, rec, effectiveNews]);

  return (
    <div
      className={`
        animate-card-in delay-${Math.min(index + 1, 8)}
        bg-white rounded-2xl border border-stone-200/60 shadow-sm
        hover:shadow-md group hover:border-stone-300 transition-shadow duration-200
      `}
    >
      {/* === 结论层（最醒目，始终可见）=== */}
      <div
        className="p-4 md:p-5 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        {/* 第一行：推荐结论 + 看涨/看跌 + 取消关注 */}
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 flex-wrap">
            {/* 今日交易推荐 - 大标签 */}
            <span className={`px-3 py-1.5 rounded-lg text-sm font-bold ${ADVICE_STYLE[advice]}`}>
              {advice}
            </span>
            {/* 看涨/看跌/中性 */}
            <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border ${SENTIMENT_STYLE[sentiment].className}`}>
              <SentimentIcon size={14} />
              {sentiment}
            </span>
            <ConfidenceDots level={rec.confidence} />
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

        {/* 第二行：股票名 + 代码 + 实时行情 */}
        <div className="flex items-baseline gap-3 mt-3 flex-wrap">
          <h3 className="text-lg font-bold text-stone-900">{rec.name}</h3>
          <span className="text-xs text-stone-400 font-mono">{rec.symbol}</span>
          {effectiveQuote != null && (
            <span className={`text-base font-bold flex items-center gap-0.5 ${pctClass}`}>
              {pct > 0 ? <TrendingUp size={16} /> : pct < 0 ? <TrendingDown size={16} /> : <Minus size={16} />}
              ¥{effectiveQuote.latestPrice.toFixed(2)}
              <span className="text-sm font-medium ml-0.5">
                ({pct > 0 ? '+' : ''}{pct.toFixed(2)}%)
              </span>
            </span>
          )}
        </div>

        {/* 第三行：推荐价格区间（醒目） */}
        <div className="mt-3 px-3 py-2.5 rounded-xl bg-stone-50 border border-stone-100">
          <p className="text-xs text-stone-500 mb-0.5 flex items-center gap-1">
            <Target size={12} />
            {advice === '买入' ? '买入推荐价' : advice === '卖出' ? '卖出推荐价' : '价格参考'}
          </p>
          <p className="text-sm font-semibold text-stone-800 leading-relaxed">{rec.pricePlan}</p>
        </div>

        {/* 第四行：简要摘要 */}
        <p className="mt-3 text-sm text-stone-600 leading-relaxed">
          {rec.summary}
        </p>

        {effectiveQuote && (
          <div className="mt-2 text-xs text-stone-400 flex items-center gap-3">
            <span>成交量: {volumeText}</span>
            <span>更新: {effectiveQuote.updatedAt?.slice(11, 19) || '--'}</span>
          </div>
        )}
      </div>

      {/* === 展开区：理由 → 新闻 → 底部（带动效） === */}
      <div
        className="overflow-hidden transition-[max-height] duration-300 ease-in-out"
        style={{ maxHeight: expanded ? `${contentHeight + 40}px` : '0px' }}
      >
        <div ref={contentRef} className="px-4 md:px-5 pb-4 md:pb-5 space-y-4 border-t border-stone-100 pt-4">
          {/* 理由支撑 */}
          {rec.reasons.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-stone-500 mb-2 uppercase tracking-wider">
                判断依据
              </h4>
              <ul className="space-y-1.5">
                {rec.reasons.map((r, i) => (
                  <li key={i} className="text-sm text-stone-600 flex items-start gap-2">
                    <span className="text-emerald-400 mt-0.5 shrink-0">•</span>
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 风险提示 */}
          {rec.risks.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-stone-500 mb-2 uppercase tracking-wider flex items-center gap-1">
                <AlertCircle size={12} />
                风险提示
              </h4>
              <ul className="space-y-1.5">
                {rec.risks.map((r, i) => (
                  <li key={i} className="text-sm text-red-600/80 flex items-start gap-2">
                    <span className="text-red-300 mt-0.5 shrink-0">•</span>
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 新闻等支撑 */}
          <div>
            <h4 className="text-xs font-semibold text-stone-500 mb-2 uppercase tracking-wider flex items-center gap-1">
              <Newspaper size={12} />
              相关新闻
            </h4>
            {hasNews ? (
              <ul className="space-y-1.5">
                {effectiveNews.map((item, i) => (
                  <li key={i} className="text-sm text-stone-600 leading-snug">
                    {item.title}
                    {item.date && <span className="text-stone-400 ml-1.5 text-xs">{item.date}</span>}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-stone-400">暂无该股票相关新闻</p>
            )}
          </div>

          {/* 底部信息 */}
          <div className="flex items-center justify-between pt-3 border-t border-stone-100">
            <p className="text-xs text-stone-400">
              失效条件: {rec.invalidCondition}
            </p>
            <span className="text-xs text-stone-400 flex items-center gap-1">
              <Clock size={11} />
              {rec.reviewAt} 复查
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
