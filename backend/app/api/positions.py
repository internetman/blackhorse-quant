from fastapi import APIRouter
from app.models import Position
from app.store import store

router = APIRouter()

@router.get("/", response_model=list[Position])
async def get_positions():
    """获取持仓列表"""
    return store.get_positions()

@router.get("/{position_id}", response_model=Position)
async def get_position(position_id: int):
    """获取单个持仓"""
    positions = store.get_positions()
    for pos in positions:
        if pos.id == position_id:
            return pos
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="持仓不存在")

@router.put("/{position_id}", response_model=Position)
async def update_position(position_id: int, updates: dict):
    """更新持仓信息"""
    updated = store.update_position(position_id, updates)
    if updated is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="持仓不存在")
    return updated

@router.delete("/", response_model=dict)
async def clear_positions():
    """清空所有持仓（强平）"""
    store.set_positions([])
    store.update_stats(totalPnl=0.0, positionCount=0)
    return {"message": "所有持仓已清空"}
