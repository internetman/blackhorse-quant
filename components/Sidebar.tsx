'use client';
import { LayoutDashboard, History, Settings, X } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { BlackHorseLogo } from './BlackHorseLogo';

interface SidebarProps {
  mobileMenuOpen: boolean;
  setMobileMenuOpen: (open: boolean) => void;
}

export const Sidebar = ({ mobileMenuOpen, setMobileMenuOpen }: SidebarProps) => {
  const pathname = usePathname();
  
  const navItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: '交易面板' },
    { path: '/config', icon: Settings, label: '量化策略' },
    { path: '/trades', icon: History, label: '成交日志' },
  ];
  
  return (
    <>
      {/* 移动端遮罩层 */}
      {mobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black/60 z-40 lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* 侧边导航栏 */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-50
        w-64 border-r border-slate-800 flex flex-col p-4 bg-[#0f1117] shrink-0
        transform transition-transform duration-300 ease-in-out
        ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="flex items-center justify-between mb-10 mt-2">
          <div className="flex items-center gap-3 px-2">
            <BlackHorseLogo className="w-9 h-9" />
            <h1 className="text-xl font-bold tracking-tight text-white italic">黑马量化</h1>
          </div>
          <button 
            onClick={() => setMobileMenuOpen(false)}
            className="lg:hidden p-2 text-slate-400 hover:text-white"
          >
            <X size={20} />
          </button>
        </div>
        
        <nav className="flex-1 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.path;
            return (
              <Link
                key={item.path}
                href={item.path}
                onClick={() => setMobileMenuOpen(false)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all text-sm md:text-base ${
                  isActive 
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20 font-bold' 
                    : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
                }`}
              >
                <Icon size={19} />{item.label}
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto p-4 bg-slate-900/50 rounded-xl border border-slate-800">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">节点 01 (正式环境)</span>
          </div>
          <div className="text-xs text-slate-500 font-mono italic">连接正常: 12ms</div>
        </div>
      </aside>
    </>
  );
};
