"""
后端引擎：模拟数据更新
"""
import asyncio
import random
from datetime import datetime
from app.store import store
from app.models import Position, Trade

def random_price_change(base_price: str) -> str:
    """生成随机价格变化（±1%）"""
    num = float(base_price.replace(',', ''))
    change = (random.random() - 0.5) * 0.02  # ±1% 变化
    new_price = num * (1 + change)
    # 格式化价格，添加千位分隔符
    return f"{new_price:,.2f}"

def calculate_pnl(entry_price: str, current_price: str, amount: str, side: str) -> tuple[str, str]:
    """计算盈亏"""
    entry = float(entry_price.replace(',', ''))
    current = float(current_price.replace(',', ''))
    qty = float(amount.replace(',', ''))
    
    if side == '多':
        pnl_percent = ((current - entry) / entry) * 100
    else:
        pnl_percent = ((entry - current) / entry) * 100
    
    pnl_value = (current - entry) * qty * (1 if side == '多' else -1)
    
    pnl_str = f"{'+' if pnl_percent >= 0 else ''}{pnl_percent:.2f}%"
    pnl_value_str = f"{'+' if pnl_value >= 0 else ''}¥{abs(int(pnl_value)):,}"
    
    return pnl_str, pnl_value_str

def generate_random_trade() -> Trade:
    """生成随机交易记录"""
    assets = ['招商银行 (600036)', '中国平安 (601318)', '中国银行 (601988)', '工商银行 (601398)', '建设银行 (601939)']
    sides = ['买入', '卖出']
    statuses = ['正常成交', '风控拒绝', '部分成交']
    reasons = ['均线金叉信号触发', 'RSI 超买信号', 'MACD 背离', '成交量突破', '价格突破阻力位']
    
    now = datetime.now()
    time_str = now.strftime('%H:%M:%S')
    
    return Trade(
        id=int(datetime.now().timestamp() * 1000),
        time=time_str,
        asset=random.choice(assets),
        side=random.choice(sides),
        price=f"{random.random() * 100 + 10:.2f}",
        status=random.choice(statuses),
        reason=random.choice(reasons)
    )

async def update_positions():
    """更新持仓价格和盈亏"""
    positions = store.get_positions()
    if not positions:
        return
    
    updated_positions = []
    for pos in positions:
        new_price = random_price_change(pos.currentPrice)
        pnl, pnl_value = calculate_pnl(pos.entryPrice, new_price, pos.amount, pos.side)
        
        updated = Position(
            id=pos.id,
            asset=pos.asset,
            side=pos.side,
            amount=pos.amount,
            entryPrice=pos.entryPrice,
            currentPrice=new_price,
            pnl=pnl,
            pnlValue=pnl_value
        )
        updated_positions.append(updated)
    
    store.set_positions(updated_positions)

async def generate_trade():
    """生成新交易记录"""
    sys_status = store.get_status()
    if sys_status == 'running':
        trade = generate_random_trade()
        store.add_trade(trade)

async def engine_loop():
    """引擎主循环"""
    tick_count = 0
    
    while True:
        try:
            sys_status = store.get_status()
            
            # 每秒更新持仓价格
            await update_positions()
            
            # 每5秒生成一条交易（仅在 running 状态）
            if sys_status == 'running' and tick_count % 5 == 0:
                await generate_trade()
            
            # kill 仅表示「停止策略、人工接管」，不再自动清空持仓。
            # 清空持仓请通过前端「全仓紧急停止并平仓」+ 确认弹窗 + DELETE 接口（需 ALLOW_FORCE_CLOSE）执行。
            
            tick_count += 1
            await asyncio.sleep(1)  # 每秒执行一次
            
        except Exception as e:
            print(f"引擎错误: {e}")
            await asyncio.sleep(1)

# 启动引擎
def start_engine():
    """启动引擎（在后台运行）"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(engine_loop())
    return loop
