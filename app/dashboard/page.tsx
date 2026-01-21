'use client';
import React from 'react';
import { useStore } from '@/lib/store';
import { PositionsTable } from '@/components/PositionsTable';

export default function DashboardPage() {
  const sysStatus = useStore((state) => state.sysStatus);
  const positions = useStore((state) => state.positions);
  const stats = useStore((state) => state.stats);
  const isConnected = useStore((state) => state.isConnected);
  const error = useStore((state) => state.error);
  const fetchPositions = useStore((state) => state.fetchPositions);
  const fetchStats = useStore((state) => state.fetchStats);
  const checkConnection = useStore((state) => state.checkConnection);
  
  const totalPnl = stats?.totalPnl ?? 0;
  const positionCount = stats?.positionCount ?? positions.length;
  const capitalUsage = stats?.capitalUsage ?? (positions.length > 0 ? Math.round((positions.length / 30) * 100) : 0);
  
  React.useEffect(() => {
    checkConnection();
    fetchPositions();
    fetchStats();
    // 每2秒刷新一次数据
    const interval = setInterval(() => {
      fetchPositions();
      fetchStats();
    }, 2000);
    return () => clearInterval(interval);
  }, [fetchPositions, fetchStats, checkConnection]);
  
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
      {/* 连接状态提示 */}
      {!isConnected && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4 md:p-6">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-5 h-5 rounded-full bg-amber-500/20 border border-amber-500/50 flex items-center justify-center mt-0.5">
              <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></div>
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-sm md:text-base font-bold text-amber-500 mb-1">无法连接到后端服务</h3>
              <p className="text-xs md:text-sm text-slate-400 mb-2">
                {error || '请确保后端服务已部署并配置了正确的 API 地址。'}
              </p>
              <p className="text-xs text-slate-500">
                本地开发：确保 FastAPI 运行在 <code className="bg-slate-800/50 px-1.5 py-0.5 rounded">http://localhost:8000</code>
                <br />
                生产环境：请在 Vercel 环境变量中设置 <code className="bg-slate-800/50 px-1.5 py-0.5 rounded">NEXT_PUBLIC_API_URL</code>
              </p>
              <p className="text-xs text-slate-500 mt-2">
                详细部署说明请查看项目根目录的 <code className="bg-slate-800/50 px-1.5 py-0.5 rounded">VERCEL_BACKEND_SETUP.md</code> 文件
              </p>
            </div>
          </div>
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl border-l-4 border-l-blue-500">
          <div className="text-[10px] text-slate-500 mb-1 font-bold uppercase tracking-widest">系统状态</div>
          <div className={`text-2xl font-bold ${statusInfo.color}`}>{statusInfo.label}</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl border-l-4 border-l-slate-600">
          <div className="text-[10px] text-slate-500 mb-1 font-bold uppercase tracking-widest">活跃持仓</div>
          <div className="text-2xl font-bold text-white font-mono tracking-tighter">
            {positionCount} <span className="text-xs font-normal text-slate-500 ml-1">个标的</span>
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
            {capitalUsage.toFixed(1)}%
          </div>
        </div>
      </div>

      <PositionsTable />
    </div>
  );
}
