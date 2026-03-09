from fastapi import APIRouter, Query, Depends
from app.models import NewsItem, User
from app.market_data import get_news_data
from app.deps import get_current_user

router = APIRouter()

@router.get("/", response_model=list[NewsItem])
async def get_news(
    symbol: str = Query(..., alias="symbol"),
    limit: int = Query(10, ge=1, le=20),
    user: User = Depends(get_current_user),
):
    _ = user
    return get_news_data(symbol, limit)
