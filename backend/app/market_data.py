from __future__ import annotations

from datetime import datetime
import os
import time
from zoneinfo import ZoneInfo

from app.models import QuoteData, NewsItem

try:
    import akshare as ak  # type: ignore
except Exception:  # pragma: no cover
    ak = None


SH_TZ = ZoneInfo("Asia/Shanghai")
USE_AKSHARE = os.getenv("USE_AKSHARE", "true").lower() == "true"
QUOTE_CACHE_TTL_SECONDS = int(os.getenv("QUOTE_CACHE_TTL_SECONDS", "20"))
NEWS_CACHE_TTL_SECONDS = int(os.getenv("NEWS_CACHE_TTL_SECONDS", "300"))


# akshare 失败时的降级数据（近期价格，约 2026 年初）
MOCK_QUOTES: dict[str, tuple[float, float, int]] = {
    "600519.SH": (1402.0, 0.25, 1256345),
    "300750.SZ": (148.0, -0.60, 3245609),
    "601318.SH": (42.8, -1.10, 5683401),
    "600036.SH": (37.5, 0.50, 4123401),
    "000858.SZ": (138.0, 0.30, 2678941),
    "601012.SH": (11.8, -0.90, 9183403),
    "002594.SZ": (278.0, 1.00, 7056234),
    "600900.SH": (27.8, 0.05, 3956784),
    "000001.SZ": (10.9, -0.20, 3012456),
    "600030.SH": (21.8, 0.70, 3567800),
}

# akshare 失败时的降级新闻（日期更新至 2026-03）
MOCK_NEWS: list[tuple[str, str, str]] = [
    ("600519", "贵州茅台经营稳健，渠道库存良性", "2026-03-18"),
    ("600519", "白酒板块估值修复，高端酒需求平稳", "2026-03-15"),
    ("300750", "宁德时代与车企签署长期供货协议", "2026-03-19"),
    ("300750", "动力电池价格企稳，行业集中度提升", "2026-03-16"),
    ("601318", "中国平安披露年度业绩预告", "2026-03-18"),
    ("600036", "招商银行四季度净息差环比持平", "2026-03-17"),
    ("000858", "五粮液动销表现符合预期", "2026-03-16"),
    ("002594", "比亚迪新能源车销量同比大增", "2026-03-19"),
    ("601012", "隆基绿能发布新一代组件产品", "2026-03-15"),
    ("600900", "长江电力年度发电量创历史新高", "2026-03-17"),
    ("000001", "平安银行发布新一期资本补充计划", "2026-03-14"),
    ("600030", "中信证券披露投行业务季度数据", "2026-03-16"),
]

_QUOTE_CACHE: dict[str, tuple[QuoteData, float]] = {}
_NEWS_CACHE: dict[str, tuple[list[NewsItem], float]] = {}
# 全市场实时行情缓存：code -> (latestPrice, changePercent, volume)，避免逐只请求失败
_SPOT_CACHE: tuple[dict[str, tuple[float, float, int]], float] | None = None
SPOT_CACHE_TTL_SECONDS = int(os.getenv("QUOTE_CACHE_TTL_SECONDS", "20"))


def normalize_symbol(symbol: str) -> str:
    raw = (symbol or "").strip().upper()
    if not raw:
        return ""
    if "." in raw:
        code, market = raw.split(".", 1)
        market = market.upper()
        if market in {"SH", "SZ"} and code.isdigit():
            return f"{code}.{market}"
        return raw
    if raw.isdigit() and len(raw) == 6:
        if raw.startswith(("6", "9", "5")):
            return f"{raw}.SH"
        if raw.startswith(("0", "2", "3")):
            return f"{raw}.SZ"
    return raw


def symbol_to_code(symbol: str) -> str:
    normalized = normalize_symbol(symbol)
    return normalized.split(".")[0] if "." in normalized else normalized


def _cached_quote(symbol: str) -> QuoteData | None:
    cached = _QUOTE_CACHE.get(symbol)
    if not cached:
        return None
    data, ts = cached
    if time.time() - ts > QUOTE_CACHE_TTL_SECONDS:
        return None
    return data


def _cached_news(symbol: str) -> list[NewsItem] | None:
    cached = _NEWS_CACHE.get(symbol)
    if not cached:
        return None
    data, ts = cached
    if time.time() - ts > NEWS_CACHE_TTL_SECONDS:
        return None
    return data


def _fetch_spot_cache() -> dict[str, tuple[float, float, int]] | None:
    """拉取全 A 股实时行情并缓存，返回 code -> (最新价, 涨跌幅, 成交量)。"""
    global _SPOT_CACHE
    if not USE_AKSHARE or ak is None:
        return None
    now = time.time()
    if _SPOT_CACHE is not None:
        _, ts = _SPOT_CACHE
        if now - ts <= SPOT_CACHE_TTL_SECONDS:
            return _SPOT_CACHE[0]
    try:
        df = ak.stock_zh_a_spot_em()
        if df is None or df.empty:
            return None
        out: dict[str, tuple[float, float, int]] = {}
        for _, row in df.iterrows():
            code = str(row.get("代码", "")).strip()
            if not code or len(code) != 6:
                continue
            try:
                latest = float(row.get("最新价", 0) or 0)
                pct = float(row.get("涨跌幅", 0) or 0)
                vol = int(float(row.get("成交量", 0) or 0))
                out[code] = (latest, pct, vol)
            except (TypeError, ValueError):
                continue
        _SPOT_CACHE = (out, now)
        return out
    except Exception:
        return None


def _get_quote_from_akshare(symbol: str) -> QuoteData | None:
    if not USE_AKSHARE or ak is None:
        return None
    normalized = normalize_symbol(symbol)
    code = symbol_to_code(symbol)
    # 优先从全市场实时行情缓存按代码取（真实价）
    spot = _fetch_spot_cache()
    if spot and code in spot:
        latest, pct, volume = spot[code]
        return QuoteData(
            symbol=normalized,
            latestPrice=latest,
            changePercent=pct,
            volume=volume,
            updatedAt=datetime.now(SH_TZ).isoformat(timespec="seconds"),
        )
    # 备用：盘口接口（可能不稳定）
    try:
        df = ak.stock_bid_ask_em(symbol=code)
        if df is not None and not df.empty:
            value_map = {
                str(row.get("item", "")).strip(): str(row.get("value", "")).strip()
                for _, row in df.iterrows()
                if "item" in row and "value" in row
            }
            latest = float(value_map.get("最新", value_map.get("最新价", "0")) or 0)
            pct = float(value_map.get("涨幅", value_map.get("涨跌幅", "0")) or 0)
            volume = int(float(value_map.get("总手", value_map.get("成交量", "0")) or 0))
            if latest > 0:
                return QuoteData(
                    symbol=normalized,
                    latestPrice=latest,
                    changePercent=pct,
                    volume=volume,
                    updatedAt=datetime.now(SH_TZ).isoformat(timespec="seconds"),
                )
    except Exception:
        pass
    return None


def _get_news_from_akshare(symbol: str, limit: int) -> list[NewsItem] | None:
    if not USE_AKSHARE or ak is None:
        return None
    code = symbol_to_code(symbol)
    try:
        df = ak.stock_news_em(symbol=code)
        if df is None or df.empty:
            return None
        rows = df.head(limit)
        out: list[NewsItem] = []
        for _, row in rows.iterrows():
            title = str(row.get("新闻标题", "")).strip()
            date_val = str(row.get("发布时间", "")).strip()
            summary = str(row.get("新闻内容", "")).strip()
            out.append(NewsItem(title=title or "无标题", date=date_val, summary=summary))
        return out
    except Exception:
        return None


def get_quote_data(symbol: str) -> QuoteData:
    normalized = normalize_symbol(symbol)
    cached = _cached_quote(normalized)
    if cached is not None:
        return cached

    real_data = _get_quote_from_akshare(normalized)
    if real_data is not None:
        _QUOTE_CACHE[normalized] = (real_data, time.time())
        return real_data

    latest_price, change_percent, volume = MOCK_QUOTES.get(normalized, (0.0, 0.0, 0))
    fallback = QuoteData(
        symbol=normalized,
        latestPrice=latest_price,
        changePercent=change_percent,
        volume=volume,
        updatedAt=datetime.now(SH_TZ).isoformat(timespec="seconds"),
    )
    _QUOTE_CACHE[normalized] = (fallback, time.time())
    return fallback


def get_news_data(symbol: str, limit: int = 10) -> list[NewsItem]:
    normalized = normalize_symbol(symbol)
    cached = _cached_news(normalized)
    if cached is not None:
        return cached[:limit]

    real_data = _get_news_from_akshare(normalized, limit)
    if real_data is not None and len(real_data) > 0:
        _NEWS_CACHE[normalized] = (real_data, time.time())
        return real_data

    code = symbol_to_code(normalized)
    items: list[NewsItem] = []
    for prefix, title, pub_date in MOCK_NEWS:
        if prefix == code:
            items.append(NewsItem(title=title, date=pub_date, summary=""))
            if len(items) >= limit:
                break
    if not items:
        items = [NewsItem(title="暂无该股票相关新闻", date="", summary="接入 akshare 后可展示实时新闻")]
    _NEWS_CACHE[normalized] = (items, time.time())
    return items


def today_shanghai_str() -> str:
    return datetime.now(SH_TZ).date().isoformat()
