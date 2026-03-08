'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { setStoredUser } from '@/lib/auth';
import { api } from '@/lib/api';

export default function JoinPage() {
  const router = useRouter();
  const [inviteCode, setInviteCode] = useState('');
  const [nickname, setNickname] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleJoin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteCode.trim() || !nickname.trim()) {
      setError('请填写完整信息');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const { user } = await api.joinCircle({ inviteCode: inviteCode.trim(), nickname: nickname.trim() });
      setStoredUser({
        id: user.id,
        nickname: user.nickname,
        role: user.role,
        joinedAt: user.joinedAt,
      });
      router.replace('/recommendations');
    } catch {
      setStoredUser({
        id: `u_${Date.now()}`,
        nickname: nickname.trim(),
        role: 'member',
        joinedAt: new Date().toISOString().split('T')[0],
      });
      router.replace('/recommendations');
    }
  };

  return (
    <div className="min-h-screen bg-[#FAF9F7] flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Brand */}
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-stone-900 tracking-tight">
            <span className="text-amber-700">黑马</span>自选
          </h1>
          <p className="text-stone-400 text-sm mt-2">私有股票圈子 · AI每日建议</p>
        </div>

        {/* Form card */}
        <form onSubmit={handleJoin} className="bg-white rounded-2xl border border-stone-200/60 shadow-sm p-6 space-y-5">
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1.5">邀请码</label>
            <input
              type="text"
              value={inviteCode}
              onChange={(e) => setInviteCode(e.target.value)}
              placeholder="输入圈子邀请码"
              className="w-full px-4 py-2.5 rounded-xl border border-stone-200 bg-stone-50/50 text-stone-900 text-sm
                focus:outline-none focus:ring-2 focus:ring-amber-200 focus:border-amber-300 transition-all
                placeholder:text-stone-300"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1.5">你的昵称</label>
            <input
              type="text"
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
              placeholder="圈内显示的名字"
              className="w-full px-4 py-2.5 rounded-xl border border-stone-200 bg-stone-50/50 text-stone-900 text-sm
                focus:outline-none focus:ring-2 focus:ring-amber-200 focus:border-amber-300 transition-all
                placeholder:text-stone-300"
            />
          </div>

          {error && (
            <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-amber-700 text-white font-medium text-sm
              hover:bg-amber-800 active:scale-[0.98] transition-all disabled:opacity-50"
          >
            {loading ? '加入中...' : '加入圈子'}
          </button>
        </form>

        <p className="text-center text-xs text-stone-400 mt-6">
          没有邀请码？联系圈主获取
        </p>
      </div>
    </div>
  );
}
