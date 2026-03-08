'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, AlertCircle, Target, Clock } from 'lucide-react';
import type { Recommendation, UserRole } from '@/lib/types';
import ActionBadge from './ActionBadge';
import LeaderBadge from './LeaderBadge';
import ConfidenceDots from './ConfidenceDots';

interface Props {
  rec: Recommendation;
  addedByName?: string;
  addedByRole?: UserRole;
  index?: number;
}

export default function StockCard({ rec, addedByName, addedByRole, index = 0 }: Props) {
  const [expanded, setExpanded] = useState(false);
  const isLeaderPick = addedByRole === 'leader' || addedByRole === 'admin';

  return (
    <div
      className={`
        animate-card-in delay-${Math.min(index + 1, 8)}
        bg-white rounded-2xl border transition-all duration-300 cursor-pointer
        hover:shadow-md group
        ${isLeaderPick
          ? 'border-amber-200/80 leader-glow'
          : 'border-stone-200/60 shadow-sm hover:border-stone-300'
        }
      `}
      onClick={() => setExpanded(!expanded)}
    >
      {/* Main content */}
      <div className="p-4 md:p-5">
        {/* Top row: stock info + action badge */}
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

            {/* Tags row */}
            <div className="flex items-center gap-2 mt-2 flex-wrap">
              <ActionBadge action={rec.action} />
              <ConfidenceDots level={rec.confidence} />
              {addedByName && addedByRole && (
                <LeaderBadge name={addedByName} role={addedByRole} />
              )}
            </div>
          </div>

          {/* Expand toggle */}
          <button className="p-1 rounded-lg text-stone-300 group-hover:text-stone-500 transition-colors shrink-0 mt-1">
            {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </button>
        </div>

        {/* Summary + Price plan */}
        <p className="mt-3 text-sm text-stone-700 leading-relaxed">
          {rec.summary}
        </p>
        <p className="mt-1.5 text-xs text-stone-400 leading-relaxed">
          <Target size={11} className="inline mr-1 -mt-0.5" />
          {rec.pricePlan}
        </p>
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
