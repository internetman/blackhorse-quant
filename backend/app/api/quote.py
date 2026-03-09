"""行情接口 stub。正式可接 akshare。"""
from datetime import datetime
from fastapi import APIRouter, Query

router = APIRouter()

MOCK_QUOTES: dict[str, tuple[float, float]] = {
    "600519.SH": (1688.0, 0.32),
    "300750.SZ": (156.0, -0.5),
    "601318.SH": (43.5, -1.2),
    "600036.SH": (38.2, 0.8),
    "000858.SZ": (142.0, 0.5),
    "601012.SH": (12.5, -0.8),
    "002594.SZ": (285.0, 1.2),
    "600900.SH": (28.5, 0.1),
}


@router.get("/")
async def get_quote(symbol: str = Query(..., alias="symbol")):
    symbol = (symbol or "").upper().strip()
    if not symbol:
        return {"symbol": "", "latestPrice": 0, "changePercent": 0, "volume": 0, "updatedAt": ""}
    price, pct = MOCK_QUOTES.get(symbol, (0.0, 0.0))
    return {
        "symbol": symbol,
        "latestPrice": price,
        "changePercent": pct,
        "volume": 1000000,
        "updatedAt": datetime.now().isoformat(),
    }
