"""Publish an allowlist of breadth files, without touching other website files."""
from __future__ import annotations
import datetime as dt
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from market_breadth import ROOT, ZONE, fetch

REPOSITORY = 'https://github.com/internetman/blackhorse-quant.git'
SITE = 'https://www.heimaq.com'
DATA_FILES = ('market-breadth.json', 'market-breadth-status.json', 'market-trading-calendar.json')
CODE_FILES = ('market_breadth.py', 'refresh_public_breadth.py', 'daily_breadth.py', 'publish_breadth.py',
              'trading_calendar.py', 'market-weather.js', 'market-breadth.js', 'radar.html', 'server.py', 'README.md', 'DAILY-BREADTH.md')


def git(cwd, *args):
    return subprocess.run(['git', '-C', str(cwd), *args], capture_output=True, text=True, check=True, timeout=90).stdout.strip()


def publish(source=ROOT, repository=REPOSITORY, include_code=False, status_only=False):
    source = Path(source)
    files = ('market-breadth-status.json',) if status_only else DATA_FILES + (CODE_FILES if include_code else ())
    with tempfile.TemporaryDirectory(prefix='breadth-publish-') as directory:
        repo = Path(directory)/'repo'
        subprocess.run(['git', 'clone', '--quiet', '--depth', '1', repository, str(repo)], check=True, timeout=90)
        before = json.loads((repo/'market-breadth.json').read_text()) if (repo/'market-breadth.json').exists() else {}
        current = json.loads((source/'market-breadth.json').read_text())
        if before.get('asOf', '') > current.get('asOf', ''):
            raise ValueError('Production already has a newer close; refusing to publish older local data/status')
        newer_remote = (before.get('asOf', ''), before.get('generatedAt', '')) > (current.get('asOf', ''), current.get('generatedAt', ''))
        for name in files:
            if name == 'market-breadth.json' and newer_remote:
                continue
            shutil.copy2(source/name, repo/name)
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


def verify_live(expected, site=SITE, code=False, attempts=12, delay=10):
    from daily_breadth import validate_snapshot
    error = None
    for attempt in range(attempts):
        try:
            stamp = str(time.time_ns())
            data = fetch(f'{site}/market-breadth.json?verify={stamp}', attempts=1, timeout=10)
            validate_snapshot(data, expected)
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
