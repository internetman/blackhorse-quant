from fastapi import APIRouter
from app.models import RecommendationsResponse
from app.store import store
from datetime import date

router = APIRouter()


@router.get("/", response_model=RecommendationsResponse)
async def get_recommendations(date_str: str | None = None):
    target = date_str or date.today().isoformat()
    recs = [r for r in store.recommendations if r.date == target]
    if not recs:
        recs = store.recommendations
    return RecommendationsResponse(
        date=target,
        summary=store.get_daily_summary(),
        recommendations=recs,
    )
