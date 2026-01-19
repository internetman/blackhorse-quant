'use client';
import { useState } from 'react';
import { Save, Lock, Target, Zap, Briefcase, GanttChart, ShieldAlert, Clock, ClipboardCheck } from 'lucide-react';
import { ConfigSection } from '@/components/ConfigSection';
import { FormField } from '@/components/FormField';
import { Switch } from '@/components/Switch';

export default function ConfigPage() {
  const [riskConfirmed, setRiskConfirmed] = useState(false);
  
  // 开关状态管理
  const [switches, setSwitches] = useState({
    excludeSuspended: true,        // 自动排除停牌标的
    excludeST: true,               // 自动排除 ST / *ST
    allowReverse: false,           // 允许同标的反向操作
    allowDynamicAdd: false,        // 允许盘中动态加仓
    smartSplit: true,              // 开启智能拆单算法
    t0Trading: true,               // 支持 T+0 回转交易
    autoPriceTrack: false,         // 自动价格追踪补单
    autoCircuitBreaker: true,       // 连续亏损自动熔断逻辑
    recordKline: true,             // 记录每一根 K 线信号快照
    recordRiskReject: true,        // 记录每笔风控拒绝判定细节
    enableReplay: false,           // 启用实时仿真回放数据流
    autoExport: true,              // 收盘自动导出审计报告
  });
  
  const updateSwitch = (key: keyof typeof switches) => {
    setSwitches(prev => ({ ...prev, [key]: !prev[key] }));
  };
  
  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-10 max-w-7xl mx-auto w-full">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between border-b border-slate-800 pb-6 md:pb-8 gap-4">
        <div className="flex-1">
          <h2 className="text-xl md:text-2xl font-bold text-white flex flex-wrap items-center gap-2 md:gap-3">
            策略参数中心 <span className="text-[9px] md:text-[10px] font-mono bg-blue-500/10 text-blue-500 px-2 py-0.5 rounded-full border border-blue-500/20">v3.2.0 稳定版</span>
          </h2>
          <p className="text-slate-500 mt-1.5 text-[10px] md:text-xs font-medium uppercase tracking-[0.1em]">
            支持参数热重载：所有变更将在下一个行情切片到来时生效
          </p>
        </div>
        <div className="flex flex-col items-stretch md:items-end gap-3">
          <div className="flex items-center gap-2 md:gap-3 bg-slate-900 border border-slate-800 px-3 md:px-4 py-2 rounded-xl md:rounded-2xl shadow-inner border-l-4 border-l-rose-500">
            <input 
              type="checkbox" 
              id="riskCheck" 
              checked={riskConfirmed} 
              onChange={(e) => setRiskConfirmed(e.target.checked)} 
              className="w-4 h-4 md:w-5 md:h-5 rounded text-blue-600 bg-black border-slate-700 focus:ring-0 shrink-0 touch-manipulation" 
            />
            <label htmlFor="riskCheck" className="text-[10px] md:text-xs text-rose-100 font-bold cursor-pointer select-none">
              我已知晓此变更将立即影响实盘，自担交易盈亏
            </label>
          </div>
          <button 
            disabled={!riskConfirmed}
            onClick={() => { alert("部署指令已发送，节点热重载中..."); setRiskConfirmed(false); }}
            className={`flex items-center justify-center gap-2 px-6 md:px-10 py-2.5 md:py-3.5 rounded-xl md:rounded-2xl font-bold transition-all transform active:scale-95 shadow-xl touch-manipulation text-sm md:text-base ${
              riskConfirmed 
                ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-blue-600/40' 
                : 'bg-slate-800 text-slate-500 cursor-not-allowed opacity-50'
            }`}
          >
            <Save size={16} className="md:w-[18px] md:h-[18px]" /> 
            <span className="hidden sm:inline">同步至实盘环境</span>
            <span className="sm:hidden">同步</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
        {/* 1. 策略基础信息 */}
        <ConfigSection title="策略基础信息" icon={Lock} readonly>
          <div className="space-y-4 opacity-75">
            <FormField label="策略名称">
              <div className="bg-black/30 p-2 rounded border border-slate-800 text-slate-300 font-mono text-[10px]">
                A股波动率均衡对冲策略
              </div>
            </FormField>
            <div className="grid grid-cols-2 gap-3">
              <FormField label="策略类型">
                <div className="bg-black/30 p-2 rounded border border-slate-800 text-slate-300 font-mono text-[9px]">波动率套利</div>
              </FormField>
              <FormField label="适用市场">
                <div className="bg-black/30 p-2 rounded border border-slate-800 text-slate-300 font-mono text-[9px]">沪深 A 股</div>
              </FormField>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <FormField label="版本识别">
                <div className="bg-blue-500/10 p-2 rounded border border-blue-500/20 text-blue-400 font-mono text-[9px]">v3.2.0 Stable</div>
              </FormField>
              <FormField label="运行环境">
                <div className="bg-rose-500/10 p-2 rounded border border-rose-500/20 text-rose-400 font-mono text-[9px]">实盘环境</div>
              </FormField>
            </div>
            <FormField label="维护团队">
              <div className="bg-black/30 p-2 rounded border border-slate-800 text-slate-300 font-mono text-[10px]">黑马量化核心研发组</div>
            </FormField>
          </div>
        </ConfigSection>

        {/* 2. 交易标的与范围 */}
        <ConfigSection title="交易标的范围" icon={Target}>
          <FormField label="证券池来源">
            <select className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 md:p-2.5 text-xs text-white outline-none touch-manipulation">
              <option>全市场活跃股</option>
              <option>沪深300成分股</option>
              <option>中证500成分股</option>
              <option>自定义关注池</option>
            </select>
          </FormField>
          <div className="grid grid-cols-2 gap-3">
            <FormField label="最大同时持仓数">
              <input type="number" defaultValue={30} className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 md:p-2.5 text-xs text-white font-mono touch-manipulation" />
            </FormField>
            <FormField label="成交额下限(万)">
              <input type="number" defaultValue={1000} className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 md:p-2.5 text-xs text-white font-mono touch-manipulation" />
            </FormField>
          </div>
          <div className="space-y-2.5 pt-2">
            <Switch checked={switches.excludeSuspended} onChange={() => updateSwitch('excludeSuspended')} label="自动排除停牌标的" />
            <Switch checked={switches.excludeST} onChange={() => updateSwitch('excludeST')} label="自动排除 ST / *ST" />
            <Switch checked={switches.allowReverse} onChange={() => updateSwitch('allowReverse')} label="允许同标的反向操作" />
          </div>
        </ConfigSection>

        {/* 3. 信号生成参数 */}
        <ConfigSection title="信号引擎参数" icon={Zap}>
          <FormField label="核心指标逻辑">
            <select className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white touch-manipulation">
              <option>EMA + ATR 趋势波动</option>
              <option>RSI 背离检测</option>
              <option>多因子打分模型</option>
            </select>
          </FormField>
          <div className="grid grid-cols-2 gap-3">
            <FormField label="数据回看周期">
              <input type="number" defaultValue={20} className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white font-mono touch-manipulation" />
            </FormField>
            <FormField label="信号触发阈值">
              <input type="number" step="0.1" defaultValue={1.5} className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white font-mono touch-manipulation" />
            </FormField>
          </div>
          <FormField label="信号确认(连续次数)">
            <input type="range" min="1" max="5" defaultValue={3} className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500" />
          </FormField>
          <FormField label="开仓冷却时间(分)">
            <input type="number" defaultValue={15} className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white font-mono touch-manipulation" />
          </FormField>
        </ConfigSection>

        {/* 4. 仓位与资金分配 */}
        <ConfigSection title="仓位与资金分配" icon={Briefcase}>
          <FormField label="资金分配模式">
            <select className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white font-bold touch-manipulation">
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
            <Switch checked={switches.allowDynamicAdd} onChange={() => updateSwitch('allowDynamicAdd')} label="允许盘中动态加仓" />
            <FormField label="最大允许加仓次数">
              <input type="number" defaultValue={0} className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white font-mono opacity-50" disabled />
            </FormField>
          </div>
        </ConfigSection>

        {/* 5. 交易执行策略 */}
        <ConfigSection title="执行算法设置" icon={GanttChart}>
          <FormField label="引擎调度频率">
            <select className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white touch-manipulation">
              <option>1 分钟 (极速响应)</option>
              <option>5 分钟 (稳健平衡)</option>
              <option>15 分钟</option>
            </select>
          </FormField>
          <div className="grid grid-cols-2 gap-3">
            <FormField label="单笔委托上限(手)">
              <input type="number" defaultValue={500} className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white font-mono touch-manipulation" />
            </FormField>
            <FormField label="滑点容忍阈值(%)">
              <input type="number" step="0.01" defaultValue={0.05} className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white font-mono touch-manipulation" />
            </FormField>
          </div>
          <div className="space-y-2.5 pt-2">
            <Switch checked={switches.smartSplit} onChange={() => updateSwitch('smartSplit')} label="开启智能拆单算法" />
            <Switch checked={switches.t0Trading} onChange={() => updateSwitch('t0Trading')} label="支持 T+0 回转交易" />
            <Switch checked={switches.autoPriceTrack} onChange={() => updateSwitch('autoPriceTrack')} label="自动价格追踪补单" />
          </div>
        </ConfigSection>

        {/* 6. 风控参数设置 */}
        <ConfigSection title="风险控制参数" icon={ShieldAlert} risk>
          <div className="grid grid-cols-2 gap-3">
            <FormField label="日内最大回撤(%)" risk>
              <input type="number" step="0.1" defaultValue={2.5} className="w-full bg-[#1e1418] border border-rose-900 rounded-lg p-2 text-xs text-rose-500 font-bold touch-manipulation" />
            </FormField>
            <FormField label="全局预警平仓线(%)" risk>
              <input type="number" step="0.1" defaultValue={8.0} className="w-full bg-[#1e1418] border border-rose-900 rounded-lg p-2 text-xs text-rose-500 font-bold touch-manipulation" />
            </FormField>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <FormField label="单股持仓比例上限(%)" risk>
              <input type="number" defaultValue={15} className="w-full bg-[#1e1418] border border-rose-900 rounded-lg p-2 text-xs text-rose-500 touch-manipulation" />
            </FormField>
            <FormField label="日交易总笔数限制" risk>
              <input type="number" defaultValue={50} className="w-full bg-[#1e1418] border border-rose-900 rounded-lg p-2 text-xs text-rose-500 touch-manipulation" />
            </FormField>
          </div>
          <div className="space-y-2.5 pt-2">
            <Switch checked={switches.autoCircuitBreaker} onChange={() => updateSwitch('autoCircuitBreaker')} label="连续亏损自动熔断逻辑" />
            <button className="w-full bg-rose-600/20 hover:bg-rose-600/40 text-rose-500 border border-rose-600/30 py-2 rounded-lg text-[10px] font-black tracking-widest uppercase flex items-center justify-center gap-2 touch-manipulation">
              <span>一键停止运行并强平</span>
            </button>
          </div>
        </ConfigSection>

        {/* 7. 交易行为约束 */}
        <ConfigSection title="交易行为约束" icon={Clock}>
          <div className="grid grid-cols-2 gap-3">
            <FormField label="开盘禁交时长(分)">
              <input type="number" defaultValue={15} className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white font-mono touch-manipulation" />
            </FormField>
            <FormField label="尾盘停止开仓(分)">
              <input type="number" defaultValue={10} className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white font-mono touch-manipulation" />
            </FormField>
          </div>
          <div className="space-y-3 pt-4 border-t border-slate-800/50">
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-slate-400 uppercase font-bold tracking-tight">禁止高频短时间反向</span>
              <input type="checkbox" defaultChecked className="w-4 h-4 rounded bg-slate-800 border-slate-700 touch-manipulation" />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-slate-400 uppercase font-bold tracking-tight">禁止盘中极端放量追涨</span>
              <input type="checkbox" defaultChecked className="w-4 h-4 rounded bg-slate-800 border-slate-700 touch-manipulation" />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-slate-400 uppercase font-bold tracking-tight">禁止大幅跳空开盘下单</span>
              <input type="checkbox" className="w-4 h-4 rounded bg-slate-800 border-slate-700 touch-manipulation" />
            </div>
          </div>
        </ConfigSection>

        {/* 8. 审计与快照设置 */}
        <ConfigSection title="审计与快照设置" icon={ClipboardCheck}>
          <div className="space-y-4">
            <Switch checked={switches.recordKline} onChange={() => updateSwitch('recordKline')} label="记录每一根 K 线信号快照" />
            <Switch checked={switches.recordRiskReject} onChange={() => updateSwitch('recordRiskReject')} label="记录每笔风控拒绝判定细节" />
            <Switch checked={switches.enableReplay} onChange={() => updateSwitch('enableReplay')} label="启用实时仿真回放数据流" />
            <Switch checked={switches.autoExport} onChange={() => updateSwitch('autoExport')} label="收盘自动导出审计报告" />
          </div>
          <div className="pt-6 mt-6 border-t border-slate-800">
            <div className="flex items-center justify-between opacity-50">
              <span className="text-[10px] text-slate-500 font-bold uppercase">日志合规存储期</span>
              <span className="text-[10px] text-slate-200 font-mono tracking-widest">90 天</span>
            </div>
          </div>
        </ConfigSection>
      </div>
    </div>
  );
}
