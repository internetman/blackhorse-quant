'use client';
import { useState } from 'react';
import { createPortal } from 'react-dom';
import { Play, Pause, XCircle, Menu, AlertTriangle } from 'lucide-react';
import { useStore } from '@/lib/store';
import { BlackHorseLogo } from './BlackHorseLogo';

interface HeaderProps {
  setMobileMenuOpen: (open: boolean) => void;
}

export const Header = ({ setMobileMenuOpen }: HeaderProps) => {
  const sysStatus = useStore((state) => state.sysStatus);
  const setSysStatus = useStore((state) => state.setSysStatus);
  const stats = useStore((state) => state.stats);
  const todayPnl = stats?.todayPnl ?? 0;
  const [showKillConfirm, setShowKillConfirm] = useState(false);
  
  const getStatusInfo = (status: string) => {
    switch(status) {
      case 'running': return { label: '运行中', color: 'text-rose-500', desc: '策略监控中：信号持续生成并报单' };
      case 'paused': return { label: '已暂停', color: 'text-amber-500', desc: '挂起：保留持仓，不再生成新订单' };
      case 'kill': return { label: '强平停止', color: 'text-emerald-500', desc: '停止：进入人工接管状态' };
      default: return { label: '', color: '', desc: '' };
    }
  };
  
  return (
    <header className="h-16 md:h-20 border-b border-slate-800 flex items-center justify-between px-4 md:px-8 bg-[#0f1117]/80 backdrop-blur-md z-10 shrink-0">
      {/* 移动端菜单按钮 */}
      <button 
        onClick={() => setMobileMenuOpen(true)}
        className="lg:hidden p-2 text-slate-400 hover:text-white"
      >
        <Menu size={24} />
      </button>

      <div className="flex items-center gap-4 md:gap-8 flex-1">
        <div className="flex flex-col gap-1.5">
          <div className="flex gap-1 md:gap-2 bg-black/40 p-1 md:p-1.5 rounded-xl border border-slate-800">
            <button 
              onClick={() => setSysStatus('running')} 
              className={`p-1.5 md:p-2 rounded-lg transition-all touch-manipulation ${sysStatus === 'running' ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-600/30' : 'text-slate-600 hover:text-slate-400'}`}
            >
              <Play size={16} className="md:w-[18px] md:h-[18px]" fill="currentColor" />
            </button>
            <button 
              onClick={() => setSysStatus('paused')} 
              className={`p-1.5 md:p-2 rounded-lg transition-all touch-manipulation ${sysStatus === 'paused' ? 'bg-amber-500 text-white shadow-lg shadow-amber-500/30' : 'text-slate-600 hover:text-slate-400'}`}
            >
              <Pause size={16} className="md:w-[18px] md:h-[18px]" fill="currentColor" />
            </button>
            <button 
              onClick={() => setShowKillConfirm(true)} 
              className={`p-1.5 md:p-2 rounded-lg transition-all touch-manipulation ${sysStatus === 'kill' ? 'bg-rose-600 text-white shadow-lg shadow-rose-600/30' : 'text-slate-600 hover:text-slate-400'}`}
              title="强平停止（仅停止策略，不会清空持仓）"
            >
              <XCircle size={16} className="md:w-[18px] md:h-[18px]" fill="currentColor" />
            </button>
          </div>
          <p className="text-[9px] md:text-[10px] text-slate-500 font-medium italic pl-1 hidden md:block">
            {getStatusInfo(sysStatus).desc}
          </p>
        </div>
        <div className="h-8 md:h-10 w-px bg-slate-800/50 hidden sm:block"></div>
        <div className="flex flex-col min-w-0">
          <span className="text-[9px] md:text-[10px] text-slate-500 font-bold uppercase tracking-widest text-rose-500/80">
            今日盈亏
          </span>
          <span className="text-lg md:text-xl font-bold font-mono text-rose-500 tracking-tight truncate">
            {todayPnl >= 0 ? '+' : ''}¥{todayPnl.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3 md:gap-5">
        <div className="text-right hidden lg:block">
          <div className="text-xs text-slate-500 font-bold uppercase tracking-widest opacity-60">实盘账户 ID</div>
          <div className="text-sm font-bold text-white tracking-wider font-mono">¥1,242,500.00</div>
        </div>
        <div className="w-8 h-8 md:w-10 md:h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center shadow-lg overflow-hidden p-1.5 shrink-0">
          <BlackHorseLogo className="w-full h-full" />
        </div>
      </div>

      {/* 强平停止确认：用 Portal 挂到 body，避免受 header 的 backdrop-blur 影响导致 fixed 定位错位 */}
      {showKillConfirm && typeof document !== 'undefined' && createPortal(
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60" role="dialog" aria-modal="true" aria-labelledby="kill-confirm-title">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl max-w-sm w-full p-6 space-y-4">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center">
                <AlertTriangle className="text-amber-500" size={20} />
              </div>
              <div>
                <h3 id="kill-confirm-title" className="text-lg font-bold text-white">切换到强平停止？</h3>
                <p className="text-sm text-slate-400 mt-1">仅停止策略、进入人工接管，<strong className="text-slate-300">不会清空持仓</strong>。若要清空持仓，请使用交易面板中的「全仓紧急停止并平仓」。</p>
              </div>
            </div>
            <div className="flex gap-3 justify-end">
              <button
                type="button"
                onClick={() => setShowKillConfirm(false)}
                className="px-4 py-2 rounded-xl border border-slate-600 text-slate-300 hover:bg-slate-800 transition-colors"
              >
                取消
              </button>
              <button
                type="button"
                onClick={() => { setSysStatus('kill'); setShowKillConfirm(false); }}
                className="px-4 py-2 rounded-xl bg-rose-600 text-white font-medium hover:bg-rose-500 transition-colors"
              >
                确认切换
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </header>
  );
};
