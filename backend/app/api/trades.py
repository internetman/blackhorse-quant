from fastapi import APIRouter, Query
from app.models import Trade
from app.store import store

router = APIRouter()

@router.get("/", response_model=list[Trade])
async def get_trades(limit: int = Query(default=100, ge=1, le=1000)):
    """获取交易记录列表"""
    return store.get_trades(limit=limit)

@router.get("/{trade_id}", response_model=Trade)
async def get_trade(trade_id: int):
    """获取单个交易记录"""
    trades = store.get_trades()
    for trade in trades:
        if trade.id == trade_id:
            return trade
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="交易记录不存在")

@router.post("/", response_model=Trade)
async def create_trade(trade: Trade):
    """创建新的交易记录"""
    store.add_trade(trade)
    return trade
