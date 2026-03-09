'use client';

import { useEffect, useState } from 'react';
import { Settings, Users, Shield, Star, User, UserPlus, Eye, EyeOff } from 'lucide-react';
import AppShell from '@/components/layout/AppShell';
import { useAdminStore } from '@/lib/store';
import { getStoredUser, isAdmin } from '@/lib/auth';
import { api } from '@/lib/api';
import type { UserRole } from '@/lib/types';

const ROLE_CONFIG: Record<UserRole, { label: string; icon: typeof Star; color: string }> = {
  admin: { label: '管理员', icon: Shield, color: 'text-purple-700 bg-purple-50' },
  leader: { label: '意见领袖', icon: Star, color: 'text-amber-700 bg-amber-50' },
  member: { label: '成员', icon: User, color: 'text-stone-600 bg-stone-50' },
};

export default function AdminPage() {
  const [user, setUser] = useState<ReturnType<typeof getStoredUser>>(null);
  const { members, fetchMembers } = useAdminStore();

  const [showForm, setShowForm] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newNickname, setNewNickname] = useState('');
  const [newRole, setNewRole] = useState<UserRole>('member');
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState('');
  const [formSuccess, setFormSuccess] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => { setUser(getStoredUser()); fetchMembers(); }, [fetchMembers]);

  if (!isAdmin(user)) {
    return (
      <AppShell>
        <div className="flex items-center justify-center h-full py-40">
          <div className="text-center">
            <Shield size={48} className="mx-auto text-stone-200 mb-3" />
            <p className="text-stone-500 font-medium">需要管理员权限</p>
            <p className="text-xs text-stone-400 mt-1">请联系管理员获取权限</p>
          </div>
        </div>
      </AppShell>
    );
  }

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUsername.trim() || !newPassword.trim() || !newNickname.trim()) {
      setFormError('请填写完整信息');
      return;
    }

    setCreating(true);
    setFormError('');
    setFormSuccess('');

    try {
      const created = await api.createUser({
        username: newUsername.trim(),
        password: newPassword,
        nickname: newNickname.trim(),
        role: newRole,
      });
      setFormSuccess(`用户 "${created.nickname}" 创建成功`);
      setNewUsername('');
      setNewPassword('');
      setNewNickname('');
      setNewRole('member');
      setShowForm(false);
      fetchMembers();
      setTimeout(() => setFormSuccess(''), 3000);
    } catch (err) {
      const msg = err instanceof Error ? err.message : '创建失败';
      if (msg.includes('409')) {
        setFormError('该用户名已存在');
      } else {
        setFormError(msg);
      }
    } finally {
      setCreating(false);
    }
  };

  return (
    <AppShell>
      <div className="p-4 md:p-6 lg:p-8 max-w-5xl mx-auto space-y-6">
        <div>
          <h2 className="text-xl md:text-2xl font-bold text-stone-900 flex items-center gap-2">
            <Settings size={22} className="text-stone-600" />
            用户管理
          </h2>
          <p className="text-sm text-stone-400 mt-0.5">用户与权限</p>
        </div>

        {formSuccess && (
          <div className="bg-green-50 border border-green-200 text-green-700 text-sm px-4 py-3 rounded-xl">
            {formSuccess}
          </div>
        )}

        {/* Add user */}
        <div className="bg-white rounded-2xl border border-stone-200/60 shadow-sm">
          <div className="p-5 border-b border-stone-100 flex items-center justify-between">
            <h3 className="text-sm font-medium text-stone-700 flex items-center gap-2">
              <UserPlus size={16} />
              添加用户
            </h3>
            <button
              onClick={() => { setShowForm(!showForm); setFormError(''); }}
              className="text-xs text-amber-700 hover:text-amber-800 font-medium"
            >
              {showForm ? '收起' : '展开'}
            </button>
          </div>

          {showForm && (
            <form onSubmit={handleCreateUser} className="p-5 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-1">用户名</label>
                  <input
                    type="text"
                    value={newUsername}
                    onChange={(e) => setNewUsername(e.target.value)}
                    placeholder="登录用的用户名"
                    className="w-full px-4 py-2.5 rounded-xl border border-stone-200 bg-stone-50/50 text-stone-900 text-sm
                      focus:outline-none focus:ring-2 focus:ring-amber-200 focus:border-amber-300 transition-all
                      placeholder:text-stone-300"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-1">密码</label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="初始密码"
                      className="w-full px-4 py-2.5 pr-10 rounded-xl border border-stone-200 bg-stone-50/50 text-stone-900 text-sm
                        focus:outline-none focus:ring-2 focus:ring-amber-200 focus:border-amber-300 transition-all
                        placeholder:text-stone-300"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-stone-400 hover:text-stone-600"
                    >
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-1">昵称</label>
                  <input
                    type="text"
                    value={newNickname}
                    onChange={(e) => setNewNickname(e.target.value)}
                    placeholder="在圈内显示的名字"
                    className="w-full px-4 py-2.5 rounded-xl border border-stone-200 bg-stone-50/50 text-stone-900 text-sm
                      focus:outline-none focus:ring-2 focus:ring-amber-200 focus:border-amber-300 transition-all
                      placeholder:text-stone-300"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-1">角色</label>
                  <select
                    value={newRole}
                    onChange={(e) => setNewRole(e.target.value as UserRole)}
                    className="w-full px-4 py-2.5 rounded-xl border border-stone-200 bg-stone-50/50 text-stone-900 text-sm
                      focus:outline-none focus:ring-2 focus:ring-amber-200 focus:border-amber-300 transition-all"
                  >
                    <option value="member">成员</option>
                    <option value="leader">意见领袖</option>
                    <option value="admin">管理员</option>
                  </select>
                </div>
              </div>

              {formError && (
                <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{formError}</p>
              )}

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={creating}
                  className="px-6 py-2.5 rounded-xl bg-amber-700 text-white text-sm font-medium
                    hover:bg-amber-800 active:scale-[0.98] transition-all disabled:opacity-50"
                >
                  {creating ? '创建中...' : '创建用户'}
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Members */}
        <div className="bg-white rounded-2xl border border-stone-200/60 shadow-sm">
          <div className="p-5 border-b border-stone-100 flex items-center justify-between">
            <h3 className="text-sm font-medium text-stone-700 flex items-center gap-2">
              <Users size={16} />
              成员列表
            </h3>
            <span className="text-xs text-stone-400">{members.length} 人</span>
          </div>
          <div className="divide-y divide-stone-100">
            {members.map((member) => {
              const roleConfig = ROLE_CONFIG[member.role];
              const RoleIcon = roleConfig.icon;
              return (
                <div key={member.id} className="px-5 py-3.5 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-stone-100 flex items-center justify-center text-stone-600 text-sm font-medium">
                      {member.nickname.charAt(0)}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-stone-900">{member.nickname}</p>
                      <p className="text-xs text-stone-400">
                        @{member.username || '—'} · 加入于 {member.joinedAt}
                      </p>
                    </div>
                  </div>
                  <span className={`inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full font-medium ${roleConfig.color}`}>
                    <RoleIcon size={12} />
                    {roleConfig.label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
