from fastapi import APIRouter, Query, Depends
from app.models import QuoteData, User
from app.market_data import get_quote_data
from app.deps import get_current_user

router = APIRouter()

@router.get("/", response_model=QuoteData)
async def get_quote(
    symbol: str = Query(..., alias="symbol"),
    user: User = Depends(get_current_user),
):
    _ = user
    return get_quote_data(symbol)
