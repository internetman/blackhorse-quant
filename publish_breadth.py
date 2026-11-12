"""Publish an allowlist of breadth files, without touching other website files."""
from __future__ import annotations
import datetime as dt
import json
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from market_breadth import ROOT, ZONE, fetch

REPOSITORY = 'https://github.com/internetman/blackhorse-quant.git'
SITE = 'https://www.heimaq.com'
DATA_FILES = ('market-breadth.json', 'market-breadth-status.json', 'market-trading-calendar.json')
MIDDAY_DATA_FILES = ('market-breadth-midday.json', 'market-breadth-midday-status.json')
CLOUD_WORKFLOW = '.github/workflows/market-breadth.yml'
CODE_FILES = ('midday_breadth.py', 'MIDDAY-BREADTH.md', 'test_midday_breadth.py', 'test-midday-view.cjs',
              'cloud_breadth.py', 'test_cloud_breadth.py', 'complete_breadth.py', 'requirements-breadth.txt', 'MA50-BREADTH.md',
              'daily_breadth.py', 'publish_breadth.py', 'market-weather.js', 'market-breadth.js',
              'test_complete_breadth.py', 'test_daily_breadth.py', 'test_market_breadth.py',
              'test_public_breadth.py', 'test-market-weather.cjs')


def git(cwd, *args):
    result = subprocess.run(['git', '-C', str(cwd), *args], capture_output=True, text=True, timeout=90)
    if result.returncode:
        detail = re.sub(r'(https?://)[^/@\s]+:[^/@\s]+@', r'\1[redacted]@', result.stderr)
        detail = re.sub(r'(?i)(gh[pousr]_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+)', '[redacted]', detail)
        raise RuntimeError(f'Git {args[0] if args else "operation"} failed: {detail[-1800:].strip()}')
    return result.stdout.strip()


def publish(source=ROOT, repository=REPOSITORY, include_code=False, status_only=False, approve_scope_upgrade=False, install_cloud=False, expected_remote_commit=None):
    source = Path(source)
    if install_cloud and (not include_code or status_only):
        raise ValueError('Cloud installation requires an explicitly reviewed code release')
    files = ('market-breadth-status.json',) if status_only else DATA_FILES + (CODE_FILES + MIDDAY_DATA_FILES if include_code else ())
    if install_cloud:
        files += (CLOUD_WORKFLOW,)
    with tempfile.TemporaryDirectory(prefix='breadth-publish-') as directory:
        repo = Path(directory)/'repo'
        subprocess.run(['git', 'clone', '--quiet', '--depth', '1', repository, str(repo)], check=True, timeout=90)
        if expected_remote_commit and git(repo, 'rev-parse', 'HEAD') != expected_remote_commit:
            raise ValueError('Production head changed since release review')
        before = json.loads((repo/'market-breadth.json').read_text()) if (repo/'market-breadth.json').exists() else {}
        current = json.loads((source/'market-breadth.json').read_text())
        if current.get('scopeVersion') == 'qfq-shsz-v1' and before.get('scopeVersion') != current.get('scopeVersion') and not approve_scope_upgrade:
            raise ValueError('Initial MA50 scope upgrade publication requires explicit release approval; scheduled publication is blocked')
        if before.get('asOf', '') > current.get('asOf', ''):
            raise ValueError('Production already has a newer close; refusing to publish older local data/status')
        newer_remote = (before.get('asOf', ''), before.get('generatedAt', '')) > (current.get('asOf', ''), current.get('generatedAt', ''))
        if include_code:
            from daily_breadth import validate_snapshot
            from midday_breadth import validate_midday
            validate_snapshot(current, current['asOf'])
            midday = json.loads((source/'market-breadth-midday.json').read_text())
            validate_midday(midday, midday['asOf'])
            if midday['previousCloseDate'] != current['asOf']:
                raise ValueError('Release noon snapshot and prior completed close disagree')
        for name in files:
            if name == 'market-breadth.json' and newer_remote:
                continue
            (repo/name).parent.mkdir(parents=True, exist_ok=True)
            origin = source/'handoff/cloud-breadth.yml' if name == CLOUD_WORKFLOW else source/name
            shutil.copy2(origin, repo/name)
        # Read actual changed paths before staging; reject any unexpected file.
        changed = set(git(repo, 'diff', '--name-only').splitlines())
        changed.update(git(repo, 'ls-files', '--others', '--exclude-standard').splitlines())
        if not changed <= set(files):
            raise ValueError('Publication contains changes outside the breadth allowlist')
        if not changed:
            return dict(status='unchanged', commit=git(repo, 'rev-parse', 'HEAD'), files=[])
        git(repo, 'add', '--', *sorted(changed))
        git(repo, '-c', 'user.name=Heimaq breadth updater', '-c', 'user.email=breadth-updater@users.noreply.github.com',
            'commit', '-m', f'Update verified breadth {current["asOf"]}' if not status_only else 'Record breadth refresh failure')
        commit = git(repo, 'rev-parse', 'HEAD')
        # Ordinary fast-forward push only. A competing deployment is a visible
        # failure, never force-pushed or resolved by deleting website files.
        git(repo, 'push', 'origin', 'HEAD:main')
        return dict(status='pushed', commit=commit, files=sorted(changed))


def publish_checkout(source=ROOT, repository=REPOSITORY, status_only=False):
    """Use checkout's repo-local short-lived auth; never clone or export a token."""
    from daily_breadth import validate_snapshot
    repo = Path(source).resolve()
    if Path(git(repo, 'rev-parse', '--show-toplevel')).resolve() != repo:
        raise ValueError('Publication must run at the checked-out repository root')
    # checkout uses both official HTTPS forms, with and without trailing .git.
    identity = lambda value: value.rstrip('/').removesuffix('.git')
    if identity(git(repo, 'remote', 'get-url', 'origin')) != identity(repository):
        raise ValueError('Refusing publication to an unexpected repository')
    git(repo, 'fetch', '--quiet', 'origin', 'main')
    if git(repo, 'rev-parse', 'HEAD') != git(repo, 'rev-parse', 'FETCH_HEAD'):
        raise ValueError('Production advanced during collection; retry from a fresh checkout')
    before = json.loads(git(repo, 'show', 'HEAD:market-breadth.json'))
    current = json.loads((repo/'market-breadth.json').read_text())
    status = json.loads((repo/'market-breadth-status.json').read_text())
    if (before.get('asOf', ''), before.get('generatedAt', '')) > (current.get('asOf', ''), current.get('generatedAt', '')):
        raise ValueError('Refusing older snapshot or generation')
    if not status_only:
        if status.get('status') != 'success' or status.get('asOf') != current.get('asOf'):
            raise ValueError('Publication requires matching successful collection status')
        validate_snapshot(current, status['asOf'], before)
    elif status.get('status') != 'failed':
        raise ValueError('Failure-only publication requires a failed status')
    changed = set(git(repo, 'diff', 'HEAD', '--name-only').splitlines())
    untracked = set(git(repo, 'ls-files', '--others', '--exclude-standard').splitlines())
    changed.update(p for p in untracked if not p.startswith('output/'))
    if not changed <= set(DATA_FILES):
        raise ValueError('Checkout contains changes outside the breadth allowlist')
    files = changed & ({'market-breadth-status.json'} if status_only else set(DATA_FILES))
    if not files:
        return dict(status='unchanged', commit=git(repo, 'rev-parse', 'HEAD'), files=[])
    git(repo, 'add', '--', *sorted(files))
    if set(git(repo, 'diff', '--cached', '--name-only').splitlines()) != files:
        raise ValueError('Unexpected staged paths; refusing commit')
    git(repo, '-c', 'user.name=github-actions[bot]',
        '-c', 'user.email=41898282+github-actions[bot]@users.noreply.github.com',
        'commit', '-m', f'Update verified breadth {current["asOf"]}' if not status_only else 'Record breadth refresh failure')
    commit = git(repo, 'rev-parse', 'HEAD')
    git(repo, 'push', 'origin', 'HEAD:main')
    return dict(status='pushed', commit=commit, files=sorted(files))


def verify_live(expected, site=SITE, code=False, attempts=12, delay=10, snapshot=None):
    from daily_breadth import validate_snapshot
    error = None
    for attempt in range(attempts):
        try:
            stamp = str(time.time_ns())
            data = fetch(f'{site}/market-breadth.json?verify={stamp}', attempts=1, timeout=10)
            validate_snapshot(data, expected)
            if snapshot and (data.get('generatedAt') != snapshot.get('generatedAt') or data['market'][-1] != snapshot['market'][-1] or data.get('benchmarks') != snapshot.get('benchmarks') or data.get('scopeVersion') != snapshot.get('scopeVersion')):
                raise ValueError('Live snapshot does not match the actual collected generation/counts')
            status = fetch(f'{site}/market-breadth-status.json?verify={stamp}', attempts=1, timeout=10)
            if status.get('asOf') != expected or status.get('status') != 'success':
                raise ValueError('Live status does not confirm this completed close')
            if code:
                calendar = fetch(f'{site}/market-trading-calendar.json?verify={stamp}', attempts=1, timeout=10)
                if str(dt.datetime.now(ZONE).year) not in calendar.get('years', {}):
                    raise ValueError('Published calendar is missing current exchange year')
            return dict(status='verified', asOf=data['asOf'], generatedAt=data['generatedAt'],
                        coveragePct=data['coveragePct'], above=data['market'][-1]['ma20']['above'],
                        valid=data['market'][-1]['ma20']['valid'], availableMetrics=data['availableMetrics'])
        except Exception as exc:
            error = exc
            if attempt+1 < attempts:
                time.sleep(delay)
    raise RuntimeError(f'Live deployment verification failed: {error}')
