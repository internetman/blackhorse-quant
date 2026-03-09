"""个股新闻接口 stub。正式可接 akshare stock_news_em。"""
from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/")
async def get_news(
    symbol: str = Query(..., alias="symbol"),
    limit: int = Query(10, ge=1, le=20),
):
    return []
