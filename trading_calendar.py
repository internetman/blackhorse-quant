"""Exchange holidays, shared with the browser; unknown years fail closed."""
from __future__ import annotations
import datetime as dt
import json
import re
from html import unescape
from pathlib import Path

from market_breadth import ROOT, ZONE, atomic_json, fetch

CALENDAR = ROOT / 'market-trading-calendar.json'
ANNUAL_PAGE = 'https://www.sse.com.cn/disclosure/dealinstruc/closed/'


def parse_annual_page(html, year):
    text = unescape(re.sub(r'<[^>]+>', '', html))
    start = text.find(f'{year}年休市安排')
    if start < 0:
        raise ValueError(f'Official exchange calendar for {year} is not available')
    section = text[start:].split('相关公告')[0]
    names = ['元旦', '春节', '清明节', '劳动节', '端午节', '中秋节', '国庆节']
    closures = []
    for name in names:
        match = re.search(name + r'\s*[：:]\s*(\d+)月(\d+)日[^至]*至\s*(?:(\d+)月)?(\d+)日', section)
        if not match:
            raise ValueError(f'Cannot safely parse {year} exchange closure: {name}')
        month, day, end_month, end_day = match.groups()
        first = dt.date(year, int(month), int(day))
        last = dt.date(year, int(end_month or month), int(end_day))
        if not first <= last or (last-first).days > 14:
            raise ValueError('Invalid official holiday interval')
        closures.append([first.isoformat(), last.isoformat()])
    return dict(source=ANNUAL_PAGE, closures=closures)


def load_calendar(path=CALENDAR, year=None, allow_fetch=False):
    path = Path(path)
    data = json.loads(path.read_text())
    if year is not None and str(year) not in data['years']:
        if not allow_fetch:
            raise ValueError(f'Exchange calendar for {year} has not been verified')
        # No guessed future holidays. Accept only a fully parsed official page.
        import subprocess
        html = subprocess.run(['curl', '--fail', '--silent', '--show-error', '--location',
                               '--max-time', '15', '--user-agent', 'Mozilla/5.0', ANNUAL_PAGE],
                              capture_output=True, text=True, check=True, timeout=17).stdout
        data['years'][str(year)] = parse_annual_page(html, year)
        atomic_json(path, data)
    return data


def is_trading_day(date, calendar):
    year = calendar['years'].get(str(date.year))
    if year is None:
        raise ValueError(f'Exchange calendar for {date.year} has not been verified')
    day = date.isoformat()
    return date.weekday() < 5 and not any(a <= day <= b for a, b in year['closures'])


def expected_close(now=None, calendar=None):
    now = (now or dt.datetime.now(ZONE)).astimezone(ZONE)
    calendar = calendar or load_calendar(year=now.year)
    date = now.date() if now.hour >= 16 else now.date()-dt.timedelta(days=1)
    for _ in range(35):
        if is_trading_day(date, calendar):
            return date.isoformat()
        date -= dt.timedelta(days=1)
    raise ValueError('Cannot determine a verified recent trading session')
