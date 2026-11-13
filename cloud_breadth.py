"""Repository-scoped, short-lived-token cloud runner. Never installs credentials."""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import time
from ffd_promotion import allow_verified_original_source_rollback
from pathlib import Path

import daily_breadth as daily
import midday_breadth as midday
from market_breadth import ROOT, ZONE, fetch
from trading_calendar import load_calendar, is_trading_day, expected_close
from publish_breadth import git, REPOSITORY, SITE

class PublicationVerificationError(RuntimeError):
    def __init__(self, receipt, error):
        super().__init__(str(error))
        self.receipt = dict(receipt, status='failed', failedStage='website_verification', error=str(error)[:600])


CRONS = {'0,20 4 * * 1-5': 'midday', '40 8,9,10 * * 1-5': 'close'}
FILES = {
    'close': ('market-breadth.json', 'market-breadth-status.json', 'market-trading-calendar.json'),
    'midday': ('market-breadth-midday.json', 'market-breadth-midday-status.json', 'market-trading-calendar.json'),
}


def choose_session(event, cron, requested, now):
    if requested not in ('auto', 'close', 'midday'):
        raise ValueError('Unknown session')
    if event == 'schedule':
        if cron not in CRONS:
            raise ValueError('Unknown scheduled event; refusing guessed session')
        return CRONS[cron]  # Never reclassify a delayed noon event as close.
    if event == 'push':
        return 'close'
    if event != 'workflow_dispatch':
        raise ValueError('Unsupported cloud event')
    if requested != 'auto':
        return requested
    return 'midday' if dt.time(11, 35) <= now.time().replace(tzinfo=None) < dt.time(12, 55) else 'close'


def changed_paths(root):
    changed = set(git(root, 'diff', 'HEAD', '--name-only').splitlines())
    changed.update(p for p in git(root, 'ls-files', '--others', '--exclude-standard').splitlines()
                   if not p.startswith('output/'))
    return changed


def check_repository(root):
    if Path(git(root, 'rev-parse', '--show-toplevel')).resolve() != root.resolve():
        raise ValueError('Runner must use repository root')
    normal = lambda s: s.rstrip('/').removesuffix('.git')
    if normal(git(root, 'remote', 'get-url', 'origin')) != normal(REPOSITORY):
        raise ValueError('Unexpected production repository')


def validate_pair(root, session, now, calendar):
    data, status = (daily.read_json(root / name) for name in FILES[session][:2])
    if session == 'close':
        daily.validate_snapshot(data, expected_close(now, calendar))
        daily.require_publishable(data)
        if data.get('scopeVersion') not in daily.ADJUSTED_SCOPES:
            raise ValueError('Cloud close requires complete adjusted MA20/MA50 scope')
        generation = status.get('lastCollectedAt')
    else:
        midday.validate_midday(data, now.date().isoformat(), calendar)
        generation = status.get('generatedAt')
    if status.get('status') != 'success' or status.get('asOf') != data.get('asOf') or generation != data.get('generatedAt'):
        raise ValueError('Snapshot and successful status generations must match')
    return data


def publish_session(root, session, now, calendar):
    """Only data/status for this session plus verified calendar; never force push."""
    check_repository(root)
    data = validate_pair(root, session, now, calendar)
    git(root, 'fetch', '--quiet', 'origin', 'main')
    head = git(root, 'rev-parse', 'HEAD')
    if head != git(root, 'rev-parse', 'FETCH_HEAD'):
        raise ValueError('Remote HEAD advanced during collection; retry fresh checkout')
    old_text = git(root, 'ls-tree', '--name-only', 'HEAD', '--', FILES[session][0])
    if old_text:
        old = json.loads(git(root, 'show', 'HEAD:' + FILES[session][0]))
        if old.get('scopeVersion') != data.get('scopeVersion') and session == 'close' and not allow_verified_original_source_rollback(old, data):
            raise ValueError('Scope migration requires an explicitly approved release')
        if (old.get('asOf', ''), old.get('generatedAt', '')) > (data['asOf'], data['generatedAt']):
            raise ValueError('Refusing date or generation regression')
    changed = changed_paths(root)
    if not changed <= set(FILES[session]):
        raise ValueError('Changes outside selected session allowlist')
    staged = set(git(root, 'diff', '--cached', '--name-only').splitlines())
    if staged:
        raise ValueError('Unexpected pre-staged changes')
    if not changed:
        return dict(status='unchanged', commit=head, files=[])
    git(root, 'add', '--', *sorted(changed))
    if set(git(root, 'diff', '--cached', '--name-only').splitlines()) != changed:
        raise ValueError('Unexpected staged paths')
    git(root, '-c', 'user.name=github-actions[bot]',
        '-c', 'user.email=41898282+github-actions[bot]@users.noreply.github.com',
        'commit', '-m', f'Update verified {session} breadth {data["asOf"]}')
    commit = git(root, 'rev-parse', 'HEAD')
    git(root, 'push', 'origin', 'HEAD:main')
    # Check the exact commit, not just the push command exit status.
    remote = git(root, 'ls-remote', 'origin', 'refs/heads/main').split()
    if not remote or remote[0] != commit:
        raise RuntimeError('Published commit is not the current remote HEAD')
    return dict(status='pushed', commit=commit, files=sorted(changed))


def verify_site(root, session, attempts=18, delay=10):
    expected = {name: daily.read_json(root/name) for name in FILES[session]}
    error = None
    for attempt in range(attempts):
        try:
            stamp = str(time.time_ns())
            for name, value in expected.items():
                actual = fetch(f'{SITE}/{name}?cloud_verify={stamp}', attempts=1, timeout=10)
                if actual != value:
                    raise ValueError(f'Website has a different generation of {name}')
            data = expected[FILES[session][0]]
            return dict(status='verified', session=session, asOf=data['asOf'], generatedAt=data['generatedAt'])
        except Exception as exc:
            error = exc
            if attempt + 1 < attempts:
                time.sleep(delay)
    raise RuntimeError(f'Website deployment not verified; Git integration may not deploy job-token pushes. No additional credential or deployment permission was used. {error}')


def run(root=ROOT, now=None, event='workflow_dispatch', cron='', requested='auto', force=False):
    root = Path(root)
    now = (now or dt.datetime.now(ZONE)).astimezone(ZONE)
    session = choose_session(event, cron, requested, now)
    # Unknown exchange calendars fail closed before collection or publication.
    calendar = load_calendar(root/'market-trading-calendar.json', now.year, allow_fetch=False)
    if not is_trading_day(now.date(), calendar):
        return dict(status='skipped', session=session, reason='Not a verified exchange trading day')
    if session == 'midday' and not midday.noon_window(now, calendar):
        return dict(status='skipped', session=session, reason='Delayed/outside lunch window; never run close instead')
    if session == 'close' and event == 'schedule' and now.hour < 16:
        return dict(status='skipped', session=session, reason='Before close collection window')
    # Full historical bootstrap is an explicit manual exception only.
    manual_bootstrap = event == 'workflow_dispatch' and force is True
    if not manual_bootstrap:
        try:
            data = validate_pair(root, session, now, calendar)
            return dict(status='already_current', alreadyCurrent=True, session=session,
                        asOf=data['asOf'], generatedAt=data['generatedAt'], historyCalls=0)
        except (ValueError, KeyError, TypeError, OSError, AttributeError):
            return dict(status='blocked_incremental_unverified', session=session,
                        reason='Verified incremental history engine is not available; automatic full-history collection is disabled',
                        historyCalls=0, dataChanged=False)
    check_repository(root)
    if changed_paths(root) or git(root, 'diff', '--cached', '--name-only'):
        raise ValueError('Cloud collection requires a clean checkout')
    force = bool(force)  # Deployments must not discard a verified same-date generation.
    caches = [root/'output'/'public-breadth-cache', root/'output'/'qfq-breadth-cache']
    count = sum(sum(1 for _ in p.rglob('*.json')) for p in caches if p.exists())
    if force and count:
        raise ValueError('Forced cold acceptance requires empty source caches')
    # Guard the other session byte-for-byte, including its status file.
    other = 'close' if session == 'midday' else 'midday'
    protected = {name: (root/name).read_bytes() if (root/name).exists() else None for name in FILES[other][:2]}
    started = time.monotonic()
    with daily.run_lock(root/'output'/'cloud-breadth.lock'):
        if session == 'midday':
            report = midday.refresh(root=root, now=now, scheduled=True, force=force)
        else:
            report = daily.refresh(root=root, now=now, scheduled=event == 'schedule', attempts=1, retry_delay=15, force=force)
        for name, before in protected.items():
            after = (root/name).read_bytes() if (root/name).exists() else None
            if after != before:
                raise ValueError('Collection modified the other session; refusing publication')
        if report['status'] == 'skipped':
            return report
        publication = publish_session(root, session, now, calendar)
        receipt = dict(report, session=session, publication=publication, initialCacheFiles=count,
                       forcedCollection=force, elapsedSeconds=round(time.monotonic()-started, 2))
        # A successful Git push is not proof of a Vercel deployment.
        try:
            receipt['verification'] = verify_site(root, session)
        except Exception as exc:
            raise PublicationVerificationError(receipt, exc) from exc
        return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--session', choices=['auto', 'close', 'midday'], default='auto')
    p.add_argument('--force', action='store_true')
    args = p.parse_args()
    receipt = {}
    try:
        if os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('GITHUB_REPOSITORY') != 'internetman/blackhorse-quant' or os.environ.get('GITHUB_REF') != 'refs/heads/main':
            raise ValueError('Cloud publication only from production main Actions job')
        event = os.environ.get('GITHUB_EVENT_NAME', '')
        payload = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
        receipt = run(event=event, cron=payload.get('schedule', ''), requested=args.session, force=args.force)
    except Exception as exc:
        receipt = getattr(exc, 'receipt', dict(status='failed', error=str(exc)[:600]))
        raise
    finally:
        receipt['runUrl'] = f"https://github.com/internetman/blackhorse-quant/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}"
        print(json.dumps(receipt, ensure_ascii=False), flush=True)
        if os.environ.get('GITHUB_STEP_SUMMARY'):
            with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as out:
                out.write('### Cloud breadth receipt\n```json\n'+json.dumps(receipt, ensure_ascii=False, indent=2)+'\n```\n')


if __name__ == '__main__':
    main()
