'use client';
import { History, ExternalLink } from 'lucide-react';
import { useStore } from '@/lib/store';

export const TradesTable = () => {
  const trades = useStore((state) => state.trades);
  
  return (
    <div className="bg-[#161922] border border-slate-800 rounded-xl md:rounded-2xl overflow-hidden shadow-2xl">
      <div className="px-4 md:px-6 py-4 md:py-5 border-b border-slate-800 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 bg-black/20">
        <h3 className="font-bold text-white text-xs uppercase tracking-[0.2em] flex items-center gap-2">
          <History size={16} /> 交易执行引擎审计流水
        </h3>
        <button className="bg-blue-600 text-[10px] px-4 md:px-5 py-2 rounded-lg md:rounded-xl text-white font-black hover:bg-blue-500 shadow-lg active:scale-95 transition-all touch-manipulation whitespace-nowrap">
          导出当日 PDF 报告
        </button>
      </div>
      {/* 桌面端表格 */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="text-[10px] text-slate-500 uppercase bg-black/40 font-bold tracking-widest">
            <tr>
              <th className="px-6 py-5">成交时间</th>
              <th className="px-6 py-5">标的代码</th>
              <th className="px-6 py-5">执行结果</th>
              <th className="px-6 py-5 text-right">成交均价</th>
              <th className="px-6 py-5 text-center">深度审计</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/40">
            {trades.map(trade => (
              <tr key={trade.id} className="hover:bg-slate-800/40 transition-colors">
                <td className="px-6 py-5 font-mono text-slate-500">{trade.time}</td>
                <td className="px-6 py-5 font-black text-slate-200">{trade.asset}</td>
                <td className="px-6 py-5">
                  <span className={`px-3 py-1 rounded-lg text-[10px] font-black border tracking-wider ${trade.status === '正常成交' ? 'text-rose-500 bg-rose-500/10 border-rose-500/20' : trade.status === '强平' ? 'text-red-500 bg-red-500/10 border-red-500/20' : 'text-amber-500 bg-amber-500/10 border-amber-500/20'}`}>
                    {trade.status}
                  </span>
                </td>
                <td className="px-6 py-5 text-right font-mono font-black text-slate-200">¥{trade.price}</td>
                <td className="px-6 py-5 text-center">
                  <button className="text-blue-400 hover:text-blue-200 transition-colors hover:scale-125 transform inline-block touch-manipulation">
                    <ExternalLink size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {/* 移动端卡片式布局 */}
      <div className="md:hidden divide-y divide-slate-800/40">
        {trades.map(trade => (
          <div key={trade.id} className="p-4 space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="font-black text-slate-200 text-sm mb-1">{trade.asset}</div>
                <div className="text-xs text-slate-500 font-mono mb-2">{trade.time}</div>
                <span className={`inline-block px-2 py-1 rounded-lg text-[10px] font-black border ${trade.status === '正常成交' ? 'text-rose-500 bg-rose-500/10 border-rose-500/20' : trade.status === '强平' ? 'text-red-500 bg-red-500/10 border-red-500/20' : 'text-amber-500 bg-amber-500/10 border-amber-500/20'}`}>
                  {trade.status}
                </span>
              </div>
              <div className="text-right">
                <div className="text-sm font-mono font-black text-slate-200 mb-1">¥{trade.price}</div>
                <button className="text-blue-400 hover:text-blue-200 transition-colors touch-manipulation">
                  <ExternalLink size={16} />
                </button>
              </div>
            </div>
            {trade.reason && (
              <div className="text-xs text-slate-500 italic">原因: {trade.reason}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
