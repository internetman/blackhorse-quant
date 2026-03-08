'use client';

import { useEffect, useState } from 'react';
import { Settings, Users, Copy, Check, Shield, Star, User } from 'lucide-react';
import AppShell from '@/components/layout/AppShell';
import { useCircleStore } from '@/lib/store';
import { getStoredUser, isAdmin } from '@/lib/auth';
import type { UserRole } from '@/lib/types';

const ROLE_CONFIG: Record<UserRole, { label: string; icon: typeof Star; color: string }> = {
  admin: { label: '管理员', icon: Shield, color: 'text-purple-700 bg-purple-50' },
  leader: { label: '意见领袖', icon: Star, color: 'text-amber-700 bg-amber-50' },
  member: { label: '成员', icon: User, color: 'text-stone-600 bg-stone-50' },
};

export default function AdminPage() {
  const [user, setUser] = useState<ReturnType<typeof getStoredUser>>(null);
  const { circle, members, fetchMembers } = useCircleStore();
  const [copied, setCopied] = useState(false);

  useEffect(() => { setUser(getStoredUser()); fetchMembers(); }, [fetchMembers]);

  if (!isAdmin(user)) {
    return (
      <AppShell>
        <div className="flex items-center justify-center h-full py-40">
          <div className="text-center">
            <Shield size={48} className="mx-auto text-stone-200 mb-3" />
            <p className="text-stone-500 font-medium">需要管理员权限</p>
            <p className="text-xs text-stone-400 mt-1">请联系圈主获取管理权限</p>
          </div>
        </div>
      </AppShell>
    );
  }

  const copyInviteCode = () => {
    if (circle?.inviteCode) {
      navigator.clipboard.writeText(circle.inviteCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <AppShell>
      <div className="p-4 md:p-6 lg:p-8 max-w-5xl mx-auto space-y-6">
        <div>
          <h2 className="text-xl md:text-2xl font-bold text-stone-900 flex items-center gap-2">
            <Settings size={22} className="text-stone-600" />
            圈子管理
          </h2>
          <p className="text-sm text-stone-400 mt-0.5">{circle?.name || '黑马圈'}</p>
        </div>

        {/* Invite code */}
        <div className="bg-white rounded-2xl border border-stone-200/60 shadow-sm p-5">
          <h3 className="text-sm font-medium text-stone-700 mb-3">邀请码</h3>
          <div className="flex items-center gap-3">
            <code className="flex-1 px-4 py-3 bg-stone-50 rounded-xl text-lg font-mono font-bold text-stone-900 tracking-widest text-center border border-stone-200">
              {circle?.inviteCode || '---'}
            </code>
            <button
              onClick={copyInviteCode}
              className="px-4 py-3 rounded-xl bg-amber-700 text-white hover:bg-amber-800 transition-colors flex items-center gap-1.5 text-sm font-medium"
            >
              {copied ? <Check size={16} /> : <Copy size={16} />}
              {copied ? '已复制' : '复制'}
            </button>
          </div>
          <p className="text-xs text-stone-400 mt-2">将此邀请码分享给你想邀请的朋友</p>
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
                      <p className="text-xs text-stone-400">加入于 {member.joinedAt}</p>
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
