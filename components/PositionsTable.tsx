'use client';
import React, { useEffect, useState } from 'react';
import { Briefcase, AlertTriangle } from 'lucide-react';
import { useStore } from '@/lib/store';

const CONFIRM_KEYWORD = 'CLEAR';

export const PositionsTable = () => {
  const positions = useStore((state) => state.positions);
  const fetchPositions = useStore((state) => state.fetchPositions);
  const clearPositions = useStore((state) => state.clearPositions);
  const [modalOpen, setModalOpen] = useState(false);
  const [confirmInput, setConfirmInput] = useState('');
  const [clearing, setClearing] = useState(false);

  useEffect(() => {
    fetchPositions();
  }, [fetchPositions]);

  const handleForceCloseClick = () => setModalOpen(true);
  const handleModalClose = () => {
    setModalOpen(false);
    setConfirmInput('');
  };
  const handleConfirmForceClose = async () => {
    if (confirmInput !== CONFIRM_KEYWORD) return;
    setClearing(true);
    try {
      await clearPositions();
      handleModalClose();
    } finally {
      setClearing(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl md:rounded-2xl overflow-hidden shadow-2xl">
      <div className="px-4 md:px-6 py-3 md:py-4 border-b border-slate-800 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 bg-black/10 font-bold">
        <h3 className="text-white text-xs uppercase tracking-widest flex items-center gap-2">
          <Briefcase size={14}/> 实时股票持仓列表 (T+0)
        </h3>
        <button
          type="button"
          onClick={handleForceCloseClick}
          className="text-[10px] text-rose-500 border border-rose-500/30 px-3 md:px-4 py-1.5 rounded-lg hover:bg-rose-400/10 font-bold uppercase tracking-widest transition-all touch-manipulation whitespace-nowrap"
        >
          全仓紧急停止并平仓
        </button>
      </div>

      {/* 强行平仓确认弹窗 */}
      {modalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60" role="dialog" aria-modal="true" aria-labelledby="force-close-title">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-rose-500/20 flex items-center justify-center">
                <AlertTriangle className="text-rose-500" size={20} />
              </div>
              <div>
                <h3 id="force-close-title" className="text-lg font-bold text-white">强行平仓 / 清空持仓</h3>
                <p className="text-sm text-slate-400 mt-1">此操作将清空所有持仓，不可恢复。请在下方输入 <code className="bg-slate-800 px-1.5 py-0.5 rounded font-mono text-rose-400">{CONFIRM_KEYWORD}</code> 以确认。</p>
              </div>
            </div>
            <input
              type="text"
              value={confirmInput}
              onChange={(e) => setConfirmInput(e.target.value)}
              placeholder={`输入 ${CONFIRM_KEYWORD}`}
              className="w-full px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-white placeholder-slate-500 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/50"
              autoComplete="off"
              aria-label={`输入 ${CONFIRM_KEYWORD} 确认`}
            />
            <div className="flex gap-3 justify-end">
              <button
                type="button"
                onClick={handleModalClose}
                className="px-4 py-2 rounded-xl border border-slate-600 text-slate-300 hover:bg-slate-800 transition-colors"
              >
                取消
              </button>
              <button
                type="button"
                onClick={handleConfirmForceClose}
                disabled={confirmInput !== CONFIRM_KEYWORD || clearing}
                className="px-4 py-2 rounded-xl bg-rose-600 text-white font-medium hover:bg-rose-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {clearing ? '执行中…' : '确认强平'}
              </button>
            </div>
          </div>
        </div>
      )}
      {/* 桌面端表格 */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full text-left text-[11px]">
          <thead className="text-slate-500 uppercase bg-black/30 font-bold tracking-widest">
            <tr>
              <th className="px-6 py-4">证券代码</th>
              <th className="px-6 py-4">方向</th>
              <th className="px-6 py-4">持仓/均价</th>
              <th className="px-6 py-4 text-right">收益率</th>
              <th className="px-6 py-4 text-right">估盈金额</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {positions.map(pos => (
              <tr key={pos.id} className="hover:bg-slate-800/30 transition-colors group">
                <td className="px-6 py-5 font-bold text-white group-hover:text-blue-400 transition-colors">{pos.asset}</td>
                <td className="px-6 py-5">
                  <span className={`px-3 py-1 rounded-full text-[10px] font-black ${pos.side === '多' ? 'text-rose-500 bg-rose-500/10 border border-rose-500/20' : 'text-emerald-500 bg-emerald-500/10 border border-emerald-500/20'}`}>
                    {pos.side}
                  </span>
                </td>
                <td className="px-6 py-5 font-mono text-slate-300">
                  <div>{pos.amount} 股</div>
                  <div className="opacity-40 text-[10px] italic">{pos.entryPrice}</div>
                </td>
                <td className={`px-6 py-5 text-right font-mono font-black ${pos.pnl.startsWith('+') ? 'text-rose-500' : 'text-emerald-500'}`}>
                  {pos.pnl}
                </td>
                <td className={`px-6 py-5 text-right font-mono font-black ${pos.pnl.startsWith('+') ? 'text-rose-500' : 'text-emerald-500'}`}>
                  {pos.pnlValue}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {/* 移动端卡片式布局 */}
      <div className="md:hidden divide-y divide-slate-800/50">
        {positions.map(pos => (
          <div key={pos.id} className="p-4 space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="font-bold text-white text-sm mb-1 truncate">{pos.asset}</div>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-black ${pos.side === '多' ? 'text-rose-500 bg-rose-500/10 border border-rose-500/20' : 'text-emerald-500 bg-emerald-500/10 border border-emerald-500/20'}`}>
                    {pos.side}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">{pos.amount} 股</span>
                </div>
              </div>
              <div className="text-right">
                <div className={`text-sm font-mono font-black ${pos.pnl.startsWith('+') ? 'text-rose-500' : 'text-emerald-500'}`}>
                  {pos.pnl}
                </div>
                <div className={`text-xs font-mono ${pos.pnl.startsWith('+') ? 'text-rose-500' : 'text-emerald-500'}`}>
                  {pos.pnlValue}
                </div>
              </div>
            </div>
            <div className="text-xs text-slate-500 font-mono">均价: {pos.entryPrice}</div>
          </div>
        ))}
      </div>
    </div>
  );
};
