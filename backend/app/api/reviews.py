from fastapi import APIRouter
from app.models import Review, ReviewStats
from app.store import store

router = APIRouter()


@router.get("/", response_model=list[Review])
async def get_reviews(type: str | None = None):
    if type:
        return [r for r in store.reviews if r.reviewType == type]
    return store.reviews


@router.get("/stats/", response_model=ReviewStats)
async def get_review_stats():
    return store.review_stats
