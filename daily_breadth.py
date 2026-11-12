"""One locked, exchange-calendar-aware close refresh. Never executes trades."""
from __future__ import annotations
import argparse
import datetime as dt
import fcntl
import json
import math
import statistics
import sys
import time
from contextlib import contextmanager
from pathlib import Path

from market_breadth import ROOT, ZONE, atomic_json
from trading_calendar import load_calendar, is_trading_day, expected_close


def read_json(path):
    return json.loads(Path(path).read_text()) if Path(path).exists() else None


def validate_snapshot(data, expected, previous=None):
    if data.get('asOf') != expected or data.get('barStatus') != 'completed':
        raise ValueError('Snapshot must be the expected completed exchange close')
    if previous and data['asOf'] < previous.get('asOf', ''):
        raise ValueError('Refusing snapshot date regression')
    dates = data.get('dates', [])
    if not dates or dates != sorted(set(dates)) or dates[-1] != expected:
        raise ValueError('Invalid snapshot dates')
    n = data.get('universeCount', 0)
    if n < 4000 or data.get('coveragePct', 0) < 95 or data.get('latestHistoryCount', 0)/n < .95:
        raise ValueError('Snapshot coverage below 95%')
    if previous and previous.get('universeLabel') == data.get('universeLabel'):
        old = previous.get('universeCount', n)
        if old and abs(n/old-1) > .05:
            raise ValueError('Universe size changed by more than 5%; review source scope')
    latest = data['market'][-1]
    if latest['date'] != expected or len(data.get('rows', [])) < 50:
        raise ValueError('Missing current market/industry observations')
    for key in data.get('availableMetrics', []):
        m = latest[key]
        if not m.get('valid') or m['valid']/n < .95 or not 0 <= m['above'] <= m['valid']:
            raise ValueError('Invalid same-date metric denominator')
        if m.get('pct') is None or not math.isfinite(m['pct']) or abs(m['pct']-100*m['above']/m['valid']) > .011:
            raise ValueError('Metric percentage disagrees with numerator/denominator')
    if 'ma20' not in data.get('availableMetrics', []):
        raise ValueError('MA20 is required')
    if 'ma50' not in data['availableMetrics'] and latest['ma50']['pct'] is not None:
        raise ValueError('Missing MA50 must remain null')
    if data.get('scopeVersion') == 'qfq-shsz-v1':
        from complete_breadth import BENCHMARKS
        if data.get('availableMetrics') != ['ma20', 'ma50']:
            raise ValueError('Adjusted full snapshot requires MA20 and MA50')
        indices = data.get('benchmarks', [])
        if len(indices) != 5 or {r.get('secid') for r in indices} != {s for s, _ in BENCHMARKS}:
            raise ValueError('Five distinct benchmark identities required')
        for r in indices:
            if r.get('asOf') != expected or r.get('historyCount', 0) < 70:
                raise ValueError('Benchmark date/history is incomplete')
            if any(not isinstance(r.get(k), (int, float)) or not math.isfinite(r[k]) for k in ('close', 'ma50', 'ma50Slope20')) or r['close'] <= 0 or r['ma50'] <= 0:
                raise ValueError('Invalid benchmark values')
        history = data.get('dailyHistory', {})
        if history.get('adjustment') != 'qfq' or history.get('cutoff') != expected:
            raise ValueError('Adjusted-history provenance missing or stale')
    return data


def merge_verified_history(data, previous):
    """Keep earlier actual counts; never mix the former 128-sector scope."""
    if not previous or previous.get('universeLabel') != data.get('universeLabel') or previous.get('availableMetrics') != data.get('availableMetrics'):
        return data
    if previous.get('scopeVersion') != data.get('scopeVersion'):
        return data
    old = {x['date']: x for x in previous.get('market', [])}
    data['market'] = [old.get(r['date'], r) if r['ma20'].get('valid', 0) == 0 and old.get(r['date'], {}).get('ma20', {}).get('valid', 0) > 0 else r for r in data['market']]
    by_name = {s['industry']: s for s in previous.get('rows', [])}
    for sector in data['rows']:
        past = {x['date']: x for x in by_name.get(sector['industry'], {}).get('series', [])}
        sector['series'] = [past[r['date']] if r['ma20'].get('reported') and past.get(r['date'], {}).get('ma20', {}).get('valid', 0) else r for r in sector['series']]
        values = [r['ma20']['pct'] for r in sector['series']]
        recent, prior = values[-5:], values[-10:-5]
        valid = lambda v: isinstance(v, (int, float)) and math.isfinite(v)
        sector['avg5'] = round(statistics.mean(recent), 2) if len(recent) == 5 and all(map(valid, recent)) else None
        sector['slope5'] = round(statistics.mean(recent)-statistics.mean(prior), 2) if len(prior) == 5 and all(map(valid, recent+prior)) else None
    return data


@contextmanager
def run_lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Another breadth refresh owns the lock')
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def refresh(root=ROOT, now=None, scheduled=False, attempts=2, retry_delay=30, force=False):
    from complete_breadth import collect, VERSION
    now = (now or dt.datetime.now(ZONE)).astimezone(ZONE)
    calendar = load_calendar(root/'market-trading-calendar.json', now.year, allow_fetch=True)
    if scheduled and (not is_trading_day(now.date(), calendar) or now.hour < 16):
        return dict(status='skipped', reason='Not an exchange close refresh window', attemptedAt=now.isoformat())
    expected = expected_close(now, calendar)
    target, status = root/'market-breadth.json', root/'market-breadth-status.json'
    previous = read_json(target)
    current = False
    if previous and not force:
        try:
            validate_snapshot(previous, expected)
            current = previous.get('scopeVersion') == VERSION and previous.get('availableMetrics') == ['ma20', 'ma50']
        except (ValueError, KeyError, TypeError):
            pass
    old_status = read_json(status) or {}
    if current and old_status.get('status') == 'success' and old_status.get('asOf') == expected and old_status.get('lastCollectedAt') == previous.get('generatedAt'):
        # Retry slots still verify production, but do not create three status
        # commits/deployments per day after the first successful publication.
        return dict(old_status, checkedAt=now.isoformat(), alreadyCurrent=True)
    if not current:
        # The collector writes only caches. The old successful snapshot remains
        # untouched until every check below has passed.
        for attempt in range(attempts):
            atomic_json(status, dict(status='running', attemptedAt=now.isoformat(), requestedCutoff=expected, attempt=attempt+1))
            try:
                result = collect(days=6, workers=4, expected=expected)
                validate_snapshot(result, expected, previous)
                result = merge_verified_history(result, previous)
                validate_snapshot(result, expected, previous)
                archive = root/'output'/'breadth-history'
                archive.mkdir(parents=True, exist_ok=True)
                atomic_json(archive/f'{expected}.json', result)
                atomic_json(target, result)
                previous = result
                break
            except Exception as exc:
                atomic_json(status, dict(status='failed', attemptedAt=dt.datetime.now(ZONE).isoformat(timespec='seconds'),
                                         requestedCutoff=expected, asOf=previous.get('asOf') if previous else None,
                                         error=str(exc)[:250], attempt=attempt+1))
                if attempt+1 == attempts:
                    raise
                time.sleep(retry_delay)
    result = dict(status='success', attemptedAt=dt.datetime.now(ZONE).isoformat(timespec='seconds'),
                  asOf=expected, expectedCloseDate=expected, coveragePct=previous['coveragePct'],
                  availableMetrics=previous['availableMetrics'], lastCollectedAt=previous['generatedAt'],
                  note='Existing verified close' if current else 'Verified same-date adjusted MA20/MA50 breadth and five benchmark histories')
    atomic_json(status, result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scheduled', action='store_true')
    p.add_argument('--publish', action='store_true')
    p.add_argument('--publish-checkout', action='store_true', help='Publish from the production Actions checkout using repo-local authentication')
    p.add_argument('--approve-scope-upgrade', action='store_true', help='Only after explicit approval for this initial MA50 production release')
    p.add_argument('--install-cloud', action='store_true', help='Explicitly authorized one-time installation of the scoped cloud scheduler')
    p.add_argument('--expected-remote-commit', help='Abort release if production advanced after review')
    p.add_argument('--include-code', action='store_true', help='One-time installation; publish only the reviewed breadth files')
    p.add_argument('--force', action='store_true')
    p.add_argument('--attempts', type=int, choices=range(1, 4), default=2)
    p.add_argument('--retry-delay', type=int, choices=range(0, 61), default=30)
    args = p.parse_args()
    if args.install_cloud and (not args.include_code or not args.publish):
        p.error('--install-cloud requires --publish --include-code')
    if args.publish_checkout and (args.publish or args.include_code or args.install_cloud):
        p.error('--publish-checkout cannot be combined with --publish or --include-code')
    report = None
    with run_lock(ROOT/'output'/'daily-breadth.lock'):
        try:
            report = refresh(scheduled=args.scheduled, attempts=args.attempts, retry_delay=args.retry_delay, force=args.force)
            if (args.publish or args.publish_checkout) and report['status'] != 'skipped':
                from publish_breadth import publish, publish_checkout, verify_live
                publication = publish_checkout(ROOT) if args.publish_checkout else publish(ROOT, include_code=args.include_code, approve_scope_upgrade=args.approve_scope_upgrade, install_cloud=args.install_cloud, expected_remote_commit=args.expected_remote_commit)
                report['publication'] = publication
                report['verification'] = verify_live(report['asOf'], code=args.include_code, snapshot=read_json(ROOT/'market-breadth.json'))
            print(json.dumps(report, ensure_ascii=False), flush=True)
        except Exception as exc:
            stage = 'verification' if report and report.get('publication') else 'publication' if report else 'collection'
            report = dict(report or {}, status='failed', failedStage=stage, error=str(exc)[:250])
            failure = read_json(ROOT/'market-breadth-status.json') or {}
            if failure.get('status') != 'failed' and stage == 'collection':
                previous = read_json(ROOT/'market-breadth.json') or {}
                atomic_json(ROOT/'market-breadth-status.json', dict(status='failed',
                    attemptedAt=dt.datetime.now(ZONE).isoformat(timespec='seconds'),
                    asOf=previous.get('asOf'), error=str(exc)[:250]))
            # Expose a failed acquisition online without replacing price data.
            if (args.publish or args.publish_checkout) and (read_json(ROOT/'market-breadth-status.json') or {}).get('status') == 'failed':
                try:
                    from publish_breadth import publish, publish_checkout
                    publish_checkout(ROOT, status_only=True) if args.publish_checkout else publish(ROOT, status_only=True)
                except Exception as publication_error:
                    print(f'Failure-status publication also failed: {type(publication_error).__name__}', file=sys.stderr)
            print(f'Breadth refresh failed: {exc}', file=sys.stderr)
            raise
        finally:
            logs = ROOT/'output'/'daily-breadth-runs'
            logs.mkdir(parents=True, exist_ok=True)
            stamp = dt.datetime.now(ZONE).strftime('%Y%m%d-%H%M%S')
            atomic_json(logs/f'{stamp}.json', report or dict(status='failed', detail='See process log and market-breadth-status.json'))


if __name__ == '__main__':
    main()
