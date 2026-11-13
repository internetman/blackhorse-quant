"""Eastmoney board index identity and completed-session window validation."""
import datetime as dt
import math
import re
from trading_calendar import load_calendar, is_trading_day, expected_close


def completed_dates(count=10, *, now=None, calendar=None):
    if count != 10:raise ValueError('Board trend requires exactly 10 completed sessions')
    calendar=calendar or load_calendar(allow_fetch=False)
    cutoff=expected_close(now,calendar)
    day=dt.date.fromisoformat(cutoff);days=[]
    for _ in range(90):
        if is_trading_day(day,calendar):days.append(day.isoformat())
        if len(days)==count:return list(reversed(days))
        day-=dt.timedelta(days=1)
    raise ValueError('Cannot establish ten official trading sessions')


def validate_rows(rows, dates):
    if not isinstance(rows,list) or [r.get('date') for r in rows]!=dates:
        raise ValueError('Board daily bars do not match ten completed exchange sessions')
    for row in rows:
        for key in ('open','close','high','low','volume','amountYi','amplitude','pct','change','turnover'):
            value=row.get(key)
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
                raise ValueError('Missing/nonfinite board bar field')
        if min(row[k] for k in ('open','close','high','low'))<=0 or row['volume']<0 or row['amountYi']<0:
            raise ValueError('Invalid board index price or volume')
        if row['high']<max(row['open'],row['close'],row['low']) or row['low']>min(row['open'],row['close'],row['high']):
            raise ValueError('Inconsistent board OHLC')
    return rows


def parse_board_history(payload,code,dates):
    if not re.fullmatch(r'BK[0-9]{4}',code):raise ValueError('Invalid Eastmoney board code')
    node=payload.get('data') or {}
    if payload.get('rc')!=0 or node.get('code')!=code or node.get('market')!=90:
        raise ValueError('Wrong board response identity or unsuccessful response')
    raw=node.get('klines')
    if not isinstance(raw,list) or not raw:raise ValueError('Missing board daily history')
    rows=[];all_dates=[]
    for line in raw:
        v=line.split(',')
        if len(v)<11:raise ValueError('Malformed board daily history')
        date=dt.date.fromisoformat(v[0]).isoformat()
        if date!=v[0] or date>dates[-1]:raise ValueError('Future or intraday bar cannot substitute for completed close')
        values=[float(x) for x in v[1:11]]
        row=dict(zip(('open','close','high','low','volume','amountYi','amplitude','pct','change','turnover'),values))
        row.update(date=date);row['amountYi']/=100000000
        rows.append(row);all_dates.append(date)
    if all_dates!=sorted(set(all_dates)):raise ValueError('Duplicate or unordered board dates')
    return validate_rows(rows[-10:],dates)
