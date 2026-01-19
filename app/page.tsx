'use client';
import React, { useState } from 'react';
import { 
  LayoutDashboard, 
  History, 
  Settings, 
  Play, 
  Pause, 
  XCircle, 
  TrendingUp, 
  Activity, 
  ShieldCheck, 
  Save, 
  ArrowUpRight, 
  ArrowDownLeft,
  Info,
  AlertTriangle,
  CheckCircle2,
  FileCode,
  ExternalLink,
  Lock,
  Layers,
  SlidersHorizontal,
  Search,
  Target,
  Zap,
  Briefcase,
  GanttChart,
  ClipboardCheck,
  ShieldAlert,
  Clock,
  Eye,
  FileSearch,
  ZapOff
} from 'lucide-react';

// --- 标志组件 ---
const BlackHorseLogo = ({ className }: { className?: string }) => {
  const [hasError, setHasError] = useState(false);
  return (
    <div className={`${className} flex items-center justify-center overflow-hidden`}>
      {!hasError ? (
        <img 
          src="/logo.png" 
          alt="黑马量化" 
          className="w-full h-full object-contain"
          onError={() => setHasError(true)}
        />
      ) : (
        <span className="text-blue-500 font-black text-xl italic leading-none">H</span>
      )}
    </div>
  );
};

// --- 模拟数据 (A股配色: 红涨绿跌) ---
const MOCK_POSITIONS = [
  { id: 1, asset: '贵州茅台 (600519)', side: '多', amount: '200', entryPrice: '1,650.00', currentPrice: '1,682.50', pnl: '+1.97%', pnlValue: '+¥6,500' },
  { id: 2, asset: '宁德时代 (300750)', side: '多', amount: '1500', entryPrice: '158.20', currentPrice: '162.10', pnl: '+2.46%', pnlValue: '+¥5,850' },
  { id: 3, asset: '隆基绿能 (601012)', side: '多', amount: '2000', entryPrice: '22.50', currentPrice: '20.10', pnl: '-10.67%', pnlValue: '-¥4,800' },
  { id: 4, asset: '比亚迪 (002594)', side: '空', amount: '800', entryPrice: '210.50', currentPrice: '205.80', pnl: '+2.23%', pnlValue: '+¥3,760' },
];

const MOCK_TRADES = [
  { id: 101, time: '14:20:01', asset: '招商银行 (600036)', side: '买入', price: '32.50', status: '正常成交', reason: '均线金叉信号触发' },
  { id: 102, time: '13:45:12', asset: '中国平安 (601318)', side: '卖出', price: '41.80', status: '风控拒绝', reason: 'RSI 超买信号' }
];

// --- 页面通用 UI 组件 ---

const ConfigSection = ({ title, icon: Icon, children, risk, readonly }: { title: string; icon: React.ComponentType<{ size?: number; className?: string }>; children: React.ReactNode; risk?: boolean; readonly?: boolean }) => (
  <div className={`bg-[#161922] border ${risk ? 'border-rose-900/50 shadow-[0_0_15px_rgba(244,63,94,0.05)]' : 'border-slate-800'} rounded-xl overflow-hidden flex flex-col h-full transition-all hover:border-slate-700`}>
    <div className={`px-4 py-3 border-b ${risk ? 'border-rose-900/50 bg-rose-950/20' : 'border-slate-800 bg-black/20'} flex items-center justify-between`}>
      <div className="flex items-center gap-2">
        <Icon size={16} className={risk ? 'text-rose-500' : 'text-blue-400'} />
        <h3 className={`text-xs font-bold uppercase tracking-widest ${risk ? 'text-rose-500' : 'text-slate-400'}`}>{title}</h3>
      </div>
      {readonly && <Lock size={12} className="text-slate-600" />}
      {risk && <ShieldAlert size={14} className="text-rose-500 animate-pulse" />}
    </div>
    <div className="p-5 space-y-4 flex-1">
      {children}
    </div>
  </div>
);

const FormField = ({ label, description, children, risk }: { label: string; description?: string; children: React.ReactNode; risk?: boolean }) => (
  <div className="space-y-1.5">
    <div className="flex justify-between items-center">
      <label className="text-[10px] font-bold text-slate-500 uppercase tracking-tighter">{label}</label>
      {risk && <span className="text-[9px] text-rose-500 font-bold px-1 rounded border border-rose-500/30">高风险</span>}
    </div>
    {children}
    {description && <p className="text-[9px] text-slate-600 italic leading-none">{description}</p>}
  </div>
);

const Switch = ({ checked, label }: { checked: boolean; label: string }) => (
  <div className="flex items-center justify-between group cursor-pointer">
    <span className="text-[11px] text-slate-400 font-medium group-hover:text-slate-200 transition-colors">{label}</span>
    <div className={`w-8 h-4 rounded-full p-0.5 transition-colors ${checked ? 'bg-blue-600' : 'bg-slate-700'}`}>
      <div className={`w-3 h-3 bg-white rounded-full transition-transform ${checked ? 'translate-x-4' : 'translate-x-0'}`} />
    </div>
  </div>
);

// --- 主程序 ---
export default function App() {
  const [activeTab, setActiveTab] = useState('config'); 
  const [sysStatus, setSysStatus] = useState('running');
  const [riskConfirmed, setRiskConfirmed] = useState(false);

  // 状态信息映射
  const getStatusInfo = (status: string) => {
    switch(status) {
      case 'running': return { label: '运行中', color: 'text-rose-500', desc: '策略监控中：信号持续生成并报单' };
      case 'paused': return { label: '已暂停', color: 'text-amber-500', desc: '挂起：保留持仓，不再生成新订单' };
      case 'kill': return { label: '强平停止', color: 'text-emerald-500', desc: '停止：进入人工接管状态' };
      default: return {};
    }
  };

  return (
    <div className="flex h-screen bg-[#0b0d11] text-slate-200 overflow-hidden font-sans text-sm selection:bg-blue-500/30">
      
      {/* 侧边导航栏 */}
      <aside className="w-64 border-r border-slate-800 flex flex-col p-4 bg-[#0f1117] shrink-0">
        <div className="flex items-center gap-3 px-2 mb-10 mt-2">
          <BlackHorseLogo className="w-9 h-9" />
          <h1 className="text-xl font-bold tracking-tight text-white italic">黑马量化</h1>
        </div>
        
        <nav className="flex-1 space-y-1">
          <button onClick={() => setActiveTab('dashboard')} className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${activeTab === 'dashboard' ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20 font-bold' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'}`}>
            <LayoutDashboard size={19} />交易面板
          </button>
          <button onClick={() => setActiveTab('config')} className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${activeTab === 'config' ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20 font-bold' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'}`}>
            <Settings size={19} />量化策略
          </button>
          <button onClick={() => setActiveTab('trades')} className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${activeTab === 'trades' ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20 font-bold' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'}`}>
            <History size={19} />成交日志
          </button>
        </nav>

        <div className="mt-auto p-4 bg-slate-900/50 rounded-xl border border-slate-800">
          <div className="flex items-center gap-2 mb-2">
             <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
             <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">节点 01 (正式环境)</span>
          </div>
          <div className="text-xs text-slate-500 font-mono italic">连接正常: 12ms</div>
        </div>
      </aside>

      {/* 主体区域 */}
      <main className="flex-1 flex flex-col overflow-hidden">
        
        {/* 顶部标题栏 */}
        <header className="h-20 border-b border-slate-800 flex items-center justify-between px-8 bg-[#0f1117]/80 backdrop-blur-md z-10 shrink-0">
          <div className="flex items-center gap-8">
            <div className="flex flex-col gap-1.5">
              <div className="flex gap-2 bg-black/40 p-1.5 rounded-xl border border-slate-800">
                <button onClick={() => setSysStatus('running')} className={`p-2 rounded-lg transition-all ${sysStatus === 'running' ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-600/30' : 'text-slate-600 hover:text-slate-400'}`}><Play size={18} fill="currentColor" /></button>
                <button onClick={() => setSysStatus('paused')} className={`p-2 rounded-lg transition-all ${sysStatus === 'paused' ? 'bg-amber-500 text-white shadow-lg shadow-amber-500/30' : 'text-slate-600 hover:text-slate-400'}`}><Pause size={18} fill="currentColor" /></button>
                <button onClick={() => setSysStatus('kill')} className={`p-2 rounded-lg transition-all ${sysStatus === 'kill' ? 'bg-rose-600 text-white shadow-lg shadow-rose-600/30' : 'text-slate-600 hover:text-slate-400'}`}><XCircle size={18} fill="currentColor" /></button>
              </div>
              <p className="text-[10px] text-slate-500 font-medium italic pl-1">{getStatusInfo(sysStatus).desc}</p>
            </div>
            <div className="h-10 w-px bg-slate-800/50"></div>
            <div className="flex flex-col">
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest text-rose-500/80">今日盈亏实时统计</span>
              <span className="text-xl font-bold font-mono text-rose-500 tracking-tight">+¥58,240.42</span>
            </div>
          </div>

          <div className="flex items-center gap-5">
             <div className="text-right hidden md:block">
               <div className="text-xs text-slate-500 font-bold uppercase tracking-widest opacity-60">实盘账户 ID</div>
               <div className="text-sm font-bold text-white tracking-wider font-mono">¥1,242,500.00</div>
             </div>
             <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center shadow-lg overflow-hidden p-1.5">
                <BlackHorseLogo className="w-full h-full" />
             </div>
          </div>
        </header>

        {/* 动态内容区 */}
        <div className="flex-1 overflow-y-auto p-8 space-y-8 bg-[#0b0d11]">
          
          {/* 量化策略面板 */}
          {activeTab === 'config' && (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-10 max-w-7xl mx-auto">
              
              <div className="flex items-center justify-between border-b border-slate-800 pb-8">
                <div>
                  <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                    策略参数中心 <span className="text-[10px] font-mono bg-blue-500/10 text-blue-500 px-2 py-0.5 rounded-full border border-blue-500/20">v3.2.0 稳定版</span>
                  </h2>
                  <p className="text-slate-500 mt-1.5 text-xs font-medium uppercase tracking-[0.1em]">支持参数热重载：所有变更将在下一个行情切片到来时生效</p>
                </div>
                <div className="flex flex-col items-end gap-3">
                  <div className="flex items-center gap-3 bg-slate-900 border border-slate-800 px-4 py-2 rounded-2xl shadow-inner border-l-4 border-l-rose-500">
                    <input type="checkbox" id="riskCheck" checked={riskConfirmed} onChange={(e) => setRiskConfirmed(e.target.checked)} className="w-4 h-4 rounded text-blue-600 bg-black border-slate-700 focus:ring-0" />
                    <label htmlFor="riskCheck" className="text-xs text-rose-100 font-bold cursor-pointer select-none">我已知晓此变更将立即影响实盘，自担交易盈亏</label>
                  </div>
                  <button 
                    disabled={!riskConfirmed}
                    onClick={() => { alert("部署指令已发送，节点热重载中..."); setRiskConfirmed(false); }}
                    className={`flex items-center gap-2 px-10 py-3.5 rounded-2xl font-bold transition-all transform active:scale-95 shadow-xl ${riskConfirmed ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-blue-600/40' : 'bg-slate-800 text-slate-500 cursor-not-allowed opacity-50'}`}
                  >
                    <Save size={18} /> 同步至实盘环境
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                
                {/* 1. 策略基础信息 */}
                <ConfigSection title="策略基础信息" icon={Lock} readonly>
                  <div className="space-y-4 opacity-75">
                    <FormField label="策略名称"><div className="bg-black/30 p-2 rounded border border-slate-800 text-slate-300 font-mono text-[10px]">A股波动率均衡对冲策略</div></FormField>
                    <div className="grid grid-cols-2 gap-3">
                      <FormField label="策略类型"><div className="bg-black/30 p-2 rounded border border-slate-800 text-slate-300 font-mono text-[9px]">波动率套利</div></FormField>
                      <FormField label="适用市场"><div className="bg-black/30 p-2 rounded border border-slate-800 text-slate-300 font-mono text-[9px]">沪深 A 股</div></FormField>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <FormField label="版本识别"><div className="bg-blue-500/10 p-2 rounded border border-blue-500/20 text-blue-400 font-mono text-[9px]">v3.2.0 Stable</div></FormField>
                      <FormField label="运行环境"><div className="bg-rose-500/10 p-2 rounded border border-rose-500/20 text-rose-400 font-mono text-[9px]">实盘环境</div></FormField>
                    </div>
                    <FormField label="维护团队"><div className="bg-black/30 p-2 rounded border border-slate-800 text-slate-300 font-mono text-[10px]">黑马量化核心研发组</div></FormField>
                  </div>
                </ConfigSection>

                {/* 2. 交易标的与范围 */}
                <ConfigSection title="交易标的范围" icon={Target}>
                  <FormField label="证券池来源">
                    <select className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white outline-none">
                      <option>全市场活跃股</option>
                      <option>沪深300成分股</option>
                      <option>中证500成分股</option>
                      <option>自定义关注池</option>
                    </select>
                  </FormField>
                  <div className="grid grid-cols-2 gap-3">
                    <FormField label="最大同时持仓数">
                      <input type="number" defaultValue={30} className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white font-mono" />
                    </FormField>
                    <FormField label="成交额下限(万)">
                      <input type="number" defaultValue={1000} className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white font-mono" />
                    </FormField>
                  </div>
                  <div className="space-y-2.5 pt-2">
                    <Switch checked={true} label="自动排除停牌标的" />
                    <Switch checked={true} label="自动排除 ST / *ST" />
                    <Switch checked={false} label="允许同标的反向操作" />
                  </div>
                </ConfigSection>

                {/* 3. 信号生成参数 */}
                <ConfigSection title="信号引擎参数" icon={Zap}>
                  <FormField label="核心指标逻辑">
                    <select className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white">
                      <option>EMA + ATR 趋势波动</option>
                      <option>RSI 背离检测</option>
                      <option>多因子打分模型</option>
                    </select>
                  </FormField>
                  <div className="grid grid-cols-2 gap-3">
                    <FormField label="数据回看周期">
                      <input type="number" defaultValue={20} className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white font-mono" />
                    </FormField>
                    <FormField label="信号触发阈值">
                      <input type="number" step="0.1" defaultValue={1.5} className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white font-mono" />
                    </FormField>
                  </div>
                  <FormField label="信号确认(连续次数)">
                    <input type="range" min="1" max="5" defaultValue={3} className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500" />
                  </FormField>
                  <FormField label="开仓冷却时间(分)">
                    <input type="number" defaultValue={15} className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white font-mono" />
                  </FormField>
                </ConfigSection>

                {/* 4. 仓位与资金分配 */}
                <ConfigSection title="仓位与资金分配" icon={Briefcase}>
                  <FormField label="资金分配模式">
                    <select className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white font-bold">
                      <option>风险平价分配</option>
                      <option>单标的等权重</option>
                      <option>基于波动率调整</option>
                    </select>
                  </FormField>
                  <FormField label="单笔最大开仓比例 (%)">
                    <div className="flex items-center gap-3">
                      <input type="range" min="1" max="50" defaultValue={10} className="flex-1 h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500" />
                      <span className="text-[10px] font-mono text-blue-400">10%</span>
                    </div>
                  </FormField>
                  <div className="space-y-2.5 pt-4 border-t border-slate-800/50">
                    <Switch checked={false} label="允许盘中动态加仓" />
                    <FormField label="最大允许加仓次数">
                      <input type="number" defaultValue={0} className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white font-mono opacity-50" disabled />
                    </FormField>
                  </div>
                </ConfigSection>

                {/* 5. 交易执行策略 */}
                <ConfigSection title="执行算法设置" icon={GanttChart}>
                  <FormField label="引擎调度频率">
                    <select className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white">
                      <option>1 分钟 (极速响应)</option>
                      <option>5 分钟 (稳健平衡)</option>
                      <option>15 分钟</option>
                    </select>
                  </FormField>
                  <div className="grid grid-cols-2 gap-3">
                    <FormField label="单笔委托上限(手)">
                      <input type="number" defaultValue={500} className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white font-mono" />
                    </FormField>
                    <FormField label="滑点容忍阈值(%)">
                      <input type="number" step="0.01" defaultValue={0.05} className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white font-mono" />
                    </FormField>
                  </div>
                  <div className="space-y-2.5 pt-2">
                    <Switch checked={true} label="开启智能拆单算法" />
                    <Switch checked={true} label="支持 T+0 回转交易" />
                    <Switch checked={false} label="自动价格追踪补单" />
                  </div>
                </ConfigSection>

                {/* 6. 风控参数设置 */}
                <ConfigSection title="风险控制参数" icon={ShieldAlert} risk>
                  <div className="grid grid-cols-2 gap-3">
                    <FormField label="日内最大回撤(%)" risk>
                      <input type="number" step="0.1" defaultValue={2.5} className="w-full bg-[#1e1418] border border-rose-900 rounded-lg p-2 text-xs text-rose-500 font-bold" />
                    </FormField>
                    <FormField label="全局预警平仓线(%)" risk>
                      <input type="number" step="0.1" defaultValue={8.0} className="w-full bg-[#1e1418] border border-rose-900 rounded-lg p-2 text-xs text-rose-500 font-bold" />
                    </FormField>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <FormField label="单股持仓比例上限(%)" risk>
                      <input type="number" defaultValue={15} className="w-full bg-[#1e1418] border border-rose-900 rounded-lg p-2 text-xs text-rose-500" />
                    </FormField>
                    <FormField label="日交易总笔数限制" risk>
                      <input type="number" defaultValue={50} className="w-full bg-[#1e1418] border border-rose-900 rounded-lg p-2 text-xs text-rose-500" />
                    </FormField>
                  </div>
                  <div className="space-y-2.5 pt-2">
                    <Switch checked={true} label="连续亏损自动熔断逻辑" />
                    <button className="w-full bg-rose-600/20 hover:bg-rose-600/40 text-rose-500 border border-rose-600/30 py-2 rounded-lg text-[10px] font-black tracking-widest uppercase flex items-center justify-center gap-2">
                      <ZapOff size={12} /> 一键停止运行并强平
                    </button>
                  </div>
                </ConfigSection>

                {/* 7. 交易行为约束 */}
                <ConfigSection title="交易行为约束" icon={Clock}>
                  <div className="grid grid-cols-2 gap-3">
                    <FormField label="开盘禁交时长(分)">
                      <input type="number" defaultValue={15} className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white font-mono" />
                    </FormField>
                    <FormField label="尾盘停止开仓(分)">
                      <input type="number" defaultValue={10} className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white font-mono" />
                    </FormField>
                  </div>
                  <div className="space-y-3 pt-4 border-t border-slate-800/50">
                    <div className="flex items-center justify-between"><span className="text-[10px] text-slate-400 uppercase font-bold tracking-tight">禁止高频短时间反向</span><input type="checkbox" defaultChecked className="w-4 h-4 rounded bg-slate-800 border-slate-700" /></div>
                    <div className="flex items-center justify-between"><span className="text-[10px] text-slate-400 uppercase font-bold tracking-tight">禁止盘中极端放量追涨</span><input type="checkbox" defaultChecked className="w-4 h-4 rounded bg-slate-800 border-slate-700" /></div>
                    <div className="flex items-center justify-between"><span className="text-[10px] text-slate-400 uppercase font-bold tracking-tight">禁止大幅跳空开盘下单</span><input type="checkbox" className="w-4 h-4 rounded bg-slate-800 border-slate-700" /></div>
                  </div>
                </ConfigSection>

                {/* 8. 审计与快照设置 */}
                <ConfigSection title="审计与快照设置" icon={ClipboardCheck}>
                  <div className="space-y-4">
                    <Switch checked={true} label="记录每一根 K 线信号快照" />
                    <Switch checked={true} label="记录每笔风控拒绝判定细节" />
                    <Switch checked={false} label="启用实时仿真回放数据流" />
                    <Switch checked={true} label="收盘自动导出审计报告" />
                  </div>
                  <div className="pt-6 mt-6 border-t border-slate-800">
                    <div className="flex items-center justify-between opacity-50">
                      <span className="text-[10px] text-slate-500 font-bold uppercase">日志合规存储期</span>
                      <span className="text-[10px] text-slate-200 font-mono tracking-widest">90 天</span>
                    </div>
                  </div>
                  <button className="w-full bg-slate-800 hover:bg-slate-700 text-slate-300 py-2 rounded-lg text-[10px] font-bold mt-4 flex items-center justify-center gap-2">
                    <FileSearch size={14} /> 查看当前配置审计快照
                  </button>
                </ConfigSection>

              </div>
            </div>
          )}

          {/* 其余页面保持原样... */}
          {activeTab === 'dashboard' && (
            <div className="animate-in fade-in duration-700 space-y-8 max-w-7xl mx-auto">
               <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl border-l-4 border-l-blue-500">
                    <div className="text-[10px] text-slate-500 mb-1 font-bold uppercase tracking-widest">系统状态</div>
                    <div className={`text-2xl font-bold ${getStatusInfo(sysStatus).color}`}>{getStatusInfo(sysStatus).label}</div>
                  </div>
                  <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl border-l-4 border-l-slate-600">
                    <div className="text-[10px] text-slate-500 mb-1 font-bold uppercase tracking-widest">活跃持仓</div>
                    <div className="text-2xl font-bold text-white font-mono tracking-tighter">4 <span className="text-xs font-normal text-slate-500 ml-1">个标的</span></div>
                  </div>
                  <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl border-l-4 border-l-rose-500">
                    <div className="text-[10px] text-slate-500 mb-1 font-bold uppercase tracking-widest text-rose-500/80">未实现盈亏</div>
                    <div className="text-2xl font-bold text-rose-500 font-mono tracking-tighter">+¥12,402</div>
                  </div>
                  <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl border-l-4 border-l-blue-400">
                    <div className="text-[10px] text-slate-500 mb-1 font-bold uppercase tracking-widest">资金占用率</div>
                    <div className="text-2xl font-bold text-blue-400 font-mono tracking-tighter">65.4%</div>
                  </div>
               </div>

               <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
                <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center bg-black/10 font-bold">
                  <h3 className="text-white text-xs uppercase tracking-widest flex items-center gap-2"><Briefcase size={14}/> 实时股票持仓列表 (T+0)</h3>
                  <button className="text-[10px] text-rose-500 border border-rose-500/30 px-4 py-1.5 rounded-lg hover:bg-rose-400/10 font-bold uppercase tracking-widest transition-all">全仓紧急停止并平仓</button>
                </div>
                <table className="w-full text-left text-[11px]">
                  <thead className="text-slate-500 uppercase bg-black/30 font-bold tracking-widest">
                    <tr><th className="px-6 py-4">证券代码</th><th className="px-6 py-4">方向</th><th className="px-6 py-4">持仓/均价</th><th className="px-6 py-4 text-right">收益率</th><th className="px-6 py-4 text-right">估盈金额</th></tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {MOCK_POSITIONS.map(pos => (
                      <tr key={pos.id} className="hover:bg-slate-800/30 transition-colors group">
                        <td className="px-6 py-5 font-bold text-white group-hover:text-blue-400 transition-colors">{pos.asset}</td>
                        <td className="px-6 py-5">
                          <span className={`px-3 py-1 rounded-full text-[10px] font-black ${pos.side === '多' ? 'text-rose-500 bg-rose-500/10 border border-rose-500/20' : 'text-emerald-500 bg-emerald-500/10 border border-emerald-500/20'}`}>{pos.side}</span>
                        </td>
                        <td className="px-6 py-5 font-mono text-slate-300"><div>{pos.amount} 股</div><div className="opacity-40 text-[10px] italic">{pos.entryPrice}</div></td>
                        <td className={`px-6 py-5 text-right font-mono font-black ${pos.pnl.startsWith('+') ? 'text-rose-500' : 'text-emerald-500'}`}>{pos.pnl}</td>
                        <td className={`px-6 py-5 text-right font-mono font-black ${pos.pnl.startsWith('+') ? 'text-rose-500' : 'text-emerald-500'}`}>{pos.pnlValue}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'trades' && (
            <div className="animate-in fade-in slide-in-from-bottom-2 duration-500 max-w-7xl mx-auto">
              <div className="bg-[#161922] border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
                <div className="px-6 py-5 border-b border-slate-800 flex justify-between items-center bg-black/20">
                  <h3 className="font-bold text-white text-xs uppercase tracking-[0.2em] flex items-center gap-2"><History size={16} /> 交易执行引擎审计流水</h3>
                  <button className="bg-blue-600 text-[10px] px-5 py-2 rounded-xl text-white font-black hover:bg-blue-500 shadow-lg active:scale-95 transition-all">导出当日 PDF 报告</button>
                </div>
                <div className="overflow-x-auto">
                   <table className="w-full text-left text-xs">
                    <thead className="text-[10px] text-slate-500 uppercase bg-black/40 font-bold tracking-widest">
                      <tr><th className="px-6 py-5">成交时间</th><th className="px-6 py-5">标的代码</th><th className="px-6 py-5">执行结果</th><th className="px-6 py-5 text-right">成交均价</th><th className="px-6 py-5 text-center">深度审计</th></tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/40">
                      {MOCK_TRADES.map(trade => (
                        <tr key={trade.id} className="hover:bg-slate-800/40 transition-colors">
                          <td className="px-6 py-5 font-mono text-slate-500">{trade.time}</td>
                          <td className="px-6 py-5 font-black text-slate-200">{trade.asset}</td>
                          <td className="px-6 py-5">
                            <span className={`px-3 py-1 rounded-lg text-[10px] font-black border tracking-wider ${trade.status === '正常成交' ? 'text-rose-500 bg-rose-500/10 border-rose-500/20' : 'text-amber-500 bg-amber-500/10 border-amber-500/20'}`}>
                              {trade.status}
                            </span>
                          </td>
                          <td className="px-6 py-5 text-right font-mono font-black text-slate-200">¥{trade.price}</td>
                          <td className="px-6 py-5 text-center">
                             <button className="text-blue-400 hover:text-blue-200 transition-colors hover:scale-125 transform inline-block"><ExternalLink size={16} /></button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}