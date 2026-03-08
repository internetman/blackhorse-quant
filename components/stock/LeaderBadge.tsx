'use client';

import type { UserRole } from '@/lib/types';

interface Props {
  name: string;
  role: UserRole;
}

export default function LeaderBadge({ name, role }: Props) {
  if (role === 'leader' || role === 'admin') {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200/60 font-medium">
        <span className="text-amber-500">★</span> {name}推荐
      </span>
    );
  }

  return (
    <span className="inline-flex items-center text-xs text-stone-400 px-2 py-0.5 rounded-full bg-stone-50 border border-stone-200/60">
      {name}关注
    </span>
  );
}
