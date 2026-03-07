"""
Real-world Data Engine using AkShare and yfinance
"""
import asyncio
import random
import os
from datetime import datetime
from typing import Dict, List, Optional
import akshare as ak
import yfinance as yf
import pandas as pd
from app.store import store
from app.models import Position, Trade

# Cache for real prices to avoid hitting API rate limits too hard
PRICE_CACHE = {}

def get_real_price(symbol: str) -> Optional[float]:
    """
    Fetch real-time price for a given symbol.
    Supports A-share (e.g., 600036), HK-share (e.g., 00700), and US-share (e.g., TSLA).
    """
    try:
        # A-share detection (6 digits)
        if len(symbol) == 6 and symbol.isdigit():
            # For A-shares, we can use akshare
            df = ak.stock_bid_ask_em(symbol=symbol)
            if not df.empty:
                return float(df['买一'].iloc[0]) # Use Bid 1 as proxy for current price
        
        # HK-share (5 digits) or US-share
        # yfinance is better for these
        ticker_map = {
            "00700": "0700.HK",
            "09988": "9988.HK",
            "TSLA": "TSLA",
            "NVDA": "NVDA",
            "GOOGL": "GOOGL",
            "AAPL": "AAPL",
            "MSFT": "MSFT",
            "AMZN": "AMZN",
            "META": "META"
        }
        yf_symbol = ticker_map.get(symbol, symbol)
        
        # Simple cache logic
        now = datetime.now()
        if yf_symbol in PRICE_CACHE:
            last_val, last_time = PRICE_CACHE[yf_symbol]
            if (now - last_time).total_seconds() < 60:
                return last_val

        ticker = yf.Ticker(yf_symbol)
        # fast_info is quicker for just the price
        price = ticker.fast_info['last_price']
        PRICE_CACHE[yf_symbol] = (price, now)
        return price
        
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
        return None

async def update_positions_real():
    """Update position prices and P&L using real data."""
    positions = store.get_positions()
    if not positions:
        return
    
    updated_positions = []
    for pos in positions:
        # Extract symbol from "Name (Symbol)" format
        import re
        match = re.search(r'\((.*?)\)', pos.asset)
        symbol = match.group(1) if match else pos.asset
        
        real_price = get_real_price(symbol)
        if real_price is None:
            # Fallback to current price if API fails, DON'T use random jitter
            try:
                real_price = float(pos.currentPrice.replace(',', ''))
            except:
                real_price = entry # Ultimate fallback

        entry = float(pos.entryPrice.replace(',', ''))
        qty = float(pos.amount.replace(',', ''))
        
        if pos.side == '多':
            pnl_percent = ((real_price - entry) / entry) * 100
        else:
            pnl_percent = ((entry - real_price) / entry) * 100
        
        pnl_value = (real_price - entry) * qty * (1 if pos.side == '多' else -1)
        
        pnl_str = f"{'+' if pnl_percent >= 0 else ''}{pnl_percent:.2f}%"
        pnl_value_str = f"{'+' if pnl_value >= 0 else ''}¥{abs(int(pnl_value)):,}"
        
        updated = Position(
            id=pos.id,
            asset=pos.asset,
            side=pos.side,
            amount=pos.amount,
            entryPrice=pos.entryPrice,
            currentPrice=f"{real_price:,.2f}",
            pnl=pnl_str,
            pnlValue=pnl_value_str
        )
        updated_positions.append(updated)
    
    store.set_positions(updated_positions)

async def check_signals_and_trade():
    """Analyze watchlist for signals and generate trades."""
    # Simplified logic: If RSI < 30 or Price crosses MA, generate a trade.
    # For now, we'll keep it simple to show we are "learning" the market.
    pass

async def engine_loop():
    """Main engine loop."""
    print("🚀 BlackHorse Real-Data Engine Started")
    while True:
        try:
            sys_status = store.get_status()
            await update_positions_real()
            
            if sys_status == 'running':
                await check_signals_and_trade()
            
            await asyncio.sleep(10) # Update every 10 seconds to stay under rate limits
            
        except Exception as e:
            print(f"Engine Loop Error: {e}")
            await asyncio.sleep(5)
