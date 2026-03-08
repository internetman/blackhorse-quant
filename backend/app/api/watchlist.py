from fastapi import APIRouter, HTTPException
from app.models import WatchItem
from app.store import store

router = APIRouter()


@router.get("/", response_model=list[WatchItem])
async def get_watchlist():
    return [w for w in store.watchlist if w.isActive]


@router.post("/", response_model=WatchItem)
async def add_item(data: dict):
    user = store.users[0]  # simplified: use first user
    item = store.add_watch_item(
        symbol=data.get("symbol", ""),
        name=data.get("name", ""),
        reason=data.get("reason", ""),
        user=user,
    )
    return item


@router.delete("/{item_id}")
async def remove_item(item_id: str):
    if not store.remove_watch_item(item_id):
        raise HTTPException(status_code=404, detail="未找到该自选股")
    return {"message": "已删除"}
