'use client';

import { TrendingUp, Eye, AlertTriangle, MinusCircle } from 'lucide-react';
import type { ActionType } from '@/lib/types';

const CONFIG: Record<ActionType, { icon: typeof TrendingUp; className: string }> = {
  '可交易': {
    icon: TrendingUp,
    className: 'text-emerald-700 bg-emerald-50 border-emerald-200',
  },
  '观望': {
    icon: Eye,
    className: 'text-amber-700 bg-amber-50 border-amber-200',
  },
  '风险升高': {
    icon: AlertTriangle,
    className: 'text-red-700 bg-red-50 border-red-200',
  },
  '不建议交易': {
    icon: MinusCircle,
    className: 'text-stone-500 bg-stone-100 border-stone-300',
  },
};

export default function ActionBadge({ action }: { action: ActionType }) {
  const { icon: Icon, className } = CONFIG[action];
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border ${className}`}>
      <Icon size={13} />
      {action}
    </span>
  );
}
