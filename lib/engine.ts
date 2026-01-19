'use client';
import { useStore } from './store';
import type { Trade } from './mock';

let engineInterval: NodeJS.Timeout | null = null;
let tradeInterval: NodeJS.Timeout | null = null;

// 生成随机价格变化
function randomPriceChange(basePrice: string): string {
  const num = parseFloat(basePrice.replace(/,/g, ''));
  const change = (Math.random() - 0.5) * 0.02; // ±1% 变化
  const newPrice = num * (1 + change);
  return newPrice.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// 计算盈亏
function calculatePnl(entryPrice: string, currentPrice: string, amount: string, side: '多' | '空'): { pnl: string; pnlValue: string } {
  const entry = parseFloat(entryPrice.replace(/,/g, ''));
  const current = parseFloat(currentPrice.replace(/,/g, ''));
  const qty = parseFloat(amount.replace(/,/g, ''));
  
  let pnlPercent: number;
  if (side === '多') {
    pnlPercent = ((current - entry) / entry) * 100;
  } else {
    pnlPercent = ((entry - current) / entry) * 100;
  }
  
  const pnlValue = (current - entry) * qty * (side === '多' ? 1 : -1);
  
  return {
    pnl: `${pnlPercent >= 0 ? '+' : ''}${pnlPercent.toFixed(2)}%`,
    pnlValue: `${pnlValue >= 0 ? '+' : ''}¥${Math.abs(pnlValue).toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`,
  };
}

// 生成随机交易
function generateRandomTrade(): Trade {
  const assets = ['招商银行 (600036)', '中国平安 (601318)', '中国银行 (601988)', '工商银行 (601398)', '建设银行 (601939)'];
  const sides = ['买入', '卖出'];
  const statuses = ['正常成交', '风控拒绝', '部分成交'];
  const reasons = ['均线金叉信号触发', 'RSI 超买信号', 'MACD 背离', '成交量突破', '价格突破阻力位'];
  
  const now = new Date();
  const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
  
  return {
    id: Date.now(),
    time,
    asset: assets[Math.floor(Math.random() * assets.length)],
    side: sides[Math.floor(Math.random() * sides.length)],
    price: (Math.random() * 100 + 10).toFixed(2),
    status: statuses[Math.floor(Math.random() * statuses.length)],
    reason: reasons[Math.floor(Math.random() * reasons.length)],
  };
}

// 启动引擎
export function startEngine() {
  // 每秒更新价格和盈亏
  engineInterval = setInterval(() => {
    const state = useStore.getState();
    
    if (state.sysStatus === 'kill') {
      // 强平：清空持仓
      if (state.positions.length > 0) {
        const now = new Date();
        const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
        
        state.positions.forEach((pos) => {
          state.addTrade({
            id: Date.now() + Math.random(),
            time,
            asset: pos.asset,
            side: pos.side === '多' ? '卖出' : '买入',
            price: pos.currentPrice,
            status: '强平',
            reason: '系统强平指令',
          });
        });
        
        state.setPositions([]);
        state.setTotalPnl(0);
      }
      return;
    }
    
    // 更新持仓价格和盈亏
    const updatedPositions = state.positions.map((pos) => {
      const newPrice = randomPriceChange(pos.currentPrice);
      const { pnl, pnlValue } = calculatePnl(pos.entryPrice, newPrice, pos.amount, pos.side);
      
      return {
        ...pos,
        currentPrice: newPrice,
        pnl,
        pnlValue,
      };
    });
    
    state.setPositions(updatedPositions);
    
    // 计算总盈亏
    const totalPnl = updatedPositions.reduce((sum, pos) => {
      const value = parseFloat(pos.pnlValue.replace(/[+¥,]/g, ''));
      return sum + value;
    }, 0);
    state.setTotalPnl(totalPnl);
    
    // 更新今日盈亏（模拟）
    const todayPnlChange = (Math.random() - 0.4) * 1000;
    state.setTodayPnl(state.todayPnl + todayPnlChange);
  }, 1000);
  
  // 每5秒生成一条交易（仅在 running 状态）
  tradeInterval = setInterval(() => {
    const state = useStore.getState();
    
    if (state.sysStatus === 'running') {
      const trade = generateRandomTrade();
      state.addTrade(trade);
    }
  }, 5000);
}

// 停止引擎
export function stopEngine() {
  if (engineInterval) {
    clearInterval(engineInterval);
    engineInterval = null;
  }
  if (tradeInterval) {
    clearInterval(tradeInterval);
    tradeInterval = null;
  }
}

// 监听状态变化（在组件中调用）
export function setupStatusListener() {
  return useStore.subscribe((state, prevState) => {
    if (state.sysStatus === 'kill' && prevState.sysStatus !== 'kill' && state.positions.length > 0) {
      // 状态变为 kill 时立即强平
      const now = new Date();
      const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
      
      state.positions.forEach((pos) => {
        state.addTrade({
          id: Date.now() + Math.random(),
          time,
          asset: pos.asset,
          side: pos.side === '多' ? '卖出' : '买入',
          price: pos.currentPrice,
          status: '强平',
          reason: '系统强平指令',
        });
      });
      
      state.setPositions([]);
      state.setTotalPnl(0);
    }
  });
}
