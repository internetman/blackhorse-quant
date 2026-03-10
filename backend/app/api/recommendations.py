from fastapi import APIRouter, Depends, Query
from app.models import DailySummary, RecommendationsResponse, User
from app.store import store
from app.deps import get_current_user
from app.market_data import get_news_data, get_quote_data, today_shanghai_str
from app.analysis_engine import generate_recommendation

router = APIRouter()


@router.get("/", response_model=RecommendationsResponse)
async def get_recommendations(
    date_str: str | None = Query(None, alias="date"),
    news_limit: int = Query(3, ge=1, le=10),
    user: User = Depends(get_current_user),
):
    target = date_str or today_shanghai_str()
    watch_items = store.get_watchlist(user.id)
    recs = [generate_recommendation(w.symbol, w.name) for w in watch_items]
    summary = DailySummary(
        total=len(recs),
        tradable=sum(1 for r in recs if r.action == "可交易"),
        risky=sum(1 for r in recs if r.action in ("风险升高", "不建议交易")),
        watch=0,
    )
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
