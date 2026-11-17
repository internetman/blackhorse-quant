"""Local launchd tick for a dedicated Mac mini. Preview unless explicitly enabled."""
from __future__ import annotations

import argparse
import datetime as dt
import errno
import fcntl
import json
import os
import stat
import subprocess
import tempfile
from pathlib import Path
from zoneinfo import ZoneInfo

from close_target import close_target
from trading_calendar import is_trading_day, load_calendar

ZONE = ZoneInfo('Asia/Shanghai')
NOON_ATTEMPTS = (dt.time(12, 7), dt.time(12, 27))
CLOSE_ATTEMPTS = (dt.time(16, 40), dt.time(17, 40), dt.time(18, 40))
SAFE_RETRY = 'retryable_no_paid_query'
SUCCESS = frozenset(('verified', 'already_current'))
PRIVATE_READY = 'private_preview_ready'
M2_SCOPE = 'four-sector-close-v1'


def candidate(now, calendar):
    now = now.astimezone(ZONE)
    wall = now.time().replace(tzinfo=None)
    trading = is_trading_day(now.date(), calendar)
    if trading and dt.time(11, 35) <= wall < dt.time(12, 55):
        slot = sum(wall >= stamp for stamp in NOON_ATTEMPTS)
        return ('midday', now.date().isoformat(), slot) if slot else None
    # Do not start extended close work on a trading day where it might hold
    # the shared lock over the noon update. Missing closes are rechecked later.
    if trading and dt.time(11) <= wall < dt.time(13):
        return None
    if not trading or wall < dt.time(16):
        return ('close', close_target(now, calendar), 4)  # missed final close catch-up
    slot = sum(wall >= stamp for stamp in CLOSE_ATTEMPTS)
    return ('close', close_target(now, calendar), slot) if slot else None


def private_directory(path):
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    mode = path.lstat().st_mode
    if not stat.S_ISDIR(mode) or mode & 0o077 or path.stat().st_uid != os.getuid():
        raise ValueError('State directory must be owned by the current user and private (0700)')


def save_state(path, data):
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as out:
        temp = Path(out.name)
        try:
            json.dump(data, out)
            out.flush()
            os.fsync(out.fileno())
            os.replace(temp, path)
            fd = os.open(path.parent, os.O_RDONLY)
            try:
                try:
                    os.fsync(fd)
                except OSError as exc:
                    # Some macOS filesystems do not support directory fsync.
                    if exc.errno not in (errno.EINVAL, errno.ENOTSUP):
                        raise
            finally:
                os.close(fd)
        finally:
            temp.unlink(missing_ok=True)


def tick(now, calendar, directory, worker, execute=False, run=subprocess.run):
    job = candidate(now, calendar)
    if job is None:
        return {'status': 'outside_window'}
    session, date, slot = job
    receipt = {'session': session, 'targetDate': date, 'slot': slot}
    if not execute:
        return dict(receipt, status='preview_no_worker')
    if not directory.is_absolute() or not worker.is_absolute():
        raise ValueError('Use absolute worker and state directory paths')
    private_directory(directory)
    lock_path = directory / 'run.lock'
    # macOS has fcntl.flock even when a shell flock command is unavailable.
    with os.fdopen(os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600), 'r+') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return dict(receipt, status='busy')
        path = directory / 'launchd-receipts.json'
        state = json.loads(path.read_text()) if path.exists() else {}
        if not isinstance(state, dict):
            raise ValueError('Invalid scheduler journal')
        if any(r.get('status') in ('inflight', 'uncertain') for r in state.values()):
            return dict(receipt, status='reconcile_pending_run')
        key = f'{session}:{date}'
        previous = state.get(key, {})
        if previous.get('status') in SUCCESS | {PRIVATE_READY} or slot <= previous.get('slot', 0):
            return dict(receipt, status='already_attempted')
        # Persist possible quota use before launching; a crash cannot retry
        # an unknown paid request silently. The worker owns its quota ledger.
        state[key] = dict(receipt, status='inflight')
        save_state(path, state)
        evidence = {}
        try:
            if session == 'midday':
                china = now.astimezone(ZONE)
                deadline = china.replace(hour=12, minute=55, second=0, microsecond=0)
                timeout = min(300, (deadline - china).total_seconds())
            else:
                timeout = 900
            p = run([str(worker), '--session', session, '--target-date', date,
                     '--state-dir', str(directory)], check=False, capture_output=True,
                    text=True, timeout=timeout)
            result = json.loads(p.stdout)
            if p.returncode or result['targetDate'] != date or result['session'] != session:
                raise ValueError('date/session verification failed')
            status = result['status']
            if status == SAFE_RETRY:
                if type(result.get('historyCalls')) is not int or result['historyCalls'] != 0:
                    raise ValueError('retry not verified as pre-collection')
            elif status in SUCCESS:
                if result.get('verifiedDate') != date or result.get('publicationVerified') is not True:
                    raise ValueError('publication not verified')
            elif status == PRIVATE_READY:
                calls = result.get('historyCalls')
                if (session != 'close' or result.get('scope') != M2_SCOPE or result.get('verifiedDate') != date
                        or result.get('publicationVerified') is not False or type(calls) is not int or calls < 0):
                    raise ValueError('private preview scope/date or quota evidence not verified')
                evidence = {'scope': M2_SCOPE, 'publicationVerified': False, 'historyCalls': calls}
            else:
                raise ValueError('unrecognized result')
        except (subprocess.SubprocessError, OSError, ValueError, TypeError, KeyError):
            status = 'uncertain'
        state[key] = dict(receipt, status=status, **evidence)
        save_state(path, state)
        return state[key]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--calendar', required=True, type=Path)
    p.add_argument('--state-dir', required=True, type=Path)
    p.add_argument('--worker', required=True, type=Path)
    p.add_argument('--execute', action='store_true')
    a = p.parse_args()
    os.umask(0o077)
    now = dt.datetime.now(ZONE)
    calendar = load_calendar(a.calendar, now.year, allow_fetch=False)
    print(json.dumps(tick(now, calendar, a.state_dir, a.worker, a.execute)), flush=True)


if __name__ == '__main__':
    main()
