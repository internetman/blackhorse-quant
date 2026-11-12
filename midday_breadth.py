"""Separate, provisional lunch-break breadth. Never writes completed daily bars.

Requires a verified previous exchange close and same-response Tencent qfq history
and noon quote. A quote is not a completed daily bar. No publication by this CLI.
"""
from __future__ import annotations
import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import math
import statistics
import urllib.parse
from collections import Counter, defaultdict
from pathlib import Path

from market_breadth import ROOT, ZONE, atomic_json, summarize
from complete_breadth import VERSION, fetch_history, parse_tencent, stock_universe
from daily_breadth import read_json, run_lock, validate_snapshot
from refresh_public_breadth import BETA, quote_timestamp
from trading_calendar import expected_close, is_trading_day, load_calendar

MIDDAY_VERSION = 'qfq-shsz-midday-v1'
PRICE_TOLERANCE = .005001  # Half a CNY cent; excludes adjustment/quote mismatches.


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def noon_window(now, calendar):
    return is_trading_day(now.date(), calendar) and dt.time(11, 35) <= now.time().replace(tzinfo=None) < dt.time(12, 55)


def noon_stamp(value, day, observed=None):
    stamp = quote_timestamp(value)
    if stamp.date().isoformat() != day or not dt.time(11, 30) <= stamp.time().replace(tzinfo=None) < dt.time(13):
        raise ValueError('Quote is not a same-day lunch-break observation')
    if observed and stamp > observed + dt.timedelta(seconds=30):
        raise ValueError('Quote timestamp is in the future')
    return stamp


def verified_sources(quotes, overview, day, observed):
    noon_stamp(quotes['updatedAt'], day, observed)
    markets = {m['market']: m for m in overview['markets']}
    if not {'sse', 'szse'} <= markets.keys():
        raise ValueError('Missing Shanghai/Shenzhen universe counts')
    for key in ('sse', 'szse'):
        noon_stamp(markets[key]['updatedAt'], day, observed)
        if not isinstance(markets[key]['stockCount'], int) or markets[key]['stockCount'] <= 0:
            raise ValueError('Invalid exchange universe count')
    count = sum(markets[k]['stockCount'] for k in ('sse', 'szse'))
    clean = {symbol: q for symbol, q in quotes['quotes'].items()
             if symbol.endswith(('.SH', '.SZ')) and finite(q.get('price')) and q['price'] > 0
             and finite(q.get('changePct')) and finite(q.get('turnoverAmount')) and q['turnoverAmount'] > 0}
    if count < 4000 or len(clean) / count < .95:
        raise ValueError('Lunch quote coverage below 95%')
    return clean, count


def extract_sample(payload, stock, beta_quote, day, prior_close, observed):
    """Use 19/49 completed adjusted closes plus the verified provisional quote.

    qfqday may stop at yesterday, or contain an unfinished today row. The latter
    is discarded. qt previous-close must agree with the adjusted last close,
    otherwise today's corporate-action basis is ambiguous and stock is excluded.
    """
    symbol = ('sh' if stock['secid'].startswith('1.') else 'sz') + stock['code']
    node = (payload.get('data') or {}).get(symbol) or {}
    q = (node.get('qt') or {}).get(symbol)
    if not isinstance(q, list) or len(q) <= 30 or str(q[2]) != stock['code']:
        raise ValueError('Missing or wrong same-response stock quote')
    raw_stamp = q[30]
    if not isinstance(raw_stamp, str) or len(raw_stamp) != 14 or not raw_stamp.isdigit():
        raise ValueError('Missing per-stock quote timestamp')
    stamp = dt.datetime.strptime(raw_stamp, '%Y%m%d%H%M%S').replace(tzinfo=ZONE)
    noon_stamp(stamp.isoformat(), day, observed)
    price, previous, volume = (float(q[i]) for i in (3, 4, 6))
    if any(not math.isfinite(v) or v <= 0 for v in (price, previous, volume)):
        raise ValueError('Inactive or invalid noon quote')
    if abs(price - beta_quote['price']) > PRICE_TOLERANCE:
        raise ValueError('Frozen noon quote cross-check failed')
    raw = node.get('qfqday')
    if not isinstance(raw, list) or not raw or raw[-1][0] not in (prior_close, day):
        raise ValueError('Adjusted history does not reach the prior completed close')
    rows = parse_tencent(payload, symbol, raw[-1][0])
    rows = [r for r in rows if r['date'] < day]  # Never accept today's partial K as a close.
    if not rows or rows[-1]['date'] != prior_close:
        raise ValueError('Prior completed adjusted close missing')
    if abs(rows[-1]['close'] - previous) > PRICE_TOLERANCE:
        raise ValueError('Current quote previous-close and adjusted basis disagree')
    values = [r['close'] for r in rows]
    sample = dict(close=price, pct=100 * (price / previous - 1))
    # Cross-check exchange-adjusted percentage as well as last price.
    if abs(sample['pct'] - beta_quote['changePct']) > .10:
        raise ValueError('Noon percent-change reference disagrees')
    for period in (20, 50):
        sample[f'ma{period}'] = statistics.mean(values[-(period-1):] + [price]) if len(values) >= period-1 else None
    return sample, dict(code=stock['code'], industry=stock['industry'], quoteAt=stamp.isoformat(),
                        historyLastDate=rows[-1]['date'], completedBars=len(rows), adjustment='qfq',
                        previousClose=previous, price=price)


def build_snapshot(base, stocks, results, failures, quotes, universe_count, started, finished):
    day = started.date().isoformat()
    if finished.date() != started.date() or finished.time().replace(tzinfo=None) >= dt.time(13):
        raise ValueError('Collection crossed the afternoon open; discard noon result')
    samples, sectors, manifests = [], defaultdict(list), []
    for stock in stocks:
        if stock['code'] not in results:
            continue
        sample, manifest = results[stock['code']]
        samples.append(sample)
        sectors[stock['industry']].append(sample)
        manifests.append(manifest)
    market = summarize(samples)
    if any(market[key]['valid'] / universe_count < .95 for key in ('ma20', 'ma50')):
        raise ValueError(f"Noon MA20/MA50 coverage below 95%: {market['ma20']['valid']}/{universe_count}, {market['ma50']['valid']}/{universe_count}")
    sizes = Counter(s['industry'] for s in stocks)
    rows = []
    for name in sorted(sizes):
        summary = summarize(sectors[name])
        for metric in ('ma20', 'ma50'):
            if summary[metric]['valid'] / sizes[name] < .95:
                summary[metric]['pct'] = None
                summary[metric]['insufficientCoverage'] = True
        rows.append(dict(industry=name, membershipCount=sizes[name], **summary))
    result = dict(schemaVersion=1, scopeVersion=MIDDAY_VERSION, session='midday', barStatus='intraday',
        asOf=day, observedAt=quotes['updatedAt'], generatedAt=finished.isoformat(timespec='seconds'),
        startedAt=started.isoformat(timespec='seconds'), previousCloseDate=base['asOf'], membershipDate=base['asOf'],
        availableMetrics=['ma20', 'ma50'], universeLabel='沪深A股', excludedMarkets=['北交所'],
        universeCount=universe_count, membershipCount=len(stocks), latestHistoryCount=market['n'],
        coveragePct=round(100 * market['n'] / universe_count, 2), market=market, rows=rows,
        source='beta大盘云图午休报价与沪深数量；腾讯同响应前复权历史及逐股午休报价',
        method='午盘动态宽度，非收盘确认。逐股最近19/49个已完成前复权收盘价加当日午休最新价，计算动态MA20/MA50，严格大于均线为站上。腾讯午价与冻结beta午价交叉验证，同响应昨收与最后完整前复权收盘相差不超过半分；不能确认当日复权基准的样本剔除。有效分母须覆盖当日沪深总数95%。行业成员来自上一交易日已核验名单，含ST、不含北交所，新增/缺失/停牌/历史不足个股不伪造。独立保存，不写收盘历史、不参与R05收盘天气确认。',
        verification=dict(provider='Tencent', validStocks=len(manifests), failedStocks=failures,
                          quoteMinAt=min(m['quoteAt'] for m in manifests), quoteMaxAt=max(m['quoteAt'] for m in manifests),
                          manifest=manifests))
    return validate_midday(result, day)


def validate_midday(data, day, calendar=None):
    calendar = calendar or load_calendar(year=dt.date.fromisoformat(day).year)
    noon = dt.datetime.fromisoformat(day+'T12:00:00+08:00')
    if not is_trading_day(noon.date(), calendar) or data.get('previousCloseDate') != expected_close(noon, calendar):
        raise ValueError('Midday requires the immediately preceding exchange close')
    if data.get('schemaVersion') != 1 or data.get('scopeVersion') != MIDDAY_VERSION or data.get('session') != 'midday' or data.get('barStatus') != 'intraday' or data.get('asOf') != day:
        raise ValueError('Not an independently marked midday observation')
    noon_stamp(data['observedAt'], day)
    noon_stamp(data['generatedAt'], day)
    if data.get('previousCloseDate', day) >= day or data.get('membershipDate') != data['previousCloseDate']:
        raise ValueError('Invalid prior-close membership date')
    n = data.get('universeCount', 0)
    if n < 4000 or data.get('coveragePct', 0) < 95 or data.get('latestHistoryCount', 0)/n < .95:
        raise ValueError('Invalid midday coverage')
    if data.get('availableMetrics') != ['ma20', 'ma50'] or len(data.get('rows', [])) < 50:
        raise ValueError('Incomplete midday metrics/industries')
    for key in ('ma20', 'ma50'):
        m = data['market'][key]
        if not all(finite(m.get(k)) for k in ('valid','above','pct')) or m['valid']/n < .95 or not 0 <= m['above'] <= m['valid'] or abs(m['pct']-100*m['above']/m['valid']) > .011:
            raise ValueError('Invalid midday fraction')
    return data


def safe_shadow_output(path, root=ROOT):
    path, root = Path(path).resolve(), Path(root).resolve()
    if path.name in {'market-breadth.json', 'market-breadth-status.json', 'market-trading-calendar.json'} or any(path.is_relative_to(root/'output'/name) for name in ('breadth-history','qfq-breadth-cache','public-breadth-cache')):
        raise ValueError('Shadow output cannot overwrite completed-close files or caches')
    return path


def collect(root=ROOT, now=None, workers=4):
    root = Path(root)
    started = (now or dt.datetime.now(ZONE)).astimezone(ZONE)
    calendar = load_calendar(root/'market-trading-calendar.json', started.year, allow_fetch=False)
    if not noon_window(started, calendar):
        raise ValueError('Collect only on exchange trading days between 11:35 and 12:55 Beijing time')
    base = read_json(root/'market-breadth.json')
    prior = expected_close(started, calendar)
    validate_snapshot(base, prior)
    if base.get('scopeVersion') != VERSION:
        raise ValueError('Verified adjusted previous-close universe is required; no implicit MA50 upgrade')
    stocks = stock_universe(base, root/'output'/'public-breadth-cache')
    import requests
    with requests.Session() as session:
        session.headers.update({'User-Agent': 'Mozilla/5.0'})
        def public(path):
            response = session.get(BETA+path, timeout=(8, 15))
            response.raise_for_status()
            return response.json()
        quotes = public('/api/heatmap/quotes?period=day')
        overview = public('/api/heatmap/overview?period=day')
    day = started.date().isoformat()
    clean, n = verified_sources(quotes, overview, day, dt.datetime.now(ZONE))
    if abs(n/base['universeCount']-1) > .05:
        raise ValueError('Unexpected universe size change')
    # Separate evidence directory per run. No shared qfq daily cache is read/written.
    archive = root/'output'/'midday-evidence'/started.strftime('%Y%m%dT%H%M%S%f')
    archive.mkdir(parents=True, exist_ok=False)
    atomic_json(archive/'quotes.json', quotes)
    atomic_json(archive/'overview.json', overview)
    def one(stock):
        try:
            observed = dt.datetime.now(ZONE)
            if observed.date() != started.date() or observed.time().replace(tzinfo=None) >= dt.time(12, 55):
                raise ValueError('Noon collection deadline reached')
            symbol = ('sh' if stock['secid'].startswith('1.') else 'sz')+stock['code']
            beta = clean[stock['code']+('.SH' if stock['secid'].startswith('1.') else '.SZ')]
            url = 'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?'+urllib.parse.urlencode({'param':f'{symbol},day,,,180,qfq'})
            payload = fetch_history(url)
            observed = dt.datetime.now(ZONE)
            sample, manifest = extract_sample(payload, stock, beta, day, prior, observed)
            raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
            manifest['sha256'] = hashlib.sha256(raw.encode()).hexdigest()
            manifest['requestUrl'] = url
            atomic_json(archive/(stock['secid']+'.json'),dict(collectedAt=observed.isoformat(),response=payload,sha256=manifest['sha256']))
            return stock['code'], (sample, manifest)
        except (ValueError, TypeError, KeyError, IndexError, AttributeError, OSError) as exc:
            return stock['code'], str(exc)[:200]
    results, failures = {}, []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for count, (code, item) in enumerate(pool.map(one, stocks), 1):
            if isinstance(item, str): failures.append(dict(code=code, error=item))
            else: results[code] = item
            if count % 250 == 0: print(f'Midday {count}/{len(stocks)}; excluded={len(failures)}', flush=True)
    return build_snapshot(base, stocks, results, failures, quotes, n, started, dt.datetime.now(ZONE))


def refresh(root=ROOT, now=None, scheduled=False, force=False):
    root = Path(root)
    now = (now or dt.datetime.now(ZONE)).astimezone(ZONE)
    calendar = load_calendar(root/'market-trading-calendar.json', now.year, allow_fetch=False)
    if not noon_window(now, calendar):
        if scheduled: return dict(status='skipped', session='midday', reason='Outside verified trading-day lunch window')
        raise ValueError('Outside verified trading-day lunch window')
    target, status = root/'market-breadth-midday.json', root/'market-breadth-midday-status.json'
    previous = read_json(target)
    if previous and not force:
        try:
            validate_midday(previous, now.date().isoformat(), calendar)
            report = dict(status='success', session='midday', asOf=previous['asOf'], generatedAt=previous['generatedAt'], coveragePct=previous['coveragePct'])
            saved = read_json(status) or {}
            if any(saved.get(k) != v for k, v in report.items()):
                atomic_json(status, report)
            return dict(report, alreadyCurrent=True)
        except (ValueError, KeyError, TypeError): pass
    try:
        result = collect(root=root, now=now)
        validate_midday(result, now.date().isoformat(), calendar)
        archive = root/'output'/'midday-history'; archive.mkdir(parents=True, exist_ok=True)
        atomic_json(archive/(result['asOf']+'.json'), result)
        atomic_json(target, result)
        report = dict(status='success', session='midday', asOf=result['asOf'], generatedAt=result['generatedAt'], coveragePct=result['coveragePct'])
        atomic_json(status, report)
        return report
    except Exception as exc:
        atomic_json(status, dict(status='failed', session='midday', attemptedAt=now.isoformat(), requestedDate=now.date().isoformat(), error=str(exc)[:250]))
        raise  # Last good midday and all completed-close bytes remain untouched.


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scheduled', action='store_true')
    p.add_argument('--force', action='store_true')
    p.add_argument('--output', type=Path, help='Shadow validation: write only this output file')
    args = p.parse_args()
    with run_lock(ROOT/'output'/'midday-breadth.lock'):
        if args.output:
            output = safe_shadow_output(args.output)
            result = collect()
            atomic_json(output, result)
            print(json.dumps({k:result[k] for k in ('asOf','observedAt','generatedAt','coveragePct','market')}, ensure_ascii=False))
        else:
            print(json.dumps(refresh(scheduled=args.scheduled, force=args.force), ensure_ascii=False))
