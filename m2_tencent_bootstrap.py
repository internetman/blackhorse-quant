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
import urllib.error
import urllib.parse
import urllib.request

from m2_incremental import M2_SYMBOL, SECTORS, days_between, validate_seed
from m2_seed_bridge import (BRIDGE_FAILURES, BridgeValidationError, bridge, merge_ffd_archives,
                            required_overlap_dates, vendor_symbol)
from trading_calendar import expected_close, is_trading_day, load_calendar
from zoneinfo import ZoneInfo

URL = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
TARGET_BARS = 340
MAX_PAYLOAD_BYTES = 3 * 1024 * 1024
REQUEST_INTERVAL = 1.0
MAX_EXECUTE = 360
ZONE = ZoneInfo("Asia/Shanghai")


FAILURE_REASONS = BRIDGE_FAILURES | frozenset({
    "provider_http_redirect_refused","provider_http_rate_limited","provider_http_access_refused",
    "provider_http_error","provider_timeout","provider_transport","provider_response_size",
    "provider_invalid_json","provider_request_failed","validation_unclassified","private_storage",
})


class ResponseSizeError(ValueError):
    """The public provider response exceeded the byte limit."""


def failure_reason(exc,phase):
    if phase == "persist":
        return "private_storage"
    if phase == "validate":
        reason = getattr(exc,"reason",None) if isinstance(exc,BridgeValidationError) else None
        return reason if isinstance(reason,str) and reason in BRIDGE_FAILURES else "validation_unclassified"
    if isinstance(exc,urllib.error.HTTPError):
        if type(exc.code) is not int:
            return "provider_http_error"
        if 300 <= exc.code < 400:
            return "provider_http_redirect_refused"
        if exc.code == 429:
            return "provider_http_rate_limited"
        if exc.code in (401,403):
            return "provider_http_access_refused"
        return "provider_http_error"
    if isinstance(exc,TimeoutError) or (isinstance(exc,urllib.error.URLError) and isinstance(exc.reason,TimeoutError)):
        return "provider_timeout"
    if isinstance(exc,ResponseSizeError):
        return "provider_response_size"
    if isinstance(exc,(json.JSONDecodeError,UnicodeError)):
        return "provider_invalid_json"
    if isinstance(exc,OSError):
        return "provider_transport"
    return "provider_request_failed"


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
        raise ResponseSizeError("Tencent response exceeds allowed size")
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
    required_days = required_overlap_dates(cutoff,calendar)
    overlap, quarantined, outside = merge_ffd_archives(
        (read_regular(p) for p in overlap_files),
        expected_symbols={s["code"] for s in securities},required_dates=required_days)
    covered = {k:0 for k in SECTORS}
    risk_known = {k:0 for k in SECTORS}
    ready = {}
    for s in securities:
        code = s["code"]
        if code.endswith(".BJ"):
            continue  # In the original fixed denominator; not queried by this venue adapter.
        if not all(d in overlap.get(code,{}) for d in required_days):
            continue
        covered[s["sector"]] += 1
        # An archived name alone isn't issuer status, even with verified OHLC.
        if s["risk"] != "unknown" and s.get("riskAsOf") == cutoff and s.get("riskEvidence"):
            risk_known[s["sector"]] += 1
        ready[code] = overlap[code]
    return ready, covered, risk_known, required_days, quarantined, outside


def validated_history(wrap,evidence,code,cutoff,calendar,required):
    rows, ev = bridge(wrap,evidence,code,cutoff,required_dates=required)
    if len(rows) > TARGET_BARS:
        raise BridgeValidationError("history_response_limit","historical response exceeds bounded bar count")
    try:
        full_dates = days_between(rows[0]["date"],cutoff,calendar)
    except (KeyError,ValueError,TypeError):
        raise BridgeValidationError("archive_calendar_unverified","source history falls outside verified calendar") from None
    if [r["date"] for r in rows] != full_dates:
        raise BridgeValidationError("history_trading_dates","historical sessions contain exchange-date gaps")
    return rows,ev


def global_hold_count(receipt_dir,history_dir,cutoff):
    # Check the whole private journal, not only whichever codes were selected.
    # Old receipts without diagnostic detail still hold and are never migrated.
    blocked = 0
    for path in receipt_dir.glob("*.json"):
        if path.name == "archive-null-audit.json":
            continue
        try:
            if not M2_SYMBOL.fullmatch(path.stem):
                raise ValueError("unknown journal record")
            receipt = read_regular(path)
            if (receipt.get("cutoff") != cutoff or receipt.get("code") != path.stem
                    or receipt.get("state") != "verified"
                    or not stat.S_ISREG((history_dir/f"{path.stem}.json").lstat().st_mode)):
                blocked += 1
        except (OSError,ValueError,TypeError,AttributeError):
            blocked += 1
    return blocked


def run(state, cutoff, manifest, overlap_files, calendar, now, *, limit, execute=False,
        codes=None, fetch=fetch_original, sleep=time.sleep):
    if type(limit) is not int or not 1 <= limit <= MAX_EXECUTE:
        raise ValueError(f"explicit request limit must be 1 through {MAX_EXECUTE}")
    require_private(state)
    ready, possible, risk, required, quarantined, outside = prepare(manifest,cutoff,overlap_files,calendar,now)
    frozen = {s["code"] for s in manifest["securities"]}
    if codes is not None and (len(codes) != len(set(codes)) or not set(codes) <= frozen):
        raise ValueError("requested symbols are not unique members of original frozen scope")
    checks = sorted(ready) if codes is None else [c for c in codes if c in ready]
    history_dir = state/f"tencent-{cutoff}"
    receipt_dir = state/f"tencent-receipts-{cutoff}"
    for path in (history_dir,receipt_dir):
        if path.exists():
            require_private(path)
    global_holds = global_hold_count(receipt_dir,history_dir,cutoff)
    pending, valid, held = [], 0, 0
    for code in checks:
        raw_path = history_dir/f"{code}.json"
        if raw_path.exists():
            try:
                validated_history(read_regular(raw_path),ready[code],code,cutoff,calendar,required)
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
                  theoreticalHistoryGatePossible=gate_possible,reused=valid,held=held,globalReconciliationHolds=global_holds,
                  ffdQuarantinedSymbolCount=sum(c in frozen for c in quarantined),
                  ffdQuarantinedArchiveSymbolCount=len(quarantined),
                  requiredOverlapDates=required,
                  ffdOutOfWindowNullSymbolCount=len(outside),
                  ffdOutOfWindowNullRowCount=sum(map(len,outside.values())),
                  heldUnverifiedVenue=sum(s["code"].endswith(".BJ") for s in manifest["securities"]),
                  hasThreeOldOverlap=len(ready),planned=min(limit,len(pending)),
                  remainingAfterThisBatch=max(0,len(pending)-len(selected)),requestLimit=limit,
                  requestsMade=0,validatedNew=0,ffdCalls=0,ffdPointsUsed=0,barsPublished=False)
    if not execute:
        return report
    if global_holds or held:
        return dict(report,status="held_saved_attempt_requires_reconciliation")
    if not selected:
        return dict(report,status="no_verified_bootstrap_candidates")
    # A large recovery is wasted when frozen overlap cannot reach its 95% gate.
    if not gate_possible and (codes is None or len(selected) != 1):
        return dict(report,status="blocked_overlap_coverage")
    with os.fdopen(os.open(state/f"tencent-{cutoff}.lock",
                           os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600),"r+") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        history_dir.mkdir(mode=0o700,exist_ok=True)
        receipt_dir.mkdir(mode=0o700,exist_ok=True)
        require_private(history_dir)
        require_private(receipt_dir)
        current_holds = global_hold_count(receipt_dir,history_dir,cutoff)
        if current_holds:
            return dict(report,status="held_saved_attempt_requires_reconciliation",globalReconciliationHolds=current_holds)
        archive_audit = dict(requiredOverlapDates=required,inWindow=quarantined,outsideWindow=outside)
        audit_path = receipt_dir/"archive-null-audit.json"
        if audit_path.exists():
            if read_regular(audit_path) != archive_audit:
                raise ValueError("private bootstrap archive-null audit changed; review before continuing")
        else:
            save(audit_path,archive_audit,exclusive=True)
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
            phase = "request"
            try:
                raw = fetch(url)
                phase = "validate"
                digest_value = digest(raw)
                wrap = dict(provider="Tencent",adjustment="qfq",effectiveKey="qfqday",cutoff=cutoff,
                            symbol=vendor_symbol(code),sha256=digest_value,response=raw)
                rows, ev = validated_history(wrap,ready[code],code,cutoff,calendar,required)
                phase = "persist"
                save(out,wrap,exclusive=True)
                save(log,dict(receipt,state="verified",responseSha256=digest_value,rows=len(rows),
                              overlap=ev["overlap"],volumeScale=ev["volumeScale"]))
                report["validatedNew"] += 1
            except Exception as exc:
                # Classify without storing exception text, raw payload, price,
                # authentication metadata or any inferred provider permission.
                reason = failure_reason(exc,phase)
                try:
                    save(log,dict(receipt,state="reconciliation_needed",failureReason=reason))
                except OSError:
                    # Pending receipt still prevents further use; do not retry
                    # a network request after local journal update failure.
                    reason = "private_storage"
                report.update(status="held_provider_or_validation",failureReason=reason)
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
