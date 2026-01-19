'use client';
import { useState, useEffect } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { startEngine, stopEngine, setupStatusListener } from '@/lib/engine';

export const AppLayout = ({ children }: { children: React.ReactNode }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  useEffect(() => {
    // 启动引擎
    startEngine();
    
    // 设置状态监听
    const unsubscribe = setupStatusListener();
    
    return () => {
      // 清理
      stopEngine();
      unsubscribe();
    };
  }, []);
  
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
