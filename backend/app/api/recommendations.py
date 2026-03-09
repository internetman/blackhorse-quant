from fastapi import APIRouter, Depends, Query
from app.models import RecommendationsResponse, User
from app.store import store
from app.deps import get_current_user
from app.market_data import get_news_data, get_quote_data, today_shanghai_str

router = APIRouter()


@router.get("/", response_model=RecommendationsResponse)
async def get_recommendations(
    date_str: str | None = Query(None, alias="date"),
    news_limit: int = Query(3, ge=1, le=10),
    user: User = Depends(get_current_user),
):
    target = date_str or today_shanghai_str()
    watch_symbols = {w.symbol for w in store.get_watchlist(user.id)}
    recs = [r for r in store.recommendations if r.date == target and r.symbol in watch_symbols]
    if not recs and not watch_symbols:
        recs = []
    elif not recs:
        recs = [r for r in store.recommendations if r.symbol in watch_symbols]
    summary = store.get_daily_summary()
    summary.total = len(recs)
    summary.tradable = sum(1 for r in recs if r.action == "可交易")
    summary.risky = sum(1 for r in recs if r.action in ("风险升高", "不建议交易"))
    summary.watch = len(recs) - summary.tradable - summary.risky
    enriched = [
        rec.model_copy(update={
            "quote": get_quote_data(rec.symbol),
            "news": get_news_data(rec.symbol, news_limit),
        })
        for rec in recs
    ]
    return RecommendationsResponse(
        date=target,
        summary=summary,
        recommendations=enriched,
    )
