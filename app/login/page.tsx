'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { setStoredUserAndToken } from '@/lib/auth';
import { api } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('请输入用户名和密码');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const { user, token } = await api.login(username.trim(), password);
      setStoredUserAndToken(
        {
          id: user.id,
          username: user.username,
          nickname: user.nickname,
          role: user.role,
          joinedAt: user.joinedAt,
        },
        token,
      );
      router.replace('/recommendations');
    } catch (err) {
      const msg = err instanceof Error ? err.message : '登录失败';
      if (msg.includes('401')) {
        setError('用户名或密码错误');
      } else {
        setError(msg);
      }
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FAF9F7] flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-stone-900 tracking-tight">
            <span className="text-amber-700">黑马</span>自选
          </h1>
          <p className="text-stone-400 text-sm mt-2">我的关注 · AI 买卖建议与复盘</p>
        </div>

        <form onSubmit={handleLogin} className="bg-white rounded-2xl border border-stone-200/60 shadow-sm p-6 space-y-5">
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1.5">用户名</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="请输入用户名"
              autoComplete="username"
              className="w-full px-4 py-2.5 rounded-xl border border-stone-200 bg-stone-50/50 text-stone-900 text-sm
                focus:outline-none focus:ring-2 focus:ring-amber-200 focus:border-amber-300 transition-all
                placeholder:text-stone-300"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1.5">密码</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="请输入密码"
              autoComplete="current-password"
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
            {loading ? '登录中...' : '登录'}
          </button>
        </form>

        <p className="text-center text-xs text-stone-400 mt-6">
          没有账号？请联系管理员创建
        </p>
      </div>
    </div>
  );
}
