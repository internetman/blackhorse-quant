from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/")
async def get_positions():
    """v1.2 已移除持仓功能，接口废弃。"""
    raise HTTPException(status_code=410, detail="Gone: 本版本已移除我的持仓，接口已废弃")


@router.get("/{position_id}")
async def get_position(position_id: str):
    """v1.2 已移除持仓功能，接口废弃。"""
    raise HTTPException(status_code=410, detail="Gone: 本版本已移除我的持仓，接口已废弃")


@router.put("/{position_id}")
async def update_position(position_id: str, updates: dict):
    """v1.2 已移除持仓功能，接口废弃。"""
    raise HTTPException(status_code=410, detail="Gone: 本版本已移除我的持仓，接口已废弃")


@router.delete("/")
async def clear_positions():
    """v1.2 已移除持仓功能，接口废弃。"""
    raise HTTPException(status_code=410, detail="Gone: 本版本已移除我的持仓，接口已废弃")
