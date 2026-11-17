"""Offline conversion of saved Tencent/FFD data into a private M2 seed."""
from __future__ import annotations

import argparse
from collections import defaultdict
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path

from m2_incremental import (FIELDS, M2_SYMBOL, OVERLAP, SECTORS, UNVERIFIED_VENUE,
                            days_between, valid_rows, validate_seed)
from trading_calendar import is_trading_day, load_calendar


def vendor_symbol(code):
    if not isinstance(code,str) or not M2_SYMBOL.fullmatch(code) or code.endswith(".BJ"):
        raise ValueError("Tencent bootstrap only accepts verified Shanghai/Shenzhen source scope")
    name, exchange = code.split(".")
    return exchange.lower() + name


def finite(*values):
    vals = tuple(float(v) for v in values)
    if not all(math.isfinite(x) for x in vals) or any(isinstance(v, bool) for v in values):
        raise ValueError("missing/nonfinite bar value")
    return vals


def convert_tencent(envelope, code, cutoff):
    sym = vendor_symbol(code)
    raw = envelope
    if "response" in envelope:
        if (envelope.get("symbol") != sym or envelope.get("provider") != "Tencent"
                or envelope.get("adjustment") != "qfq" or envelope.get("effectiveKey") != "qfqday"
                or envelope.get("cutoff") != cutoff):
            raise ValueError("cached Tencent provenance, cutoff or symbol mismatch")
        raw = envelope["response"]
        encoded = json.dumps(raw,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
        if hashlib.sha256(encoded).hexdigest() != envelope.get("sha256"):
            raise ValueError("Tencent cache digest mismatch")
    if raw.get("code") not in (0, "0"):
        raise ValueError("Tencent response not successful")
    node = raw["data"][sym]
    if "qfqday" not in node:
        # A "day" fallback is not independently verified adjusted data.
        raise ValueError("Tencent explicit qfqday series not available")
    rows = []
    for date, o, c, h, l, v, *_ in node["qfqday"]:
        oo, cc, hh, ll, vv = finite(o, c, h, l, v)
        rows.append(dict(date=date, open=oo, high=hh, low=ll, close=cc, volume=vv, amount=None))
    if not rows or rows[-1]["date"] != cutoff or any(r["date"] > cutoff for r in rows):
        raise ValueError("Tencent series does not terminate at requested close")
    return rows


def unwrap_ffd(data):
    # Original pilot saved the MCP call result containing a text JSON envelope.
    if "result" in data:
        data = json.loads(data["result"]["content"][0]["text"])
    elif "content" in data:
        data = json.loads(data["content"][0]["text"])
    return data


def load_ffd_archive(envelope):
    raw = unwrap_ffd(envelope)
    basis = raw.get("adjustment_execution") or {}
    if basis.get("requested") != "qfq" or basis.get("effective") != "qfq":
        raise ValueError("FFD overlap requires explicit qfq execution metadata")
    if raw.get("code") != 200:
        raise ValueError("FFD pilot request did not succeed")
    meta = raw.get("field_metadata") or {}
    for field, unit in (("volume","shares"),("amt","CNY")):
        cell = meta.get(field) or {}
        if cell.get("unit") != unit or cell.get("scale") != 1:
            raise ValueError("FFD overlap missing native volume/amount units")
    rows = raw.get("raw_rows")
    if rows is None and isinstance(raw.get("data"), dict):
        rows = raw["data"].get("raw_rows")
    if not isinstance(rows, list):
        raise ValueError("FFD pilot raw_rows missing")
    # Identity and dimensions must be known for every row, even a placeholder.
    # Only native null price cells in an otherwise attributable row are
    # quarantinable. Invalid currency, malformed complete data, unknown row
    # shape and duplicate observations fail the entire archive.
    native = tuple("amt" if k == "amount" else k for k in FIELDS)
    out = defaultdict(dict)
    held = defaultdict(dict)
    identities = set()
    for r in rows:
        if not isinstance(r,dict) or not {*native,"code","time","trade_currency"} <= r.keys():
            raise ValueError("malformed native FFD overlap row")
        code, day = r["code"], r["time"]
        if (not isinstance(code,str) or not M2_SYMBOL.fullmatch(code) or not isinstance(day,str)
                or dt.date.fromisoformat(day).isoformat() != day):
            raise ValueError("invalid overlap identity/date")
        key = (code,day)
        if key in identities:
            raise ValueError("duplicate FFD overlap code/date")
        identities.add(key)
        if r["trade_currency"] != "CNY":
            raise ValueError("overlap is not in CNY")
        vals = [r[k] for k in native]
        present = [v for v in vals if v is not None]
        # Prove all nonnull values at least have the native numeric shape;
        # explicit NULL cannot camouflage a malformed non-null cell.
        try:
            nonnull = {field:finite(val)[0] for field,val in zip(native,vals) if val is not None}
        except (TypeError, ValueError):
            raise ValueError("malformed native non-null FFD data") from None
        if any((value <= 0 if field in {"open","high","low","close"} else value < 0)
               for field,value in nonnull.items()):
            raise ValueError("invalid FFD overlap price, volume or turnover")
        if any(nonnull[lo] > nonnull[hi] for lo,hi in (("low","open"),("low","close"),("low","high"),
               ("open","high"),("close","high")) if lo in nonnull and hi in nonnull):
            raise ValueError("invalid FFD overlap OHLC")
        if len(present) != len(vals):
            held[code][day] = [field for field,val in zip(native,vals) if val is None]
            continue
        bar = dict(date=day, **dict(zip(FIELDS, finite(*vals))))
        if not (0 < bar["low"] <= min(bar["open"],bar["close"]) <= max(bar["open"],bar["close"]) <= bar["high"]):
            raise ValueError("invalid FFD overlap OHLC")
        if bar["volume"] < 0 or bar["amount"] < 0:
            raise ValueError("invalid FFD overlap volume/turnover")
        out[code][day] = bar
    return out, held, identities


def load_ffd_rows(envelope):
    """Compatibility view excludes the whole symbol after any native NULL."""
    out, held, _ = load_ffd_archive(envelope)
    return {code:days for code,days in out.items() if code not in held}


def required_overlap_dates(cutoff, calendar):
    day = dt.date.fromisoformat(cutoff)
    if day.isoformat() != cutoff or not is_trading_day(day,calendar):
        raise ValueError("overlap cutoff is not a verified exchange date")
    first = (day-dt.timedelta(days=24)).isoformat()
    expected = days_between(first,cutoff,calendar)[-OVERLAP:]
    if len(expected) != OVERLAP or expected[-1] != cutoff:
        raise ValueError("verified calendar does not cover all three close observations")
    return expected


def merge_ffd_archives(envelopes, *, expected_symbols=None, required_dates=None):
    merged = defaultdict(dict)
    all_nulls = defaultdict(dict)
    seen = set()
    required = None if required_dates is None else tuple(required_dates)
    if required is not None and (len(required) != OVERLAP or tuple(sorted(set(required))) != required
            or any(dt.date.fromisoformat(day).isoformat() != day for day in required)):
        raise ValueError("required overlap dates must be three unique canonical dates")
    for envelope in envelopes:
        rows, quarantined, keys = load_ffd_archive(envelope)
        if expected_symbols is not None and any(code not in expected_symbols for code,_ in keys):
            raise ValueError("FFD archived identity outside frozen manifest")
        if seen.intersection(keys):
            raise ValueError("duplicate persisted FFD overlap code/date")
        seen.update(keys)
        for code, days in rows.items():
            merged[code].update(days)
        for code, days in quarantined.items():
            all_nulls[code].update(days)
    held, outside = {}, {}
    for code, days in all_nulls.items():
        for day, missing in days.items():
            dest = held if required is None or day in required else outside
            dest.setdefault(code,{})[day] = missing
    for code in held:
        merged.pop(code,None)
    return merged, held, outside


def bridge(envelope, evidence, code, cutoff, *, required_dates=None):
    rows = convert_tencent(envelope, code, cutoff)
    tail = rows[-OVERLAP:]
    if required_dates is not None and [r["date"] for r in tail] != list(required_dates):
        raise ValueError("Tencent tail does not match three verified overlap dates")
    if len(tail) != OVERLAP or any(r["date"] not in evidence for r in tail):
        raise ValueError("missing FFD overlap on one or more last three sessions")
    used = [evidence[r["date"]] for r in tail]
    if any(abs(old[k]-new[k]) > 1e-8 for old,new in zip(tail,used) for k in FIELDS[:4]):
        raise ValueError("same-date adjusted OHLC disagree between Tencent and FFD")
    # Tencent feed unit is not uniform; infer one multiplier per complete series
    # using all last three overlap sessions and reject all ambiguous cases.
    scales = [scale for scale in (1, 100)
              if all(abs(old["volume"]*scale-new["volume"]) <= (50 if scale==100 else 1e-8)
                     for old,new in zip(tail,used))]
    if len(scales) != 1:
        raise ValueError("ambiguous or mixed Tencent volume units")
    scale = scales[0]
    merged = [dict(r,volume=r["volume"]*scale) for r in rows[:-OVERLAP]] + used
    return valid_rows(merged, permit_older_missing_amount=True), dict(volumeScale=scale,
              overlap=[r["date"] for r in used], originalOlderAmountUnavailable=True)


def build(manifest, cutoff, tencent_dir, ffd_paths, *, calendar=None):
    if not manifest.get("membershipSource") or not manifest.get("membershipDate"):
        raise ValueError("missing verified frozen universe evidence")
    if manifest["membershipDate"] > cutoff:
        raise ValueError("membership is newer than target seed cutoff")
    securities = []
    for item in manifest["securities"]:
        security = {k:item[k] for k in ("code","name","sector")}
        status = "unknown" if security["code"].endswith(".BJ") else item.get("risk", "unknown")
        # Risk snapshot must come from independently checked dated listing/
        # exchange event evidence; a quote name alone is not evidence of eligibility.
        if status in {"eligible","excluded"} and not (item.get("riskAsOf") == cutoff and item.get("riskEvidence")):
            status = "unknown"
        security["risk"] = status
        if status != "unknown":
            security["riskAsOf"] = item["riskAsOf"]
            security["riskEvidence"] = item["riskEvidence"]
        securities.append(security)
    validate_seed(securities)
    frozen = {s["code"] for s in securities}
    required = required_overlap_dates(cutoff, calendar if calendar is not None else load_calendar())
    overlap, quarantined, outside = merge_ffd_archives((json.loads(file.read_text()) for file in ffd_paths),
                                            expected_symbols=frozen, required_dates=required)
    seed = dict(schemaVersion=1, adjustment="qfq", volumeUnit="share", amountUnit="CNY",
                olderAmountsUnavailable=True,
                provenance="Verified Tencent qfq OHLCV + native FFD qfq OHLCV/amt overlap, freeze before reuse",
                membershipDate=manifest["membershipDate"], securities=securities, histories={},
                sourceArchiveNullAudit=dict(requiredOverlapDates=required,inWindow=quarantined,
                                            outsideWindow=outside))
    missing, passed, eligible_counts = {}, {}, {k: 0 for k in SECTORS}
    hist_counts = {k:0 for k in SECTORS}
    for item in securities:
        code = item["code"]
        if code in quarantined:
            missing[code] = {"reason":"native FFD cells explicitly null; symbol not screened",
                             "datesAndFields":quarantined[code]}
            continue
        if code.endswith(".BJ"):
            missing[code] = UNVERIFIED_VENUE
            continue
        try:
            file = tencent_dir / f"{code}.json"
            if not file.is_file():
                file = tencent_dir / f"{vendor_symbol(code)}.json"
            if not file.is_file():
                secid = ("1." if code.endswith(".SH") else "0.") + code[:6]
                file = tencent_dir / f"{secid}.json"
            rows, evidence = bridge(json.loads(file.read_text()), overlap[code], code, cutoff,
                                    required_dates=required)
            seed["histories"][code] = rows
            passed[code] = evidence
            hist_counts[item["sector"]] += 1
            if item["risk"] != "unknown":
                eligible_counts[item["sector"]] += 1
        except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
            missing[code] = type(exc).__name__
    return seed, dict(cutoff=cutoff, bridged=len(passed), omitted=len(missing),
                      riskUnknown=sum(s["risk"]=="unknown" for s in securities),
                      ffdQuarantinedSymbolCount=sum(code in frozen for code in quarantined),
                      ffdQuarantinedArchiveSymbolCount=len(quarantined),
                      requiredOverlapDates=required,
                      ffdOutOfWindowNullSymbolCount=len(outside),
                      ffdOutOfWindowNullRowCount=sum(map(len,outside.values())),
                      heldUnverifiedVenue=sum(s["code"].endswith(".BJ") for s in securities),
                      validHistoryBySector=hist_counts, validKnownRiskBySector=eligible_counts,
                      canReachHistoricalGate=all(hist_counts[k]*100 >= SECTORS[k]*95 for k in SECTORS),
                      canReachCoverageGate=all(eligible_counts[k]*100 >= SECTORS[k]*95 for k in SECTORS)), passed, missing


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--tencent-dir",type=Path,required=True)
    p.add_argument("--ffd-overlap",type=Path,required=True,nargs="+")
    p.add_argument("--cutoff",required=True)
    p.add_argument("--calendar",type=Path,help="Independently verified exchange calendar; never fetches")
    p.add_argument("--write-seed",type=Path,help="Explicitly write seed.json into this private mode-0700 directory")
    a=p.parse_args()
    if dt.date.fromisoformat(a.cutoff).isoformat() != a.cutoff:
        p.error("use ISO completed seed date")
    calendar = load_calendar(a.calendar,allow_fetch=False) if a.calendar else load_calendar()
    seed, report, passed, missing=build(json.loads(a.manifest.read_text()),a.cutoff,a.tencent_dir,a.ffd_overlap,
                                      calendar=calendar)
    if a.write_seed:
        state=a.write_seed.resolve(strict=True)
        repo=Path(__file__).resolve().parent
        if state.stat().st_mode & 0o077 or state == repo or repo in state.parents:
            p.error("requires a private mode-0700 directory outside repository")
        if not report["canReachHistoricalGate"]:
            p.error(f"insufficient private seed coverage; not written: {json.dumps(report,ensure_ascii=False)}")
        os.umask(0o077)
        final_seed = state/"seed.json"
        if final_seed.exists() or (state/"seed-bridge-receipt.json").exists():
            p.error("private seed/receipt already exists; refuses replacement")
        import tempfile
        for target, obj in ((state/"seed-bridge-receipt.json",dict(report,checks=passed,omissions=missing,archiveNullAudit=seed["sourceArchiveNullAudit"])),
                            (final_seed,seed)):
            with tempfile.NamedTemporaryFile(mode="w", dir=state, delete=True,encoding="utf-8") as out:
                json.dump(obj,out,ensure_ascii=False,allow_nan=False)
                out.flush()
                os.fsync(out.fileno())
                os.link(out.name,target)
    print(json.dumps(report,ensure_ascii=False))
    if not report["canReachHistoricalGate"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
