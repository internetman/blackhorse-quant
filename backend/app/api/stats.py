from fastapi import APIRouter
from app.models import Stats
from app.store import store

router = APIRouter()

@router.get("/", response_model=Stats)
async def get_stats():
    """获取统计数据"""
    # 实时计算统计数据
    positions = store.get_positions()
    stats = store.get_stats()
    
    # 更新持仓数量
    position_count = len(positions)
    
    # 计算总盈亏
    total_pnl = 0.0
    for pos in positions:
        # 解析 pnlValue，例如 "+¥6,500" -> 6500
        pnl_str = pos.pnlValue.replace('+¥', '').replace('-¥', '').replace(',', '')
        try:
            pnl_value = float(pnl_str)
            if pos.pnlValue.startswith('-'):
                pnl_value = -pnl_value
            total_pnl += pnl_value
        except:
            pass
    
    # 计算资金占用率
    capital_usage = (position_count / 30) * 100 if position_count > 0 else 0
    
    # 更新统计数据
    stats = Stats(
        totalPnl=total_pnl,
        todayPnl=stats.todayPnl,
        positionCount=position_count,
        capitalUsage=capital_usage
    )
    store.update_stats(**stats.model_dump())
    
    return stats
