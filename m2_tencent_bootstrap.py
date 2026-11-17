"""One-time, bounded qfq seed recovery from Tencent; never calls FFD."""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import time
import urllib.parse
import urllib.request

from m2_incremental import OVERLAP, SECTORS, days_between, validate_seed
from m2_seed_bridge import bridge, load_ffd_rows, vendor_symbol
from trading_calendar import expected_close, is_trading_day, load_calendar
from zoneinfo import ZoneInfo

URL = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
TARGET_BARS = 340
MAX_PAYLOAD_BYTES = 3 * 1024 * 1024
REQUEST_INTERVAL = 1.0
MAX_EXECUTE = 360
ZONE = ZoneInfo("Asia/Shanghai")


def digest(data):
    return hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_original(query):
    # No credentials, query key, alternate routes, or retries; verified TLS.
    opener = urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(query,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
    with opener.open(req,timeout=12) as res:
        raw = res.read(MAX_PAYLOAD_BYTES+1)
    if len(raw) > MAX_PAYLOAD_BYTES:
        raise ValueError("Tencent response exceeds allowed size")
    return json.loads(raw)


def request_url(code, cutoff):
    return URL + "?" + urllib.parse.urlencode({"param":f"{vendor_symbol(code)},day,,{cutoff},{TARGET_BARS},qfq"})


def require_private(path):
    st = path.lstat()
    if not path.is_absolute() or not stat.S_ISDIR(st.st_mode) or st.st_mode & 0o077 or st.st_uid != os.getuid():
        raise ValueError("requires owned mode-0700 private directory")


def save(path,data,*,exclusive=False):
    with tempfile.NamedTemporaryFile(mode="w",dir=path.parent,encoding="utf-8",delete=False) as f:
        name = Path(f.name)
        try:
            json.dump(data,f,ensure_ascii=False,allow_nan=False)
            f.flush()
            os.fsync(f.fileno())
            if exclusive:
                os.link(name,path)
            else:
                os.replace(name,path)
        finally:
            name.unlink(missing_ok=True)


def read_regular(path):
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError("not a regular saved data file")
    return json.loads(path.read_text())


def prepare(manifest, cutoff, overlap_files, calendar, now):
    if (dt.date.fromisoformat(cutoff).isoformat() != cutoff or cutoff > expected_close(now,calendar)
            or not is_trading_day(dt.date.fromisoformat(cutoff),calendar)):
        raise ValueError("use a verified completed cutoff date")
    if not manifest.get("membershipSource") or not manifest.get("membershipDate") or manifest["membershipDate"] > cutoff:
        raise ValueError("dated frozen membership evidence required")
    securities = [{**s,"risk":s.get("risk","unknown")} for s in manifest["securities"]]
    validate_seed(securities)
    overlap = {}
    for p in overlap_files:
        native = load_ffd_rows(read_regular(p))
        for code, dated in native.items():
            dst = overlap.setdefault(code,{})
            for day, bar in dated.items():
                if day in dst and dst[day] != bar:
                    raise ValueError("saved FFD overlap conflict")
                dst[day] = bar
    overlap_start = (dt.date.fromisoformat(cutoff)-dt.timedelta(days=24)).isoformat()
    required_days = days_between(overlap_start,cutoff,calendar)[-OVERLAP:]
    if len(required_days) != OVERLAP:
        raise ValueError("verified calendar does not cover three close overlaps")
    covered = {k:0 for k in SECTORS}
    risk_known = {k:0 for k in SECTORS}
    ready = {}
    for s in securities:
        code = s["code"]
        if not all(d in overlap.get(code,{}) for d in required_days):
            continue
        covered[s["sector"]] += 1
        # An archived name alone isn't issuer status, even with verified OHLC.
        if s["risk"] != "unknown" and s.get("riskAsOf") == cutoff and s.get("riskEvidence"):
            risk_known[s["sector"]] += 1
        ready[code] = overlap[code]
    return ready, covered, risk_known


def validated_history(wrap,evidence,code,cutoff,calendar):
    rows, ev = bridge(wrap,evidence,code,cutoff)
    full_dates = days_between(rows[0]["date"],cutoff,calendar)
    if [r["date"] for r in rows] != full_dates or len(rows) > TARGET_BARS:
        raise ValueError("historical sessions contain gaps or exceed bounded response")
    return rows,ev


def run(state, cutoff, manifest, overlap_files, calendar, now, *, limit, execute=False,
        codes=None, fetch=fetch_original, sleep=time.sleep):
    if type(limit) is not int or not 1 <= limit <= MAX_EXECUTE:
        raise ValueError(f"explicit request limit must be 1 through {MAX_EXECUTE}")
    require_private(state)
    ready, possible, risk = prepare(manifest,cutoff,overlap_files,calendar,now)
    frozen = {s["code"] for s in manifest["securities"]}
    if codes is not None and (len(codes) != len(set(codes)) or not set(codes) <= frozen):
        raise ValueError("requested symbols are not unique members of original frozen scope")
    checks = sorted(ready) if codes is None else [c for c in codes if c in ready]
    history_dir = state/f"tencent-{cutoff}"
    receipt_dir = state/f"tencent-receipts-{cutoff}"
    for path in (history_dir,receipt_dir):
        if path.exists():
            require_private(path)
    pending, valid, held = [], 0, 0
    for code in checks:
        raw_path = history_dir/f"{code}.json"
        if raw_path.exists():
            try:
                validated_history(read_regular(raw_path),ready[code],code,cutoff,calendar)
                valid += 1
            except (OSError, ValueError, KeyError, TypeError, IndexError):
                held += 1
        elif (receipt_dir/f"{code}.json").exists():
            held += 1  # Prior request uncertain/failed; never repeat silently.
        else:
            pending.append(code)
    selected = pending[:limit]
    gate_possible = all(possible[k]*100 >= SECTORS[k]*95 for k in SECTORS)
    report = dict(status="plan_only",seedCutoff=cutoff,scope="four-sector-close-v1",
                  availableOldOverlapBySector=possible,qualifiedRiskAtSeedCutoffBySector=risk,
                  theoreticalHistoryGatePossible=gate_possible,reused=valid,held=held,
                  hasThreeOldOverlap=len(ready),planned=min(limit,len(pending)),
                  remainingAfterThisBatch=max(0,len(pending)-len(selected)),requestLimit=limit,
                  requestsMade=0,validatedNew=0,ffdCalls=0,ffdPointsUsed=0,barsPublished=False)
    if not execute or not selected:
        return report
    # A large recovery is wasted when frozen overlap cannot reach its 95% gate.
    if not gate_possible and (codes is None or len(selected) != 1):
        return dict(report,status="blocked_overlap_coverage")
    if held:
        return dict(report,status="held_saved_attempt_requires_reconciliation")
    with os.fdopen(os.open(state/f"tencent-{cutoff}.lock",
                           os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600),"r+") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        history_dir.mkdir(mode=0o700,exist_ok=True)
        receipt_dir.mkdir(mode=0o700,exist_ok=True)
        require_private(history_dir)
        require_private(receipt_dir)
        report["status"] = "bounded_batch"
        for code in selected:
            out, log = history_dir/f"{code}.json",receipt_dir/f"{code}.json"
            if out.exists() or log.exists():
                continue   # Inventory changed after preflight; do not fetch.
            url = request_url(code,cutoff)
            receipt = dict(state="pending",code=code,cutoff=cutoff,requestURL=url,provider="Tencent")
            save(log,receipt,exclusive=True)
            if report["requestsMade"]:
                sleep(REQUEST_INTERVAL)
            report["requestsMade"] += 1
            try:
                raw = fetch(url)
                digest_value = digest(raw)
                wrap = dict(provider="Tencent",adjustment="qfq",effectiveKey="qfqday",cutoff=cutoff,
                            symbol=vendor_symbol(code),sha256=digest_value,response=raw)
                rows, ev = validated_history(wrap,ready[code],code,cutoff,calendar)
                save(out,wrap,exclusive=True)
                save(log,dict(receipt,state="verified",responseSha256=digest_value,rows=len(rows),
                              overlap=ev["overlap"],volumeScale=ev["volumeScale"]))
                report["validatedNew"] += 1
            except (OSError,ValueError,KeyError,TypeError,IndexError) as exc:
                # Stop after the first anomalous response. Do not log exception
                # text or overwrite originals, and don't switch provider.
                save(log,dict(receipt,state="reconciliation_needed",exceptionType=type(exc).__name__))
                report["status"] = "held_provider_or_validation"
                break
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--state-dir",required=True,type=Path)
    p.add_argument("--manifest",required=True,type=Path)
    p.add_argument("--ffd-overlap",required=True,type=Path,nargs="+",help="Saved private files only")
    p.add_argument("--cutoff",required=True)
    p.add_argument("--limit",type=int,required=True)
    p.add_argument("--symbols",nargs="+",help="Optional explicit subset; use one for a canary")
    p.add_argument("--calendar",type=Path)
    p.add_argument("--execute",action="store_true",help="Explicitly enable capped free-source requests; never a schedule")
    a=p.parse_args()
    now=dt.datetime.now(ZONE)
    os.umask(0o077)
    calendar=load_calendar(a.calendar,now.year,allow_fetch=False) if a.calendar else load_calendar(year=now.year)
    state=a.state_dir.absolute()
    repo=Path(__file__).resolve().parent
    real=state.resolve(strict=True)
    if real == repo or repo in real.parents:
        p.error("private state must be outside the checkout")
    try:
        print(json.dumps(run(state,a.cutoff,read_regular(a.manifest),a.ffd_overlap,calendar,now,
                             limit=a.limit,execute=a.execute,codes=a.symbols),ensure_ascii=False))
    except (OSError,ValueError,TypeError,KeyError) as exc:
        p.error(str(exc))


if __name__=="__main__":
    main()
