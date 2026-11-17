"""Offline, exact reconciliation of the 360 archive identities with dated SCKD membership."""
from __future__ import annotations
import argparse
from datetime import date
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from urllib.parse import urlencode

from m2_incremental import M2_SYMBOL, SECTORS, validate_seed
from trading_calendar import is_trading_day, load_calendar

SCKD = "https://sckd.dapanyuntu.com/api/api/stock_daily_data_by_industry_and_date"
DIGITS = re.compile(r"[0-9]{1,6}(?:[.]0+)?")
SHA256 = re.compile(r"[0-9a-f]{64}")
MAX = 2 * 1024 * 1024


def day(value):
    if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
        raise ValueError('Use a canonical date')
    return value


def numeric_code(value):
    # SCKD wire values sometimes have a decimal zero suffix or lost leading
    # zeros. Do not round, interpret nonzero fractions, or guess aliases.
    if type(value) not in (int, float, str) or not DIGITS.fullmatch(str(value)):
        raise ValueError('SCKD stock code is not an integral native identity')
    return f'{int(Decimal(str(value))):06d}'


def exchange_code(digits):
    venue = {'0':'SZ', '3':'SZ', '6':'SH', '4':'BJ', '8':'BJ', '9':'BJ'}.get(digits[0])
    if venue is None:
        raise ValueError('Unverified exchange prefix')
    return digits + '.' + venue


def archive_ids(archive, target):
    if not isinstance(archive, list) or len(archive) != sum(SECTORS.values()):
        raise ValueError('Original frozen history archive must retain all 360 identities')
    seen = set()
    for r in archive:
        raw = r['code']
        if isinstance(raw,str) and M2_SYMBOL.fullmatch(raw):
            code = exchange_code(raw[:6])
            if code != raw: raise ValueError('Archive exchange suffix disagrees')
        else:
            code = exchange_code(numeric_code(raw))
        if (code in seen or day(r['asOfDate']) > target or type(r['bars']) is not int
                or r['bars'] <= 0 or not isinstance(r['sha256'],str) or not SHA256.fullmatch(r['sha256'])):
            raise ValueError('Invalid or duplicate archived evidence identity')
        seen.add(code)
    return seen


def exact_membership(archive, bundles, target):
    target = day(target)
    archive_set = archive_ids(archive,target)
    seen_sectors, records = set(), {}
    if not isinstance(bundles,list) or len(bundles) != len(SECTORS):
        raise ValueError('Need one same-date SCKD response for each four sectors')
    for b in bundles:
        sector = b.get('industry')
        rows = b.get('data')
        if (sector not in SECTORS or sector in seen_sectors or b.get('date') != target
                or not isinstance(rows,list) or len(rows) != SECTORS[sector]):
            raise ValueError('SCKD date, industry or exact sector count mismatch')
        seen_sectors.add(sector)
        for row in rows:
            if row.get('date') != target or row.get('industry') != sector:
                raise ValueError('SCKD row date or sector does not match bundle')
            code = exchange_code(numeric_code(row.get('stock_code')))
            name = row.get('stock_name')
            if (not isinstance(name,str) or not name.strip() or any(ord(c)<32 for c in name)
                    or code in records):
                raise ValueError('SCKD row has a missing name or duplicate identity')
            records[code] = dict(code=code,name=name.strip(),sector=sector,risk='unknown')
    if archive_set != records.keys():
        raise ValueError('Dated SCKD union differs from the exact frozen original archive identities')
    securities = sorted(records.values(),key=lambda x:x['code'])
    validate_seed(securities)
    return dict(membershipDate=target,membershipSource=SCKD,securities=securities)


def load_saved(path):
    path = Path(path)
    props = path.lstat()
    if not stat.S_ISREG(props.st_mode) or not 0 < props.st_size <= MAX:
        raise ValueError('Expected regular bounded saved source file')
    raw = path.read_bytes()
    if len(raw) > MAX:
        raise ValueError('Saved source file exceeds size cap')
    return json.loads(raw),hashlib.sha256(raw).hexdigest()


def atomic_new(path, data):
    parent = path.parent.resolve(strict=True)
    info = parent.stat()
    study = Path(__file__).resolve().parent
    if (not stat.S_ISDIR(info.st_mode) or info.st_mode & 0o077 or info.st_uid != os.getuid()
            or parent == study or study in parent.parents):
        raise ValueError('Output must be outside the checkout in mode-0700 user-owned state')
    out_path = parent/path.name
    if out_path.exists() or out_path.is_symlink():
        raise ValueError('No output replacement')
    with tempfile.NamedTemporaryFile(dir=parent,mode='w',encoding='utf-8') as f:
        json.dump(data,f,ensure_ascii=False,allow_nan=False)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
        os.link(f.name,out_path)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',required=True,type=Path)
    p.add_argument('--as-of',required=True)
    p.add_argument('--calendar',required=True,type=Path)
    p.add_argument('--sckd',required=True,type=Path,nargs=len(SECTORS))
    p.add_argument('--write-to',type=Path,help='Optional new file outside repo in owner-only state')
    a = p.parse_args()
    os.umask(0o077)
    try:
        target = day(a.as_of)
        calendar = load_calendar(a.calendar,date.fromisoformat(target).year,allow_fetch=False)
        if not is_trading_day(date.fromisoformat(target),calendar):
            raise ValueError('Not a verified trading date')
        archive, arch_hash = load_saved(a.archive)
        loaded = [load_saved(x) for x in a.sckd]
        out = exact_membership(archive,[x[0] for x in loaded],target)
        out['evidence'] = dict(originalArchiveSha256=arch_hash,sourceBundles=[
            dict(industry=b['industry'],date=target,sha256=h,
                 nativeRawSha256=b.get('nativeRawSha256') if isinstance(b.get('nativeRawSha256'), str)
                   and SHA256.fullmatch(b['nativeRawSha256']) else None,sourceURL=SCKD+'?'+urlencode(
                dict(industry=b['industry'],date=target))) for b,h in loaded],
            method='exact archived 360-id union and all four fixed per-sector counts',risk='all_unknown')
        if a.write_to:
            atomic_new(a.write_to,out)
        print(json.dumps(dict(status='exact_membership_verified', date=target, bySector=SECTORS,
                              identities=len(out['securities']), riskKnown=0, outputWritten=bool(a.write_to)),
                         ensure_ascii=False))
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        p.error(str(exc))


if __name__=='__main__':
    main()
