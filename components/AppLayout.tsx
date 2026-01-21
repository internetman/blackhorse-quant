'use client';
import { useState, useEffect } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { useStore } from '@/lib/store';

export const AppLayout = ({ children }: { children: React.ReactNode }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const fetchStatus = useStore((state) => state.fetchStatus);
  
  useEffect(() => {
    // 初始化时获取状态
    fetchStatus();
  }, [fetchStatus]);
  
  return (
    <div className="flex h-screen bg-[#0b0d11] text-slate-200 overflow-hidden font-sans text-sm selection:bg-blue-500/30">
      <Sidebar mobileMenuOpen={mobileMenuOpen} setMobileMenuOpen={setMobileMenuOpen} />
      
      <main className="flex-1 flex flex-col overflow-hidden lg:ml-0">
        <Header setMobileMenuOpen={setMobileMenuOpen} />
        
        <div className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 space-y-6 md:space-y-8 bg-[#0b0d11]">
          {children}
        </div>
      </main>
    </div>
  );
};
