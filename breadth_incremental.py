"""Offline staging for gap-only MA20/MA50 breadth; no credentials or publishing."""
from __future__ import annotations

import collections
import datetime as dt
import hashlib
import json
import math
import os
import statistics
from pathlib import Path

from trading_calendar import is_trading_day

SCHEMA = 'heima-private-breadth-input-v1'
PROVIDERS = frozenset(('FFD', 'Tencent', 'Eastmoney'))
CLOSE_SOURCES = PROVIDERS | {'sckd', 'beta'}


class CloseMismatch(ValueError):
    pass
OVERLAP = 3
MAX_GAP = 5
WINDOW = 49
GATE = 95
# Issuer-confirmed full-day halts, not assertions supplied by a quote payload.
VERIFIED_HISTORICAL_SUSPENSIONS = {
    ('688053', '2026-11-10'): (
        'SSE issuer announcement 2026-027',
        'https://epaper.cs.com.cn/zgzqb/html/2026-11/10/nw.D110000zgzqb_20261110_5-B021.htm',
        '2026-11-11',
    ),
}


def canonical_digest(value):
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False,
                     separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def trading_dates(first, last, calendar, *, max_span=45):
    a, b = dt.date.fromisoformat(first), dt.date.fromisoformat(last)
    if (b-a).days > max_span or b < a:
        raise ValueError('Gap date range must be bounded')
    return [(a+dt.timedelta(days=i)).isoformat() for i in range((b-a).days+1)
            if is_trading_day(a+dt.timedelta(days=i), calendar)]


def verified_overlap(code, actual, calendar):
    expected = trading_dates(actual[0], actual[-1], calendar)
    if not set(actual) <= set(expected):
        raise ValueError('Overlap contains a non-trading date')
    omissions = []
    for day in sorted(set(expected) - set(actual)):
        evidence = VERIFIED_HISTORICAL_SUSPENSIONS.get((code, day))
        if evidence is None:
            raise ValueError('Seed has unverified historical overlap gap')
        notice, source, resumed = evidence
        if resumed not in actual:
            raise ValueError('Seed lacks the verified resumed trading session')
        omissions.append(dict(date=day, source=source, notice=notice, resumedOn=resumed))
    return omissions


def make_plan(membership, seed, target_date, calendar):
    origin = seed['cutoff']
    dates = trading_dates(origin, target_date, calendar)
    if not dates or dates[0] != origin or dates[-1] != target_date or not 1 <= len(dates)-1 <= MAX_GAP:
        raise ValueError('Expected explicit later trading session and 1–5 missing trading dates')
    if membership['asOf'] != origin:
        raise ValueError('Unverified or mismatched frozen membership date')
    members = membership['stocks']
    if not isinstance(members, dict) or not isinstance(seed['series'], dict):
        raise ValueError('Membership and seed series must be identity maps')
    if any(not isinstance(k, str) or len(k)!=6 or not k.isascii() or not k.isdigit()
           or k[0] not in '036' or not isinstance(v, str) or not v for k,v in members.items()):
        raise ValueError('Invalid Shanghai/Shenzhen member identities')
    for k in ('seed', 'membership'):
        obj = seed if k == 'seed' else membership
        if obj.get('schema') != SCHEMA or not isinstance(obj.get('source'), str) or not obj['source']:
            raise ValueError('Missing private seed or membership provenance')
    denom = membership['universeCount']
    if type(denom) is not int or denom <= 0 or len(members) > denom or len(members)*100 < GATE*denom:
        raise ValueError('Membership cannot meet fixed coverage gate')

    requests, excluded = {}, collections.Counter()
    for code in members:
        try:
            item = seed['series'][code]
            if (item['provider'] not in PROVIDERS or item['adjustment'] != 'qfq'
                    or item['cutoff'] != origin or item['code'] != code):
                raise ValueError('Invalid seed identity')
            bars = check_bars(item['bars'], origin, calendar, minimum=WINDOW)
            if item['barSha256'] != canonical_digest(bars):
                raise ValueError('Seed digest mismatch')
            overlap = [r['date'] for r in bars[-OVERLAP:]]
            suspensions = verified_overlap(code, overlap, calendar)
            # Never bridge independent price bases implicitly. A verified FFD seed
            # stays on FFD; prior Tencent/Eastmoney bases require the same source.
            requests[code] = dict(provider=item['provider'], firstDate=overlap[0],
                                  lastDate=target_date, expectedDates=overlap+dates[1:])
            if suspensions:
                requests[code]['verifiedHistoricalSuspensions'] = suspensions
        except (KeyError, TypeError, ValueError):
            excluded['invalidOrMissingSeed'] += 1
    return dict(base=origin, target=target_date, dates=dates[1:], requests=requests,
                excluded=dict(excluded), universeCount=denom)


def check_bars(bars, cutoff, calendar, minimum=1):
    if not isinstance(bars, list) or len(bars) < minimum:
        raise ValueError('Insufficient bars')
    dates = [r['date'] for r in bars]
    if dates != sorted(set(dates)) or dates[-1] != cutoff:
        raise ValueError('Bars are unordered, duplicate, or stale')
    if any(dt.date.fromisoformat(d).isoformat() != d
           or not is_trading_day(dt.date.fromisoformat(d), calendar) for d in dates):
        raise ValueError('Bars include unverified trading dates')
    for r in bars:
        for key in ('close', 'volume'):
            raw = r[key]
            if type(raw) not in (int, float) or not math.isfinite(raw) or raw < 0 or key == 'close' and not raw:
                raise ValueError('Malformed daily bar')
    return bars


def import_seed(snapshot, cache_dir, calendar, ffd_receipt_dir=None):
    """Import local original cache by public manifest; never fetch missing bars."""
    from complete_breadth import VERSION, parse_eastmoney, parse_tencent
    from daily_breadth import validate_snapshot
    from ffd_history import parse_history

    origin = snapshot['asOf']
    validate_snapshot(snapshot, origin)
    history = snapshot['dailyHistory']
    if history['cutoff'] != origin or history['adjustment'] != 'qfq':
        raise ValueError('Snapshot has no verified historical provenance')
    stocks = {x['code']: x for x in history['sourceStocks']}
    if len(stocks) != history['stockCount']:
        raise ValueError('Frozen universe contains duplicate members')
    manifest = {x['code']: x for x in history['manifest']}
    if len(manifest) != len(history['manifest']) or len(manifest) != history['validHistories']:
        raise ValueError('Historical manifest count mismatch')
    membership = dict(schema=SCHEMA, source='verified completed-close snapshot', asOf=origin,
                      universeCount=snapshot['universeCount'],
                      stocks={c:x['industry'] for c,x in stocks.items()})
    seed = dict(schema=SCHEMA, source='private-cache/public-source-manifest SHA256',
                cutoff=origin, series={})
    cache_dir = Path(cache_dir)
    status = collections.Counter()
    receipt_index = {}
    if ffd_receipt_dir is not None:
        for path in Path(ffd_receipt_dir).glob('*.response.json'):
            try:
                fingerprint = path.name.removesuffix('.response.json')
                receipt = json.loads(path.with_name(fingerprint+'.json').read_text())
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                req = receipt['request']
                semantic_match = (receipt['state']=='completed' and receipt['responseFile']==path.name
                    and receipt['requestFingerprint']==fingerprint
                    and canonical_digest(req)==fingerprint
                    and receipt['sanitizedResponseSha256']==digest
                    and req['function']=='history' and req['indicators']=='close,volume'
                    and req['options']=='CPS:2' and req['coverage_policy']=='strict')
                if semantic_match:
                    receipt_index[digest] = (path,req)
            except (KeyError, TypeError, ValueError, OSError):
                continue
    for code,m in manifest.items():
        provider, stock = m['provider'], stocks.get(code)
        if not stock or m['industry'] != stock['industry'] or m['lastDate'] != origin or provider not in PROVIDERS:
            raise ValueError('Historical manifest semantic mismatch')
        market = '1' if code.startswith('6') else '0'
        secid = market+'.'+code
        if stock['secid'] != secid:
            raise ValueError('Historical manifest security mismatch')
        symbol = ('sh' if market=='1' else 'sz')+code
        try:
            if provider == 'FFD':
                ffd_code = code+('.SH' if market=='1' else '.SZ')
                if m['sha256'] in receipt_index:
                    path, req = receipt_index[m['sha256']]
                    if req['codes'] != ffd_code or req['end_date'] != origin or req['start_date'] > m['firstDate']:
                        raise ValueError('FFD receipt identity/range mismatch')
                    raw = json.loads(path.read_text())
                else:
                    path = cache_dir/(secid+'.ffd.json')
                    wrapper = json.loads(path.read_text())
                    raw = wrapper.get('response', wrapper)
                if canonical_digest(raw) != m['sha256']:
                    raise ValueError('FFD raw receipt differs from verified manifest')
                dates = trading_dates(m['firstDate'], origin, calendar, max_span=120)
                bars = parse_history(raw, ffd_code, m['firstDate'], origin, expected_dates=dates)
            else:
                path = cache_dir/(secid+'.json')
                wrapper = json.loads(path.read_text())
                raw = wrapper['response']
                if (wrapper['provider']!=provider or wrapper['version']!=VERSION or wrapper['symbol']!=symbol
                        or wrapper['cutoff']!=origin or wrapper['adjustment']!='qfq'
                        or wrapper['sha256'] != m['sha256'] or canonical_digest(raw) != m['sha256']):
                    raise ValueError('Original source cache/manifest mismatch')
                bars = (parse_tencent(raw,symbol,origin) if provider=='Tencent' else
                        parse_eastmoney(raw,code,origin,market))
            if len(bars) != m['bars'] or bars[0]['date'] != m['firstDate']:
                raise ValueError('Original source cache/manifest window mismatch')
            retained = check_bars(bars[-70:],origin,calendar,minimum=WINDOW)
            seed['series'][code] = dict(code=code,provider=provider,adjustment='qfq',cutoff=origin,
                bars=retained,barSha256=canonical_digest(retained),originSourceSha256=m['sha256'])
            status[provider] += 1
        except (KeyError, TypeError, ValueError, OSError, IndexError):
            status['missingOrUnverified'] += 1
    return membership, seed, dict(status)


def normalize_stock(code, item, delta, quote_pack, request, cutoff, calendar):
    bars = item['bars']
    if (delta['code'] != code or delta['provider'] != request['provider'] or delta['adjustment'] != 'qfq'
            or delta['cutoff'] != cutoff or not delta['requestId']):
        raise ValueError('Delta identity, provider, request or cutoff mismatch')
    # Three matching observations detect common basis problems, but do not
    # certify an older history. Explicit complete corporate-action verification
    # is also mandatory. Exclude the affected name instead of silently rebasing.
    factors = delta['corporateActions']
    first = bars[-WINDOW]['date']
    if (factors['code'] != code or factors['state'] != 'complete_no_rebase'
            or not factors['source'] or not factors['evidenceId']
            or not factors['verifiedFrom'] <= first
            or not factors['verifiedThrough'] >= cutoff):
        raise ValueError('Corporate-action coverage missing or rebase required')
    for k in ('verifiedFrom','verifiedThrough'):
        if dt.date.fromisoformat(factors[k]).isoformat() != factors[k]:
            raise ValueError('Invalid factor evidence date')
    inc = check_bars(delta['bars'], cutoff, calendar)
    if [r['date'] for r in inc] != request['expectedDates']:
        raise ValueError('Delta coverage mismatch')
    if any(a['close'] != b['close'] or a['volume'] != b['volume']
           for a,b in zip(bars[-OVERLAP:],inc[:OVERLAP])):
        raise ValueError('Overlap price/volume basis mismatch')
    combined = [{k:r[k] for k in ('date','close','volume')} for r in bars+inc[OVERLAP:]]
    values = {}
    for i in range(len(bars),len(combined)):
        row = combined[i]
        ext = quote_pack[row['date']][code]
        stamp = dt.datetime.fromisoformat(ext['sourceTime'])
        from market_breadth import ZONE
        if stamp.tzinfo is None:
            raise ValueError('Independent close lacks source timezone')
        stamp = stamp.astimezone(ZONE)
        if (ext['provider'] not in CLOSE_SOURCES - {delta['provider']} or ext['session'] != 'completed_close'
                or ext['asOf'] != row['date'] or stamp.date().isoformat() != row['date'] or stamp.hour < 15
                or ext['code'] != code or type(ext['close']) not in (int,float)
                or not math.isfinite(ext['close']) or ext['close'] <= 0 or row['volume'] <= 0):
            raise ValueError('Unverified or zero-volume close')
        if abs(row['close']/ext['close']-1) > .005:
            raise CloseMismatch('Independent close differs by more than 0.5%')
        values[row['date']] = {n: row['close'] > statistics.fmean(r['close'] for r in combined[i-n+1:i+1])
                               for n in (20,50)}
    return combined, values


def verify_benchmarks(entries, plan, calendar):
    """Five independently sourced, same-provider native index series."""
    from complete_breadth import BENCHMARKS
    universe = {x for x,_ in BENCHMARKS}
    if not isinstance(entries, dict) or set(entries) != universe:
        raise ValueError('All five benchmark inputs are required')
    result = {d: {} for d in plan['dates']}
    for secid in sorted(universe):
        pair = entries[secid]
        seed, delta = pair['seed'], pair['delta']
        if seed['provider'] not in PROVIDERS or delta['provider'] != seed['provider']:
            raise ValueError('Benchmark provider mismatch')
        if any(x['adjustment']!='none' or x['secid']!=secid for x in (seed,delta)):
            raise ValueError('Benchmark identity/adjustment mismatch')
        bars = check_bars(seed['bars'],plan['base'],calendar,minimum=70)
        if seed['barSha256'] != canonical_digest(bars):
            raise ValueError('Benchmark seed digest mismatch')
        overlap = [r['date'] for r in bars[-OVERLAP:]]
        if trading_dates(overlap[0], plan['base'], calendar) != overlap:
            raise ValueError('Benchmark seed misses overlap dates')
        inc = check_bars(delta['bars'],plan['target'],calendar)
        if [r['date'] for r in inc] != overlap+plan['dates'] or not delta['requestId']:
            raise ValueError('Benchmark delta dates/identity mismatch')
        if any(a['close'] != b['close'] for a,b in zip(bars[-OVERLAP:],inc[:OVERLAP])):
            raise ValueError('Benchmark price overlap mismatch')
        chain = bars+inc[OVERLAP:]
        for i in range(len(bars),len(chain)):
            row = chain[i]
            avg = statistics.fmean(r['close'] for r in chain[i-49:i+1])
            prior = statistics.fmean(r['close'] for r in chain[i-69:i-19])
            result[row['date']][secid] = dict(ma50Slope20=round((avg/prior-1)*100,6),
                                             aboveMA50=row['close']>avg)
    return result


def stage(membership, seed, deltas, independent_quotes, target_date, calendar, benchmarks=None):
    """Create private seed and a raw-data-free report. Does not live publish."""
    plan = make_plan(membership, seed, target_date, calendar)
    valid, failures = {}, collections.Counter(plan['excluded'])
    counts = {d: collections.defaultdict(collections.Counter) for d in plan['dates']}
    sectors = collections.Counter(membership['stocks'].values())
    for code, req in plan['requests'].items():
        try:
            delta = deltas[code]
            combined, values = normalize_stock(code, seed['series'][code],delta,
                independent_quotes,req,target_date,calendar)
        except CloseMismatch:
            failures['closeMismatch'] += 1
            continue
        except (TypeError, KeyError, ValueError, IndexError):
            failures['notVerified'] += 1
            continue
        cached = combined[-70:]
        valid[code] = dict(code=code,provider=req['provider'],adjustment='qfq',cutoff=target_date,
                           bars=cached,barSha256=canonical_digest(cached))
        for d, metrics in values.items():
            for bucket in (counts[d][None], counts[d][membership['stocks'][code]]):
                bucket['valid'] += 1
                for n,b in metrics.items():
                    bucket[n] += int(b)

    def metrics(bucket, denom):
        enough = bucket['valid']*100 >= GATE*denom
        return {f'ma{n}':dict(valid=bucket['valid'],above=bucket[n],eligible=denom,
                  insufficientCoverage=not enough, pct=round(100*bucket[n]/bucket['valid'],2) if enough else None)
                for n in (20,50)}

    sessions = {d:dict(market=metrics(counts[d][None],plan['universeCount']),
                       sectors={s:metrics(counts[d][s],n) for s,n in sorted(sectors.items())})
                for d in plan['dates']}
    close_pass = failures['closeMismatch']*100 <= len(plan['requests'])
    coverage_pass = all(not s['market']['ma50']['insufficientCoverage'] for s in sessions.values())
    if benchmarks is None:
        benchmarks_pass = False
    else:
        try:
            verified_benchmarks = verify_benchmarks(benchmarks,plan,calendar)
            for d,v in verified_benchmarks.items():
                sessions[d]['benchmarks'] = v
            benchmarks_pass = True
        except (ValueError,TypeError,KeyError,IndexError):
            benchmarks_pass = False
            failures['benchmarkValidation'] += 1
    report = dict(schema='heima-breadth-incremental-shadow-v1', session='completed_close_shadow',
                  cutoff=target_date, membershipDate=membership['asOf'], coveragePass=coverage_pass,
                  independentCloseGatePassed=close_pass, benchmarkGatePassed=benchmarks_pass,
                  publishable=False, failureCounts=dict(failures),
                  sessions=sessions, priorSeedHash=canonical_digest(seed))
    private = dict(schema=SCHEMA,cutoff=target_date,source='verified same-provider delta workspace',
                   series=valid, priorSeedHash=report['priorSeedHash'])
    return report, private


def main(argv=None):
    import argparse
    from trading_calendar import load_calendar, expected_close
    p = argparse.ArgumentParser(description=__doc__)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument('--bundle', type=Path)
    src.add_argument('--snapshot', type=Path, help='Previous verified breadth JSON for import-only preflight')
    p.add_argument('--cache-dir', type=Path, help='Private original raw cache, only used with --snapshot')
    p.add_argument('--ffd-receipt-dir', type=Path, help='Optional authenticated original private FFD receipts')
    p.add_argument('--target-date', required=True)
    p.add_argument('--calendar', type=Path, required=True)
    p.add_argument('--private-stage', type=Path, required=True,
                   help='New private location outside the production checkout')
    args = p.parse_args(argv)
    root = Path(__file__).resolve().parent
    dest = args.private_stage.resolve()
    if dest.is_relative_to(root):
        p.error('Private stage must be outside production checkout')
    cal = load_calendar(args.calendar, allow_fetch=False)
    if args.target_date > expected_close(calendar=cal):
        p.error('Target date is after the latest finalized close')
    if args.snapshot is not None:
        if args.cache_dir is None:
            p.error('--snapshot requires --cache-dir')
        membership, seed, counts = import_seed(json.loads(args.snapshot.read_text()), args.cache_dir, cal, args.ffd_receipt_dir)
        plan = make_plan(membership, seed, args.target_date, cal)
        preflight = dict(status='preflight_only', membershipDate=plan['base'], targetDate=plan['target'],
                         missingDates=plan['dates'], imported=counts, usableSeedCount=len(plan['requests']),
                         universeCount=plan['universeCount'], publishable=False)
        outputs = [('membership.json',membership),('source-seed.json',seed),('plan.json',plan)]
        passed = len(plan['requests'])*100 >= GATE*plan['universeCount']
    else:
        if args.cache_dir is not None or args.ffd_receipt_dir is not None:
            p.error('Cache and receipt paths apply only to --snapshot')
        bundle = json.loads(args.bundle.read_text())
        report, private = stage(bundle['membership'],bundle['seed'],bundle['deltas'],
                                bundle['independentQuotes'],args.target_date,cal,bundle.get('benchmarks'))
        preflight = {k:v for k,v in report.items() if k != 'sessions'}
        outputs = [('report.json',report),('source-seed.json',private)]
        passed = report['coveragePass'] and report['independentCloseGatePassed'] and report['benchmarkGatePassed']
    dest.mkdir(mode=0o700, parents=False, exist_ok=False)
    for name,value in outputs:
        fd = os.open(dest/name, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
        with os.fdopen(fd,'w') as f:
            json.dump(value,f,ensure_ascii=False,separators=(',',':'),allow_nan=False)
            f.flush()
            os.fsync(f.fileno())
    print(json.dumps(preflight, ensure_ascii=False))
    return 0 if passed else 2


if __name__ == '__main__':
    raise SystemExit(main())
