'use client';
import { useStore } from '@/lib/store';
import { PositionsTable } from '@/components/PositionsTable';

export default function DashboardPage() {
  const sysStatus = useStore((state) => state.sysStatus);
  const positions = useStore((state) => state.positions);
  const totalPnl = useStore((state) => state.totalPnl);
  
  const getStatusInfo = (status: string) => {
    switch(status) {
      case 'running': return { label: '运行中', color: 'text-rose-500' };
      case 'paused': return { label: '已暂停', color: 'text-amber-500' };
      case 'kill': return { label: '强平停止', color: 'text-emerald-500' };
      default: return { label: '', color: '' };
    }
  };
  
  const statusInfo = getStatusInfo(sysStatus);
  
  return (
    <div className="animate-in fade-in duration-700 space-y-8 max-w-7xl mx-auto w-full">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl border-l-4 border-l-blue-500">
          <div className="text-[10px] text-slate-500 mb-1 font-bold uppercase tracking-widest">系统状态</div>
          <div className={`text-2xl font-bold ${statusInfo.color}`}>{statusInfo.label}</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl border-l-4 border-l-slate-600">
          <div className="text-[10px] text-slate-500 mb-1 font-bold uppercase tracking-widest">活跃持仓</div>
          <div className="text-2xl font-bold text-white font-mono tracking-tighter">
            {positions.length} <span className="text-xs font-normal text-slate-500 ml-1">个标的</span>
          </div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl border-l-4 border-l-rose-500">
          <div className="text-[10px] text-slate-500 mb-1 font-bold uppercase tracking-widest text-rose-500/80">未实现盈亏</div>
          <div className={`text-2xl font-bold font-mono tracking-tighter ${totalPnl >= 0 ? 'text-rose-500' : 'text-emerald-500'}`}>
            {totalPnl >= 0 ? '+' : ''}¥{totalPnl.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
          </div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl border-l-4 border-l-blue-400">
          <div className="text-[10px] text-slate-500 mb-1 font-bold uppercase tracking-widest">资金占用率</div>
          <div className="text-2xl font-bold text-blue-400 font-mono tracking-tighter">
            {positions.length > 0 ? Math.round((positions.length / 30) * 100) : 0}%
          </div>
        </div>
      </div>

      <PositionsTable />
    </div>
  );
}
