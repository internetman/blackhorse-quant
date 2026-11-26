"""Read-only verification of a pinned Heima checkout and scheduler preview."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

REQUIRED = (
    "mac_mini_scheduler.py", "m2_mini_worker.py", "m2_incremental.py",
    "ffd_history.py", "close_target.py", "trading_calendar.py", "market_breadth.py",
    "market-trading-calendar.json", "deployment/com.heima.refresh.plist.example",
    "deployment/m2-worker-wrapper.sh.example",
)
GIT = Path("/usr/bin/git")


def checked(args, env):
    proc = subprocess.run(args, text=True, capture_output=True, check=False, timeout=30, env=env)
    if proc.returncode != 0:
        # A local command can echo arbitrary paths/config; avoid exposing its stderr.
        raise ValueError("local Git or Python preflight command failed")
    return proc.stdout.rstrip("\n")


def pinned_checkout(path, expected, *, git=GIT):
    if not re.fullmatch(r"(?:[a-f0-9]{40}|[a-f0-9]{64})", expected):
        raise ValueError("expected-commit must be the full reviewed lowercase Git object ID")
    root = path.resolve(strict=True)
    env = {key:value for key,value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null", GIT_TERMINAL_PROMPT="0",
               GIT_OPTIONAL_LOCKS="0", GIT_LFS_SKIP_SMUDGE="1")
    args = [str(git),"--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false",
            "-c","core.hooksPath=/dev/null","-C",str(root)]
    if Path(checked([*args,"rev-parse","--show-toplevel"],env)).resolve() != root:
        raise ValueError("checkout must be the Git working tree root")
    head = checked([*args,"rev-parse","--verify","HEAD^{commit}"],env)
    if expected != head:
        raise ValueError("checked-out commit differs from the reviewed pinned commit")
    # Compare plain file bytes to the reviewed tree, without Git status/filter
    # execution. Do not trust Git index flags or smudge/clean hooks on this host.
    tree = {}
    for entry in checked([*args,"ls-tree","-rz","--full-tree",head],env).split("\0"):
        if not entry:
            continue
        header, rel = entry.split("\t",1)
        mode, kind, oid = header.split()
        if mode not in ("100644","100755") or kind != "blob":
            raise ValueError("reviewed checkout contains a symlink or non-file Git entry")
        tree[rel] = oid
    if not set(REQUIRED) <= set(tree):
        raise ValueError("reviewed checkout lacks a required tracked file")
    seen = set()
    for here, dirs, files in os.walk(root, followlinks=False):
        parent = Path(here)
        if parent == root:
            dirs[:] = [d for d in dirs if d != ".git"]
            files = [f for f in files if f != ".git"]  # permitted Git administrative pointer
        if any(not stat.S_ISDIR((parent/d).lstat().st_mode) for d in dirs):
            raise ValueError("checkout must be clean; unexpected directory symlink")
        for name in files:
            path = parent/name
            rel = path.relative_to(root).as_posix()
            st = path.lstat()
            oid = tree.get(rel)
            if oid is None or not stat.S_ISREG(st.st_mode):
                raise ValueError("checkout must be clean with no untracked or ignored files")
            h = hashlib.sha1() if len(oid)==40 else hashlib.sha256()
            h.update(("blob " + str(st.st_size) + "\0").encode("ascii"))
            with path.open("rb") as stream:
                for part in iter(lambda: stream.read(256*1024), b""):
                    h.update(part)
            if h.hexdigest() != oid:
                raise ValueError("checkout file differs from pinned commit")
            seen.add(rel)
    if seen != set(tree):
        raise ValueError("checkout is missing a pinned tracked file")
    return root, head


PROBE = r"""
import ast, datetime as dt, fcntl, json, pathlib, ssl, sys
from zoneinfo import ZoneInfo
if sys.version_info < (3,9):
    raise ValueError('Requires Python 3.9 or newer')
root=pathlib.Path(sys.argv[1])
files=['mac_mini_scheduler.py','close_target.py','trading_calendar.py','market_breadth.py',
       'm2_mini_worker.py','m2_incremental.py','ffd_history.py']
for name in files:
    ast.parse((root/name).read_text(),feature_version=(3,9))
    compile((root/name).read_text(),name,'exec')
sys.path.append(str(root))
import mac_mini_scheduler as s
zone=ZoneInfo('Asia/Shanghai')
now=dt.datetime.fromisoformat(sys.argv[2]).astimezone(zone) if sys.argv[2] else dt.datetime.now(zone)
calendar=s.load_calendar(root/'market-trading-calendar.json',now.year,allow_fetch=False)
# Deliberately use no valid state or worker, and leave execute=False. Abort if
# the scheduler interface stops producing a no-worker result.
def refused(*a,**kw):
    raise AssertionError('dry-run must not launch a worker')
out=s.tick(now,calendar,pathlib.Path('/nonexistent-heima-preflight-state'),
           pathlib.Path('/nonexistent-heima-preflight-worker'),execute=False,run=refused)
if out.get('status') not in ('preview_no_worker','outside_window'):
    raise ValueError('scheduler preview returned an unexpected state')
print(json.dumps({'pythonVersion':'.'.join(map(str,sys.version_info[:3])),
                  'marketClock':now.isoformat(),'scheduler':out}))
"""


def report(checkout, expected, python, sample=None):
    root, sha = pinned_checkout(checkout, expected)
    if not python.is_absolute() or not os.access(python, os.X_OK):
        raise ValueError("pass an existing absolute executable Python path")
    if sample is not None and dt.datetime.fromisoformat(sample).utcoffset() is None:
        raise ValueError("sample preview time must include a timezone offset")
    # Exclude credential/search paths; run with isolated imports and no .pyc writes.
    env = {k:os.environ[k] for k in ("HOME","PATH","LANG","LC_ALL","TZDIR") if k in os.environ}
    ping = json.loads(checked([str(python),"-I","-B","-S","-c",PROBE,str(root),sample or ""],env))
    return dict(status="preview_ok", commit=sha, schedulerInstalled=False,
                workerStarted=False, networkUsed=False, ffdPointsUsed=0, stateCreated=False, **ping)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--checkout",type=Path,required=True)
    p.add_argument("--expected-commit",required=True)
    p.add_argument("--python",type=Path,default=Path(sys.executable))
    p.add_argument("--at",help="Optional ISO preview timestamp with timezone offset")
    a=p.parse_args()
    try:
        print(json.dumps(report(a.checkout,a.expected_commit,a.python,a.at),ensure_ascii=False))
    except (OSError,ValueError,TypeError,subprocess.SubprocessError) as e:
        p.error(str(e))


if __name__ == "__main__":
    main()
