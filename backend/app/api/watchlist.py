from fastapi import APIRouter, HTTPException, Depends
from app.models import WatchItem, User
from app.store import store
from app.deps import get_current_user

router = APIRouter()


@router.get("/", response_model=list[WatchItem])
async def get_watchlist(user: User = Depends(get_current_user)):
    return store.get_watchlist(user.id)


@router.post("/", response_model=WatchItem)
async def add_item(data: dict, user: User = Depends(get_current_user)):
    symbol = data.get("symbol", "").strip()
    name = (data.get("name", "") or symbol).strip()
    reason = data.get("reason", "").strip()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol 不能为空")
    item = store.add_watch_item(user.id, symbol, name, reason)
    if item is None:
        raise HTTPException(status_code=409, detail="已在关注列表中")
    return item


@router.delete("/{symbol:path}")
async def remove_item(symbol: str, user: User = Depends(get_current_user)):
    if not store.remove_watch_item(user.id, symbol):
        raise HTTPException(status_code=404, detail="未找到该自选股")
    return {"message": "已取消关注"}
