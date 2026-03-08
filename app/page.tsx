'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getStoredUser } from '@/lib/auth';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const user = getStoredUser();
    router.replace(user ? '/recommendations' : '/login');
  }, [router]);

  return (
    <div className="flex items-center justify-center h-screen bg-[#FAF9F7]">
      <div className="animate-pulse text-stone-400 text-sm">加载中...</div>
    </div>
  );
}
