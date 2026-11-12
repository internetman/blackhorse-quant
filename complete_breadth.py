"""Verified full-market MA20/MA50 from same-cutoff forward-adjusted daily bars.

Dapanyuntu supplies the current Shanghai/Shenzhen universe and industry labels.
Tencent qfq daily bars are primary; Eastmoney fqt=1 is a bounded fallback.
Never stitch cached bars across adjustment reference dates or use raw stock bars.
"""
from __future__ import annotations
import concurrent.futures
import datetime as dt
import hashlib
import json
import math
import statistics
import threading
import time
import os
import tempfile
import urllib.parse
from collections import Counter, defaultdict
from pathlib import Path

from market_breadth import ROOT, ZONE, atomic_json, fetch, summarize

VERSION = 'qfq-shsz-v1'
_HTTP = threading.local()

def fetch_history(url):
    # One connection pool per worker. Normal TLS verification/proxy routing remain enabled.
    import requests
    if not hasattr(_HTTP, 'session'):
        _HTTP.session = requests.Session()
        _HTTP.session.headers.update({'User-Agent': 'Mozilla/5.0', 'Referer': 'https://quote.eastmoney.com/'})
    last = None
    for attempt in range(2):
        try:
            response = _HTTP.session.get(url, timeout=(8, 8))
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            last = exc
            if attempt == 0:
                time.sleep(.5)
    raise ValueError(f'Daily history request failed: {type(last).__name__}')

def save_history(path, data):
    # Unique temporary files also make concurrent read-only verification runs safe.
    fd, name = tempfile.mkstemp(prefix=path.name+'.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)

BENCHMARKS = [('1.000001', '上证指数'), ('1.000300', '沪深300'),
              ('1.000852', '中证1000'), ('0.399006', '创业板指'), ('1.000688', '科创50')]


def number(value):
    try:
        n = float(value)
    except (TypeError, ValueError):
        raise ValueError('Invalid numeric bar field')
    if not math.isfinite(n):
        raise ValueError('Nonfinite bar field')
    return n


def parse_tencent(payload, symbol, cutoff, index=False):
    if payload.get('code') != 0:
        raise ValueError('Tencent did not report success')
    node = (payload.get('data') or {}).get(symbol)
    if not isinstance(node, dict):
        raise ValueError('Wrong security identity')
    key = 'day' if index else 'qfqday'
    raw = node.get(key)
    if not raw:
        raise ValueError('Required adjusted stock bars/index bars not supplied')
    result = []
    for row in raw:
        if not isinstance(row, list) or len(row) < 6:
            raise ValueError('Malformed Tencent daily bar')
        result.append(dict(date=row[0], close=number(row[2]), volume=number(row[5])))
    return validate_bars(result, cutoff)


def parse_eastmoney(payload, code, cutoff, market=None):
    node = payload.get('data') or {}
    if str(node.get('code')) != code or not node.get('klines'):
        raise ValueError('Wrong security identity or missing daily bars')
    if market is not None and node.get('market') != int(market):
        raise ValueError('Wrong security market identity')
    result = []
    for line in node['klines']:
        v = line.split(',')
        if len(v) < 6:
            raise ValueError('Malformed Eastmoney daily bar')
        result.append(dict(date=v[0], close=number(v[2]), volume=number(v[5])))
    return validate_bars(result, cutoff)


def validate_bars(rows, cutoff):
    if not rows:
        raise ValueError('No daily history')
    dates = [r['date'] for r in rows]
    for date in dates:
        if dt.date.fromisoformat(date).isoformat() != date or date > cutoff:
            raise ValueError('Future or invalid daily-bar date')
    if dates != sorted(set(dates)):
        raise ValueError('Unsorted or duplicate daily bars')
    if any(r['close'] <= 0 or r['volume'] < 0 for r in rows):
        raise ValueError('Invalid daily close or volume')
    if dates[-1] != cutoff:
        raise ValueError('Daily bars do not reach expected completed close')
    return rows


def get_history(stock, cutoff, cache, index=False):
    secid, code = stock['secid'], stock['code']
    symbol = ('sh' if secid.startswith('1.') else 'sz') + code
    path = cache / f'{secid}.json'
    if path.exists():
        try:
            saved = json.loads(path.read_text())
            raw = json.dumps(saved['response'], ensure_ascii=False, sort_keys=True, separators=(',', ':'))
            if (saved.get('cutoff') != cutoff or saved.get('version') != VERSION or saved.get('symbol') != symbol
                    or saved.get('adjustment') != ('index' if index else 'qfq')
                    or saved.get('provider') not in ('Tencent', 'Eastmoney')
                    or hashlib.sha256(raw.encode()).hexdigest() != saved.get('sha256')):
                raise ValueError('Cache identity or digest mismatch')
            rows = (parse_tencent(saved['response'], symbol, cutoff, index) if saved['provider'] == 'Tencent'
                    else parse_eastmoney(saved['response'], code, cutoff, secid.split('.')[0]))
            return rows, saved['provider'], saved['sha256']
        except (ValueError, TypeError, KeyError, OSError, AttributeError, IndexError):
            pass  # A corrupt or incompatible cache is a miss, never valid data.
    start = (dt.date.fromisoformat(cutoff) - dt.timedelta(days=280)).isoformat()
    qq = 'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?' + urllib.parse.urlencode(
        {'param': f'{symbol},day,{start},{cutoff},180,qfq'})
    em = 'https://push2his.eastmoney.com/api/qt/stock/kline/get?' + urllib.parse.urlencode(dict(
        secid=secid, klt=101, fqt=1, lmt=180, end=cutoff.replace('-', ''),
        fields1='f1,f2,f3,f4,f5,f6', fields2='f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61'))
    providers = [('Eastmoney', em), ('Tencent', qq)] if index else [('Tencent', qq), ('Eastmoney', em)]
    errors = []
    for provider, url in providers:
        try:
            response = fetch_history(url)
            rows = parse_tencent(response, symbol, cutoff, index) if provider == 'Tencent' else parse_eastmoney(response, code, cutoff, secid.split('.')[0])
            raw = json.dumps(response, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
            digest = hashlib.sha256(raw.encode()).hexdigest()
            save_history(path, dict(version=VERSION, cutoff=cutoff, symbol=symbol, provider=provider,
                                  adjustment='index' if index else 'qfq', effectiveKey=('day' if index else 'qfqday') if provider=='Tencent' else 'klines:fqt=1', requestUrl=url,
                                  collectedAt=dt.datetime.now(ZONE).isoformat(timespec='seconds'),
                                  sha256=digest, response=response))
            return rows, provider, digest
        except Exception as exc:
            errors.append(f'{provider}: {type(exc).__name__}: {str(exc)[:100]}')
    raise ValueError('; '.join(errors))


def stock_universe(base, cache):
    """Resolve the frozen source universe, including on a cold cloud runner."""
    cutoff = base['asOf']
    declared = base.get('dailyHistory', {}).get('stockCount', base['latestHistoryCount'])
    retained = base.get('dailyHistory', {}).get('sourceStocks')
    if retained:
        stocks = {s['code']: s for s in retained}
        if len(stocks) != len(retained) or len(stocks) != declared or any(
                not s['code'].isdigit() or len(s['code']) != 6
                or s['code'][0] not in '036' or s['secid'] != ('1.' if s['code'].startswith('6') else '0.')+s['code']
                or s['close'] <= 0 or not math.isfinite(s['close']) for s in retained):
            raise ValueError('Invalid retained source universe')
        return list(stocks.values())
    cache.mkdir(parents=True, exist_ok=True)
    quote_file = cache/f'quotes-{cutoff}.json'
    quotes = json.loads(quote_file.read_text()) if quote_file.exists() else fetch('https://beta.dapanyuntu.com/api/heatmap/quotes?period=day', attempts=2, timeout=10)
    from refresh_public_breadth import require_closed_quote
    require_closed_quote(quotes['updatedAt'], cutoff)
    symbols = {code.split('.')[0] for code, q in quotes['quotes'].items() if code.endswith(('.SH','.SZ'))
               and isinstance(q.get('price'),(int,float)) and math.isfinite(q['price']) and q['price']>0
               and isinstance(q.get('changePct'),(int,float)) and math.isfinite(q['changePct'])}
    if not quote_file.exists():
        atomic_json(quote_file, quotes)
    cached = []
    for file in sorted(cache.glob(f'{cutoff}-industry-*.json')):
        try:
            data = json.loads(file.read_text())
            if data.get('date') == cutoff:
                cached.append(data)
        except (ValueError, OSError):
            pass
    by_industry = {d['industry']: d for d in cached}
    stocks = {}
    for idx, sector in enumerate(base['rows']):
        industry = sector['industry']
        data = by_industry.get(industry)
        if data is None:
            query = urllib.parse.urlencode(dict(industry=industry,date=cutoff))
            data = fetch('https://sckd.dapanyuntu.com/api/api/stock_daily_data_by_industry_and_date?'+query, attempts=2, timeout=10)
            if data.get('date') != cutoff or data.get('industry') != industry:
                raise ValueError('Cold source universe date/industry mismatch')
            # Separate identity from the source collector's numeric cache indices.
            atomic_json(cache/f'cold-{cutoff}-industry-{idx:03d}.json', data)
        for row in data['data']:
            raw_code = number(row['stock_code'])
            if not raw_code.is_integer() or not 0 <= raw_code <= 999999:
                raise ValueError('Invalid source stock code')
            code = f'{int(raw_code):06d}'
            if code not in symbols or code[0] not in '036':
                continue  # Beijing shares are excluded from this frozen scope.
            close, change = row.get('close_price'), row.get('change_percent')
            if not isinstance(close, (float, int)) or not math.isfinite(close) or close <= 0 or not isinstance(change, (float, int)) or not math.isfinite(change):
                continue
            if row.get('date') != cutoff or row.get('industry') != industry or code in stocks:
                raise ValueError('Duplicate or mixed source universe')
            stocks[code] = dict(code=code, secid=('1.' if code.startswith('6') else '0.')+code,
                                industry=industry, close=close)
    if len(stocks) != declared:
        raise ValueError('Daily-bar universe does not match the frozen verified source count')
    return list(stocks.values())


def build_snapshot(base, stocks, histories, benchmarks, failures):
    cutoff, n = base['asOf'], base['universeCount']
    by_date, by_sector = defaultdict(list), defaultdict(list)
    provider_counts, manifests, mismatches = Counter(), [], []
    for stock in stocks:
        item = histories.get(stock['code'])
        if not item:
            continue
        rows, provider, digest = item
        validate_bars(rows, cutoff)
        if abs(rows[-1]['close']/stock['close']-1) > .005:
            mismatches.append(stock['code'])
            continue
        provider_counts[provider] += 1
        manifests.append(dict(code=stock['code'], industry=stock['industry'], provider=provider,
                              firstDate=rows[0]['date'], lastDate=rows[-1]['date'], bars=len(rows), sha256=digest))
        for i, row in enumerate(rows):
            if row['date'] not in base['dates'] or row['volume'] <= 0 or i == 0:
                continue
            sample = dict(close=row['close'], pct=round((row['close']/rows[i-1]['close']-1)*100, 6))
            for period in (20, 50):
                sample[f'ma{period}'] = statistics.mean(r['close'] for r in rows[i-period+1:i+1]) if i+1 >= period else None
            by_date[row['date']].append(sample)
            by_sector[(stock['industry'], row['date'])].append(sample)
    # Each date has its own auditable denominator; low-coverage dates stay null.
    market = []
    for date in base['dates']:
        row = dict(date=date, **summarize(by_date[date]))
        for metric in ('ma20', 'ma50'):
            if row[metric]['valid']/n < .95:
                row[metric]['pct'] = None
                row[metric]['insufficientCoverage'] = True
        market.append(row)
    latest = market[-1]
    if any(latest[m]['pct'] is None for m in ('ma20', 'ma50')):
        raise ValueError(f"Same-date MA20/MA50 coverage below 95%: {latest['ma20']['valid']}/{n}, {latest['ma50']['valid']}/{n}")
    if len(mismatches)/max(1, len(histories)) > .01:
        raise ValueError('Adjusted latest closes disagree with verified source by over 0.5% for >1% of stocks')
    if len(benchmarks) != 5 or {b.get('secid') for b in benchmarks} != {s for s, _ in BENCHMARKS} or any(
            b.get('asOf') != cutoff or not all(isinstance(b.get(k), (int,float)) and math.isfinite(b[k]) for k in ('close','ma50','ma50Slope20')) for b in benchmarks):
        raise ValueError('Five same-date benchmark histories are required')
    sectors = []
    sector_sizes = Counter(s['industry'] for s in stocks)
    for industry in sorted(sector_sizes):
        series = []
        for date in base['dates']:
            row = dict(date=date, **summarize(by_sector[(industry,date)]))
            for m in ('ma20','ma50'):
                if row[m]['valid']/sector_sizes[industry] < .95:
                    row[m]['pct'] = None
                    row[m]['insufficientCoverage'] = True
            series.append(row)
        values = [r['ma20']['pct'] for r in series]
        recent, prior = values[-5:], values[-10:-5]
        complete = lambda v: len(v)==5 and all(x is not None for x in v)
        sectors.append(dict(industry=industry,series=series,latest=values[-1],
                            avg5=round(statistics.mean(recent),2) if complete(recent) else None,
                            slope5=round(statistics.mean(recent)-statistics.mean(prior),2) if complete(recent) and complete(prior) else None,
                            days70=sum(v is not None and v>=70 for v in values), daysTotal=sum(v is not None for v in values),isCurrentR02=False))
    result = dict(base)
    result.update(scopeVersion=VERSION, expectedCloseDate=cutoff, availableMetrics=['ma20','ma50'], market=market, rows=sectors,
                  generatedAt=dt.datetime.now(ZONE).isoformat(timespec='seconds'),
                  historyCount=len(manifests), latestHistoryCount=latest['n'], coveragePct=round(latest['n']/n*100,2),
                  providerCounts=dict(provider_counts), benchmarks=benchmarks,
                  source='大盘云图沪深名单/东财行业；腾讯前复权日K为主、东方财富前复权日K备用；本地等权计算MA20/MA50',
                  method='沪深A股，含ST、不含北交所。当前已核验名单回溯，存在存续样本偏差。每只股票MA20/MA50与收盘价来自同一提供商、同一截止日的前复权完整序列，不跨复权基日拼接；指数使用指数原始点位。收盘价严格大于均线才算站上；剔除当日零成交、历史不足或日K缺失。最新MA20、MA50有效分母各自至少覆盖沪深名单95%；历史日与行业不足95%则留空。最新日K收盘与sckd收盘交叉校验，偏差超过0.5%的样本排除，超1%则整批拒绝。行业为当前86东财分类；不拼接旧MA20来源的历史比例。未独立重建除权因子，依赖提供商明确的前复权序列。指数确认须5个指数同日且至少70条历史，缺失不算通过。',
                  dailyHistory=dict(adjustment='qfq',cutoff=cutoff,stockCount=len(stocks),sourceStocks=stocks,validHistories=len(manifests),
                                    failedStocks=failures,priceMismatchCodes=mismatches,manifest=manifests),
                  verification=dict(base.get('verification',{}),dailyHistoryFailures=len(failures),dailyHistoryMismatches=len(mismatches)))
    return result


def collect(days=6, workers=4, expected=None):
    import requests  # Fail before collection if deployment missed the explicit dependency.
    from refresh_public_breadth import collect as collect_ma20
    from trading_calendar import expected_close
    allowed = expected_close()
    expected = expected or allowed
    if expected > allowed:
        raise ValueError('Refusing future or incomplete close')
    target = ROOT/'market-breadth.json'
    base = json.loads(target.read_text()) if target.exists() else None
    if base and base.get('asOf') == expected:
        from daily_breadth import validate_snapshot
        validate_snapshot(base, expected)
    else:
        base = collect_ma20(days=days, workers=workers, expected=expected)
    cutoff = base['asOf']
    stocks = stock_universe(base, ROOT/'output'/'public-breadth-cache')
    cache = ROOT/'output'/'qfq-breadth-cache'/cutoff
    cache.mkdir(parents=True, exist_ok=True)
    histories, failures, benchmarks = {}, [], []
    for secid, name in BENCHMARKS:
        stock = dict(secid=secid, code=secid.split('.')[1])
        rows, provider, digest = get_history(stock, cutoff, cache, index=True)
        if len(rows) < 70:
            raise ValueError(f'{name}: fewer than 70 index bars')
        closes = [r['close'] for r in rows]
        avg, prior = statistics.mean(closes[-50:]), statistics.mean(closes[-70:-20])
        benchmarks.append(dict(secid=secid,name=name,asOf=rows[-1]['date'],close=closes[-1],ma50=round(avg,6),
                               ma50Slope20=round((avg/prior-1)*100,6),provider=provider,historyCount=len(rows),sha256=digest))
    print(f'Collecting adjusted histories: {len(stocks)} stocks; {len(benchmarks)}/5 indices verified', flush=True)
    # Bound active upstream requests; cache every successful complete response.
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        def one(stock):
            try:
                return stock, get_history(stock, cutoff, cache)
            except Exception as exc:
                return stock, str(exc)[:250]
        for count, (stock, item) in enumerate(pool.map(one, stocks), 1):
            if isinstance(item, str): failures.append(dict(code=stock['code'],error=item))
            else: histories[stock['code']] = item
            if count % 250 == 0:
                print(f'Adjusted history {count}/{len(stocks)}; failures={len(failures)}', flush=True)
    result = build_snapshot(base,stocks,histories,benchmarks,failures)
    from daily_breadth import validate_snapshot
    return validate_snapshot(result, cutoff)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--expected')
    p.add_argument('--workers', type=int, choices=range(1, 9), default=4)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    Path(str(args.output)+'.pid').write_text(str(os.getpid()))
    result = collect(workers=args.workers, expected=args.expected)
    atomic_json(args.output, result)
    print(json.dumps({k:result[k] for k in ['asOf','generatedAt','coveragePct','providerCounts','benchmarks']}, ensure_ascii=False), flush=True)
