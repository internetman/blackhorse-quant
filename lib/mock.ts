// Mock 数据
export interface Position {
  id: number;
  asset: string;
  side: '多' | '空';
  amount: string;
  entryPrice: string;
  currentPrice: string;
  pnl: string;
  pnlValue: string;
}

export interface Trade {
  id: number;
  time: string;
  asset: string;
  side: string;
  price: string;
  status: string;
  reason?: string;
}

export const MOCK_POSITIONS: Position[] = [
  { id: 1, asset: '贵州茅台 (600519)', side: '多', amount: '200', entryPrice: '1,650.00', currentPrice: '1,682.50', pnl: '+1.97%', pnlValue: '+¥6,500' },
  { id: 2, asset: '宁德时代 (300750)', side: '多', amount: '1500', entryPrice: '158.20', currentPrice: '162.10', pnl: '+2.46%', pnlValue: '+¥5,850' },
  { id: 3, asset: '隆基绿能 (601012)', side: '多', amount: '2000', entryPrice: '22.50', currentPrice: '20.10', pnl: '-10.67%', pnlValue: '-¥4,800' },
  { id: 4, asset: '比亚迪 (002594)', side: '空', amount: '800', entryPrice: '210.50', currentPrice: '205.80', pnl: '+2.23%', pnlValue: '+¥3,760' },
];

export const MOCK_TRADES: Trade[] = [
  { id: 101, time: '14:20:01', asset: '招商银行 (600036)', side: '买入', price: '32.50', status: '正常成交', reason: '均线金叉信号触发' },
  { id: 102, time: '13:45:12', asset: '中国平安 (601318)', side: '卖出', price: '41.80', status: '风控拒绝', reason: 'RSI 超买信号' }
];
