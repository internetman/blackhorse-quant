'use client';
import { Lock, ShieldAlert } from 'lucide-react';

interface ConfigSectionProps {
  title: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  children: React.ReactNode;
  risk?: boolean;
  readonly?: boolean;
}

export const ConfigSection = ({ title, icon: Icon, children, risk, readonly }: ConfigSectionProps) => (
  <div className={`bg-[#161922] border ${risk ? 'border-rose-900/50 shadow-[0_0_15px_rgba(244,63,94,0.05)]' : 'border-slate-800'} rounded-lg md:rounded-xl overflow-hidden flex flex-col h-full transition-all hover:border-slate-700`}>
    <div className={`px-3 md:px-4 py-2.5 md:py-3 border-b ${risk ? 'border-rose-900/50 bg-rose-950/20' : 'border-slate-800 bg-black/20'} flex items-center justify-between`}>
      <div className="flex items-center gap-2 min-w-0">
        <Icon size={14} className={`md:w-4 md:h-4 shrink-0 ${risk ? 'text-rose-500' : 'text-blue-400'}`} />
        <h3 className={`text-[10px] md:text-xs font-bold uppercase tracking-widest truncate ${risk ? 'text-rose-500' : 'text-slate-400'}`}>{title}</h3>
      </div>
      <div className="flex items-center gap-1.5 shrink-0">
        {readonly && <Lock size={10} className="md:w-3 md:h-3 text-slate-600" />}
        {risk && <ShieldAlert size={12} className="md:w-3.5 md:h-3.5 text-rose-500 animate-pulse" />}
      </div>
    </div>
    <div className="p-3 md:p-4 lg:p-5 space-y-3 md:space-y-4 flex-1">
      {children}
    </div>
  </div>
);
