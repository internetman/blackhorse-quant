'use client';
import { Briefcase } from 'lucide-react';
import { useStore } from '@/lib/store';

export const PositionsTable = () => {
  const positions = useStore((state) => state.positions);
  
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl md:rounded-2xl overflow-hidden shadow-2xl">
      <div className="px-4 md:px-6 py-3 md:py-4 border-b border-slate-800 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 bg-black/10 font-bold">
        <h3 className="text-white text-xs uppercase tracking-widest flex items-center gap-2">
          <Briefcase size={14}/> 实时股票持仓列表 (T+0)
        </h3>
        <button className="text-[10px] text-rose-500 border border-rose-500/30 px-3 md:px-4 py-1.5 rounded-lg hover:bg-rose-400/10 font-bold uppercase tracking-widest transition-all touch-manipulation whitespace-nowrap">
          全仓紧急停止并平仓
        </button>
      </div>
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
