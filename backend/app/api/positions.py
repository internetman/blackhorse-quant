from fastapi import APIRouter, HTTPException
from app.models import PrivatePosition
from app.store import store

router = APIRouter()


@router.get("/", response_model=list[PrivatePosition])
async def get_positions():
    return store.positions


@router.put("/{position_id}", response_model=PrivatePosition)
async def update_position(position_id: str, updates: dict):
    for i, pos in enumerate(store.positions):
        if pos.id == position_id:
            updated = pos.model_copy(update=updates)
            store.positions[i] = updated
            return updated
    raise HTTPException(status_code=404, detail="持仓不存在")
