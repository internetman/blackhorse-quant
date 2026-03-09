from fastapi import APIRouter, Depends
from app.models import Review, ReviewStats, User
from app.store import store
from app.deps import get_current_user

router = APIRouter()


def _user_reviews(user_id: str):
    return [r for r in store.reviews if r.userId == user_id]


@router.get("/", response_model=list[Review])
async def get_reviews(
    type: str | None = None,
    user: User = Depends(get_current_user),
):
    reviews = _user_reviews(user.id)
    if type:
        reviews = [r for r in reviews if r.reviewType == type]
    return reviews


@router.get("/stats/", response_model=ReviewStats)
async def get_review_stats(user: User = Depends(get_current_user)):
    reviews = _user_reviews(user.id)
    effective = sum(1 for r in reviews if r.verdict == "有效")
    neutral = sum(1 for r in reviews if r.verdict == "一般")
    ineffective = sum(1 for r in reviews if r.verdict == "失效")
    total = len(reviews)
    return ReviewStats(
        total=total,
        effective=effective,
        neutral=neutral,
        ineffective=ineffective,
        effectiveRate=effective / total if total else 0.0,
    )
