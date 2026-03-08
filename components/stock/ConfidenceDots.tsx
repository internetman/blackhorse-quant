'use client';

import type { ConfidenceLevel } from '@/lib/types';

const levels: Record<ConfidenceLevel, number> = { '高': 3, '中': 2, '低': 1 };

export default function ConfidenceDots({ level }: { level: ConfidenceLevel }) {
  const filled = levels[level];
  return (
    <div className="flex items-center gap-1" title={`置信度: ${level}`}>
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className={`w-1.5 h-1.5 rounded-full ${
            i <= filled ? 'bg-stone-700' : 'bg-stone-200'
          }`}
        />
      ))}
      <span className="text-[10px] text-stone-400 ml-0.5">{level}</span>
    </div>
  );
}
