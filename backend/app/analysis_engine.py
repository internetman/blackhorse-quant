"""
动态生成买卖建议：基于 akshare K 线 + 技术指标（MA/RSI/MACD），
产出 action、bias、pricePlan、reasons、risks，按 symbol+交易日 缓存。
"""
from __future__ import annotations

import os
import time
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from app.models import Recommendation
from app.market_data import (
    get_quote_data,
    normalize_symbol,
    symbol_to_code,
    today_shanghai_str,
)

try:
    import akshare as ak  # type: ignore
except Exception:
    ak = None

SH_TZ = ZoneInfo("Asia/Shanghai")
USE_AKSHARE = os.getenv("USE_AKSHARE", "true").lower() == "true"
CACHE_TTL_SECONDS = int(os.getenv("ANALYSIS_CACHE_TTL_SECONDS", "3600"))  # 1h
_REC_CACHE: dict[str, tuple[Recommendation, float]] = {}


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, float("nan"))
    return (100 - (100 / (1 + rs))).fillna(50)


def _macd_cross(dif: pd.Series, dea: pd.Series) -> str:
    """最近一根 K 线：golden / death / none"""
    if len(dif) < 2 or len(dea) < 2:
        return "none"
    prev = dif.iloc[-2] - dea.iloc[-2]
    curr = dif.iloc[-1] - dea.iloc[-1]
    if prev <= 0 and curr > 0:
        return "golden"
    if prev >= 0 and curr < 0:
        return "death"
    return "none"


def _fetch_hist(symbol: str) -> pd.DataFrame | None:
    if not USE_AKSHARE or ak is None:
        return None
    code = symbol_to_code(symbol)
    try:
        df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
        if df is None or df.empty or len(df) < 60:
            return None
        df = df.rename(columns={"日期": "date", "开盘": "open", "收盘": "close", "最高": "high", "最低": "low", "成交量": "volume"})
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        return df.tail(120)
    except Exception:
        return None


def _decide(price: float, ma5: float, ma20: float, ma60: float, rsi: float, macd_cross: str) -> tuple[str, str, str]:
    """返回 (action, bias, confidence)."""
    if price <= 0 or ma20 <= 0:
        return "观望", "暂不参与", "低"
    if rsi < 30 and price > ma60:
        return "可交易", "偏低吸", "高"
    if rsi > 70 or (macd_cross == "death" and price < ma20):
        return "风险升高", "偏减仓", "高"
    if macd_cross == "golden" and price > ma20 and rsi < 65:
        return "可交易", "偏低吸", "高"
    if price > ma20 and price > ma60 and rsi < 55:
        return "可交易", "偏突破", "中"
    if price < ma20 and rsi > 55:
        return "观望", "暂不参与", "中"
    return "观望", "暂不参与", "低"


def _build_price_plan(price: float, low20: float, high20: float, action: str, bias: str) -> str:
    """以当前价为基准生成价格区间文案."""
    if price <= 0:
        return "暂无足够数据，请等待更多交易日。"
    pct = 0.02
    support = round(price * (1 - pct), 2)
    resistance = round(price * (1 + pct), 2)
    stop = round(price * (1 - 0.03), 2)
    if low20 > 0 and high20 > 0:
        support = round(min(support, low20 * 0.998), 2)
        resistance = round(max(resistance, high20 * 1.002), 2)
    if action == "可交易":
        if bias == "偏低吸":
            return f"关注 {support}-{price:.0f} 区间低吸，止盈参考 {resistance}，跌破 {stop} 离场"
        return f"突破 {resistance} 可跟进，目标 {round(resistance * 1.02, 2)}，跌破 {support} 止损"
    if action == "风险升高":
        return f"反弹至 {resistance} 可考虑减仓，跌破 {support} 需果断止损"
    return f"观望区间 {support}-{resistance}，等待方向明确后再操作"


def generate_recommendation(symbol: str, name: str = "") -> Recommendation:
    """对单只股票生成当日建议，带 symbol+交易日 缓存."""
    normalized = normalize_symbol(symbol)
    code = symbol_to_code(symbol)
    display_name = name or code
    trade_date = today_shanghai_str()
    cache_key = f"{normalized}_{trade_date}"
    now = time.time()
    if cache_key in _REC_CACHE:
        rec, ts = _REC_CACHE[cache_key]
        if now - ts <= CACHE_TTL_SECONDS:
            return rec

    quote = get_quote_data(symbol)
    price = quote.latestPrice if quote else 0.0

    df = _fetch_hist(symbol)
    if df is None or df.empty:
        fallback = Recommendation(
            id=f"rec_{uuid.uuid4().hex[:12]}",
            symbol=normalized,
            name=display_name,
            date=trade_date,
            action="观望",
            bias="暂不参与",
            confidence="低",
            pricePlan="K 线数据不足，请等待更多交易日后查看建议。",
            summary="暂无足够历史数据生成建议。",
            reasons=[],
            risks=["数据不足，建议谨慎参考"],
            invalidCondition="数据充足后重新生成",
            reviewAt="T+1",
            generatedAt=datetime.now(SH_TZ).isoformat(),
        )
        _REC_CACHE[cache_key] = (fallback, now)
        return fallback

    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    ma5 = close.rolling(5).mean().iloc[-1] if len(close) >= 5 else price
    ma20 = close.rolling(20).mean().iloc[-1] if len(close) >= 20 else price
    ma60 = close.rolling(60).mean().iloc[-1] if len(close) >= 60 else price
    rsi_val = _rsi(close, 14).iloc[-1] if len(close) >= 14 else 50.0
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    macd_cross = _macd_cross(dif, dea)
    low20 = low.rolling(20).min().iloc[-1] if len(low) >= 20 else 0
    high20 = high.rolling(20).max().iloc[-1] if len(high) >= 20 else 0

    current = close.iloc[-1] if len(close) else price
    if price <= 0:
        price = current

    action, bias, confidence = _decide(price, ma5, ma20, ma60, rsi_val, macd_cross)
    price_plan = _build_price_plan(price, low20, high20, action, bias)

    reasons: list[str] = []
    if rsi_val < 35:
        reasons.append(f"RSI={rsi_val:.0f} 进入超卖区间，性价比回升")
    elif rsi_val > 65:
        reasons.append(f"RSI={rsi_val:.0f} 偏高，注意追涨风险")
    if price > ma20:
        reasons.append("价格站上 20 日均线，短期趋势偏多")
    elif price < ma20:
        reasons.append("价格在 20 日均线下方，短期承压")
    if macd_cross == "golden":
        reasons.append("MACD 金叉，技术面偏多")
    elif macd_cross == "death":
        reasons.append("MACD 死叉，技术面偏空")
    if not reasons:
        reasons.append("多空均衡，等待更明确信号")

    risks: list[str] = []
    if rsi_val > 70:
        risks.append("RSI 超买，短期回调风险")
    if price < ma60:
        risks.append("处于 60 日均线下方，中期趋势偏弱")
    if not risks:
        risks.append("大盘波动可能影响个股")

    summary_map = {
        ("可交易", "偏低吸"): "回落至支撑位附近，可轻仓低吸试错。",
        ("可交易", "偏突破"): "放量测试前高，突破概率较大。",
        ("风险升高", "偏减仓"): "连续下跌后反弹乏力，风险信号增多。",
        ("观望", "暂不参与"): "横盘震荡中，无明确方向，等待突破或回调确认。",
    }
    summary = summary_map.get((action, bias), "多空分歧，建议观望。")

    invalid_map = {
        "可交易": "若跌破支撑或放量破位，结论转为观望或减仓",
        "风险升高": "若强势收复均线并放量，风险预警可解除",
        "观望": "若放量突破关键压力或跌破支撑，结论将更新",
    }
    invalid_condition = invalid_map.get(action, "根据盘面变化及时调整")

    rec = Recommendation(
        id=f"rec_{uuid.uuid4().hex[:12]}",
        symbol=normalized,
        name=display_name,
        date=trade_date,
        action=action,
        bias=bias,
        confidence=confidence,
        pricePlan=price_plan,
        summary=summary,
        reasons=reasons,
        risks=risks,
        invalidCondition=invalid_condition,
        reviewAt="T+1",
        generatedAt=datetime.now(SH_TZ).isoformat(),
    )
    _REC_CACHE[cache_key] = (rec, now)
    return rec
