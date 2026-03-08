'use client';

import { useEffect, useState } from 'react';
import { Lock, Edit3, Check, X } from 'lucide-react';
import AppShell from '@/components/layout/AppShell';
import { usePositionStore } from '@/lib/store';
import type { PositionLevel } from '@/lib/types';

const LEVEL_COLORS: Record<PositionLevel, string> = {
  '空仓': 'text-stone-400 bg-stone-50 border-stone-200',
  '轻仓': 'text-sky-700 bg-sky-50 border-sky-200',
  '中仓': 'text-amber-700 bg-amber-50 border-amber-200',
  '重仓': 'text-red-700 bg-red-50 border-red-200',
};

export default function PositionsPage() {
  const { positions, loading, fetch, update } = usePositionStore();
  const [editId, setEditId] = useState<string | null>(null);
  const [editNotes, setEditNotes] = useState('');

  useEffect(() => { fetch(); }, [fetch]);

  const startEdit = (id: string, notes: string) => {
    setEditId(id);
    setEditNotes(notes);
  };

  const saveEdit = async (id: string) => {
    await update(id, { notes: editNotes });
    setEditId(null);
  };

  return (
    <AppShell>
      <div className="p-4 md:p-6 lg:p-8 max-w-5xl mx-auto space-y-6">
        <div>
          <h2 className="text-xl md:text-2xl font-bold text-stone-900 flex items-center gap-2">
            <Lock size={22} className="text-stone-600" />
            我的持仓
          </h2>
          <p className="text-sm text-stone-400 mt-0.5">
            仅自己可见，不会分享给圈子成员
          </p>
        </div>

        <div className="bg-amber-50/60 rounded-xl p-3 border border-amber-200/40">
          <p className="text-xs text-amber-700">
            🔒 持仓信息完全私密，其他圈子成员无法查看你的仓位和成本价。
          </p>
        </div>

        {loading && <div className="py-20 text-center animate-pulse text-stone-400">加载中...</div>}

        {!loading && (
          <div className="space-y-3">
            {positions.map((pos, i) => (
              <div
                key={pos.id}
                className={`animate-card-in delay-${Math.min(i + 1, 8)} bg-white rounded-2xl border border-stone-200/60 shadow-sm p-4 md:p-5`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-semibold text-stone-900">{pos.name}</h3>
                      <span className="text-xs text-stone-400 font-mono">{pos.symbol}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${LEVEL_COLORS[pos.level]}`}>
                        {pos.level}
                      </span>
                    </div>

                    {pos.costPrice && (
                      <p className="text-sm text-stone-500 mt-1.5">
                        成本价: <span className="font-mono font-medium text-stone-700">¥{pos.costPrice}</span>
                      </p>
                    )}

                    {editId === pos.id ? (
                      <div className="mt-2 flex items-center gap-2">
                        <input
                          value={editNotes}
                          onChange={(e) => setEditNotes(e.target.value)}
                          className="flex-1 px-3 py-1.5 rounded-lg border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-amber-200"
                          autoFocus
                        />
                        <button onClick={() => saveEdit(pos.id)} className="p-1.5 rounded-lg hover:bg-emerald-50 text-emerald-600">
                          <Check size={16} />
                        </button>
                        <button onClick={() => setEditId(null)} className="p-1.5 rounded-lg hover:bg-stone-100 text-stone-400">
                          <X size={16} />
                        </button>
                      </div>
                    ) : (
                      <p className="text-sm text-stone-500 mt-1.5">
                        {pos.notes || '无备注'}
                      </p>
                    )}
                  </div>

                  {editId !== pos.id && (
                    <button
                      onClick={() => startEdit(pos.id, pos.notes)}
                      className="p-1.5 rounded-lg text-stone-300 hover:text-stone-600 hover:bg-stone-100 transition-colors"
                    >
                      <Edit3 size={14} />
                    </button>
                  )}
                </div>

                <p className="text-[10px] text-stone-300 mt-2">更新于 {pos.updatedAt}</p>
              </div>
            ))}
          </div>
        )}

        {!loading && positions.length === 0 && (
          <div className="py-20 text-center">
            <Lock size={40} className="mx-auto text-stone-200 mb-3" />
            <p className="text-stone-400">还没有持仓记录</p>
            <p className="text-xs text-stone-300 mt-1">在每日建议页面可以记录持仓</p>
          </div>
        )}
      </div>
    </AppShell>
  );
}
