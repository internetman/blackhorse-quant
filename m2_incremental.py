"""One completed-date four-sector run. Inputs, receipts and history stay private."""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import json
import math
import re
import statistics
from pathlib import Path

from ffd_history import HistoryClient
from market_breadth import ZONE
from trading_calendar import expected_close, is_trading_day, load_calendar

FIELDS = ("open", "high", "low", "close", "volume", "amount")
SECTORS = {"半导体": 161, "消费电子": 97, "光伏设备": 76, "电子化学品": 26}
SEED_MIN = 319
KEEP = 330
OVERLAP = 3


def write(path, obj):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, allow_nan=False) + "\n")
    tmp.replace(path)


def days_between(first, last, calendar):
    start, end = dt.date.fromisoformat(first), dt.date.fromisoformat(last)
    return [(start + dt.timedelta(days=i)).isoformat() for i in range((end - start).days + 1)
            if is_trading_day(start + dt.timedelta(days=i), calendar)]


def valid_rows(rows, dates=None, *, permit_older_missing_amount=False):
    if not isinstance(rows, list) or len(rows) < SEED_MIN:
        raise ValueError("insufficient long historical seed")
    observed = []
    for i, bar in enumerate(rows):
        day = bar["date"]
        if dt.date.fromisoformat(day).isoformat() != day:
            raise ValueError("invalid historical date")
        observed.append(day)
        for key in FIELDS:
            v = bar[key]
            if key == "amount" and v is None and permit_older_missing_amount and i < len(rows) - OVERLAP:
                continue  # No amount is synthesized or used by S2 on these bars.
            if isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v):
                raise ValueError("invalid historical field")
            if (v <= 0 if key in FIELDS[:4] else v < 0):
                raise ValueError("invalid historical value")
        if not bar["low"] <= min(bar["open"], bar["close"]) <= max(bar["open"], bar["close"]) <= bar["high"]:
            raise ValueError("inconsistent historical OHLC")
    if observed != sorted(set(observed)) or (dates is not None and observed != dates):
        raise ValueError("missing, duplicate or unsorted historical session")
    return rows


def reconcile(old, incoming):
    # Three overlaps detect rebasing; they don't prove earlier action events.
    if len(old) < OVERLAP or len(incoming) <= OVERLAP:
        raise ValueError("insufficient independent overlap and new sessions")
    for prior, ffd in zip(old[-OVERLAP:], incoming[:OVERLAP]):
        if prior["date"] != ffd["date"]:
            raise ValueError("missing same-date overlap")
        if any(abs(prior[k] - ffd[k]) > 1e-8 for k in FIELDS[:4]):
            raise ValueError("overlap price basis mismatch")
        if abs(prior["amount"] - ffd["amount"]) > 1.0:
            raise ValueError("overlap amount units mismatch")
        if abs(prior["volume"] - ffd["volume"]) > 50.0:
            raise ValueError("overlap volume units mismatch")
    return (old[:-OVERLAP] + incoming)[-KEEP:]


def stage(security, rows, cutoff):
    # First pilot only assesses current S2; prior-stage state is not inferred.
    latest = rows[-1]
    if security["risk"] != "eligible" or latest["volume"] <= 0 or latest["amount"] <= 0:
        return None
    closes = [r["close"] for r in rows]
    avg = lambda n, back=0: statistics.fmean(closes[-n-back:len(closes)-back])
    ma50, ma150, ma200 = (avg(i) for i in (50, 150, 200))
    slope = [avg(200, i) for i in (0, 5, 10, 20)]
    high, low = max(r["high"] for r in rows[-250:]), min(r["low"] for r in rows[-250:])
    if not (latest["close"] > ma50 > ma150 > ma200 and slope[0] > slope[1] > slope[2] > slope[3]
            and slope[0] >= slope[3] * 1.002 and latest["close"] >= low * 1.25
            and latest["close"] >= high * .75):
        return None
    ret, gap = latest["close"] / closes[-21] - 1, latest["close"] / ma50 - 1
    pos = "S2延伸" if ret > .30 or gap > .15 else "S2位置待核" if ret < 0 else "S2正常"
    return dict(code=security["code"][:6], name=security["name"], asOfDate=cutoff, stage="S2", position=pos,
                reasons=["满足试跑的 S2 均线、均线趋势和近 250 日位置条件"],
                pendingChecks=["复权事件", "VCP、Pivot 和量能", "证券状态及重大事件"])


def validate_seed(securities):
    actual = {key: 0 for key in SECTORS}
    seen = set()
    for sec in securities:
        code = sec["code"]
        if not re.fullmatch(r"\d{6}\.(SH|SZ)", code) or code[:6] in seen:
            raise ValueError("invalid or duplicate symbol")
        if sec["sector"] not in actual or sec["risk"] not in {"eligible", "excluded", "unknown"}:
            raise ValueError("invalid sector or risk metadata")
        if not isinstance(sec["name"], str) or not 0 < len(sec["name"]) <= 40:
            raise ValueError("invalid security name")
        if re.match(r"^\*?ST", sec["name"], re.I) or "退市" in sec["name"]:
            if sec["risk"] == "eligible":
                raise ValueError("risk metadata conflicts with security name")
        actual[sec["sector"]] += 1
        seen.add(code[:6])
    if actual != SECTORS:
        raise ValueError("seed must contain exact frozen four-sector universe")


def run(state, cutoff, budget, calendar, now, *, client_factory=HistoryClient, plan_only=True):
    if cutoff > expected_close(now, calendar) or not is_trading_day(dt.date.fromisoformat(cutoff), calendar):
        raise ValueError("target must be a verified completed trading date")
    base = json.loads((state / "seed.json").read_text())
    if base["schemaVersion"] != 1 or base["adjustment"] != "qfq" or base["volumeUnit"] != "share" or base["amountUnit"] != "CNY":
        raise ValueError("unsupported seed provenance / units")
    if not (base.get("provenance") and base.get("membershipDate") and base["membershipDate"] <= cutoff):
        raise ValueError("missing seed provenance or point-in-time membership date")
    permit_older_missing_amount = base.get("olderAmountsUnavailable") is True
    history_dir = state / "histories"
    histories = base["histories"]
    # This command only advances its persistent cache; historical replay must
    # use a separate reviewed immutable seed, not roll back active state.
    for path in history_dir.glob("*.json"):
        if json.loads(path.read_text())[-1]["date"] > cutoff:
            raise ValueError("private history already advanced beyond target")
    securities = base["securities"]
    validate_seed(securities)
    plans, missing, candidates, cached = [], {}, [], 0
    unknown_risk = sum(s["risk"] == "unknown" for s in securities)
    known_excluded = sum(s["risk"] == "excluded" for s in securities)
    sector_counts = {key: 0 for key in SECTORS}
    for security in securities:
        code, sector = security["code"], security["sector"]
        try:
            if security["risk"] == "unknown":
                raise ValueError("security risk state unknown; not screened or counted valid")
            active = history_dir / f"{code}.json"
            rows = valid_rows(json.loads(active.read_text()) if active.exists() else histories[code],
                              permit_older_missing_amount=permit_older_missing_amount)
            prior = rows[-1]["date"]
            if prior > cutoff:
                raise ValueError("history is ahead of target; refuse rollback")
            # Reject missing dates against independently verified calendar years.
            valid_rows(rows, days_between(rows[0]["date"], prior, calendar),
                       permit_older_missing_amount=permit_older_missing_amount)
            overlap_start = rows[-OVERLAP]["date"]
            expected = days_between(overlap_start, cutoff, calendar)
            if not (OVERLAP <= len(expected) <= OVERLAP + 5) or (dt.date.fromisoformat(cutoff)-dt.date.fromisoformat(overlap_start)).days > 14:
                raise ValueError("gap exceeds incremental limit")
            if prior == cutoff:
                sector_counts[sector] += 1
                cached += 1
                c = stage(security, rows, cutoff)
                if c:
                    candidates.append(c)
            else:
                max_points = ((dt.date.fromisoformat(cutoff) - dt.date.fromisoformat(overlap_start)).days + 1) * len(FIELDS)
                plans.append((security, rows, expected, max_points))
        except (ValueError, KeyError, TypeError, IndexError) as exc:
            missing[code] = str(exc)
    planned = sum(item[3] for item in plans)
    potential = {sector: sector_counts[sector]+sum(s["sector"] == sector for s, *_ in plans) for sector in SECTORS}
    gate_possible = all(potential[k] * 100 >= SECTORS[k] * 95 for k in SECTORS)
    j = dict(asOfDate=cutoff, plannedRequests=len(plans), worstCasePoints=planned,
             possiblePerSector=potential, canReachCoverageGate=gate_possible,
             pointCap=budget, cachedCurrent=cached, unusableAtPreflight=len(missing),
             riskUnknown=unknown_risk, knownExcluded=known_excluded)
    if plan_only:
        return dict(j, status="plan_only", fitsCap=planned <= budget)
    if not gate_possible:
        raise ValueError("seed cannot meet 95% coverage in every sector; no requests issued")
    if planned > budget:
        raise ValueError(f"planned upper bound {planned} exceeds cap {budget}; no requests issued")
    ledger_dir = state/"receipts"
    if (state / "billing-hold.json").exists():
        raise ValueError("private billing hold requires reconciliation; no new requests issued")
    for path in ledger_dir.glob("*.json"):
        if path.name.endswith(".response.json"):
            continue
        stored_state = json.loads(path.read_text()).get("state")
        if stored_state not in {"completed", "reconciled"}:
            raise ValueError("private ledger has an unreconciled attempt; no new requests issued")
    client = client_factory(budget, receipt_dir=ledger_dir) if plans else None
    history_dir.mkdir(mode=0o700, exist_ok=True)
    reported = 0
    unknown_charge = 0
    abnormal_charge = False
    for security, rows, expected, reservation in plans:
        code, sector = security["code"], security["sector"]
        try:
            incoming, envelope = client.history(code, expected[0], cutoff, expected_dates=expected,
                                                fields=FIELDS, reuse_completed=True)
            if not envelope.get("_ledgerReused"):
                points = envelope.get("quota_used")
                if isinstance(points, (int, float)) and not isinstance(points, bool) and math.isfinite(points) and points >= 0:
                    reported += points
                    if points > reservation:
                        abnormal_charge = True
                else:
                    unknown_charge += 1
                    abnormal_charge = True
                if abnormal_charge:
                    write(state / "billing-hold.json", dict(asOfDate=cutoff, code=code,
                          reason="FFD reported no valid charge or exceeded this request reservation"))
                    missing[code] = "FFD billing receipt requires reconciliation"
                    break
            current = reconcile(rows, incoming)
            # Commit safely after each reconciled request so a crash doesn't repurchase it.
            write(history_dir / f"{code}.json", current)
            sector_counts[sector] += 1
            c = stage(security, current, cutoff)
            if c:
                candidates.append(c)
        except (ValueError, KeyError, TypeError, IndexError) as exc:
            missing[code] = str(exc)
            # Transport uncertainty or unexplained provider errors halt the rest.
            if client.halted:
                break
    valid = sum(sector_counts.values())
    sufficient = all(sector_counts[k] * 100 >= SECTORS[k] * 95 for k in SECTORS)
    receipt = dict(j, status="candidate_ready" if sufficient and not (abnormal_charge or client and client.halted) else "partial",
                   valid=valid, expected=sum(SECTORS.values()), sectorValid=sector_counts,
                   reservedPoints=client.reserved if client else 0,
                   reportedSuccessPoints=reported, successfulRequestsWithUnknownCharge=unknown_charge,
                   failedOrOmitted=missing, stopUncertain=bool(abnormal_charge or client and client.halted))
    write(state / f"run-{cutoff}.json", receipt)
    # No OHLCV, volumes, amount, percentages or per-stock receipt fields in this output.
    if sufficient and not (abnormal_charge or client and client.halted):
        payload = dict(schemaVersion=1, mode="derived-pilot",
                       runStatus="success", barStatus="completed",
                       asOfDate=cutoff, candidateCount=len(candidates),
                       candidates=sorted(candidates, key=lambda x: x["code"]),
                       source="FFD 增量 + 既有历史（四板块试点）",
                       universe=dict(scope="四板块收盘试点（非全市场）", scopeId="four-sector-close-v1",
                                     sectors=[dict(name=k, valid=sector_counts[k], total=SECTORS[k]) for k in SECTORS], valid=valid, riskUnknown=unknown_risk, knownExcluded=known_excluded,
                                     total=sum(SECTORS.values()), coveragePct=round(valid * 100 / sum(SECTORS.values()), 2)),
                       limitations=["只筛当前 S2；不生成买卖信号", "复权事件未独立核实；全部待核",
                                    f"仅覆盖已验证的 {valid}/{sum(SECTORS.values())} 只；没有入围不代表未覆盖股票不符合"])
        write(state / f"derived-{cutoff}.json", payload)
    return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--state", required=True, type=Path)
    p.add_argument("--as-of", required=True)
    p.add_argument("--max-points", required=True, type=int)
    p.add_argument("--history-calendar", type=Path,
                   help="Private, independently verified exchange calendar for earlier seed years")
    flags = p.add_mutually_exclusive_group()
    flags.add_argument("--plan-only", action="store_true", help="Default: no paid calls or output")
    flags.add_argument("--execute", action="store_true", help="Explicitly enable paid requests")
    a = p.parse_args()
    if a.max_points < 1:
        p.error("--max-points must be positive")
    # Reject state under the repo: private seeds and charge receipts must never
    # be picked up by Git or website deployment.
    state = a.state.resolve(strict=True)
    if state == Path(__file__).resolve().parent or Path(__file__).resolve().parent in state.parents:
        p.error("private state must live outside the repository")
    if state.stat().st_mode & 0o077:
        p.error("private state directory must have mode 0700")
    import os
    os.umask(0o077)
    now = dt.datetime.now(ZONE)
    calendar = load_calendar(year=now.year)
    if a.history_calendar:
        extra = load_calendar(path=a.history_calendar)
        for year, data in extra["years"].items():
            if year in calendar["years"] and calendar["years"][year]["closures"] != data["closures"]:
                p.error(f"historical calendar conflicts with published year {year}")
            calendar["years"].setdefault(year, data)
    with (state / "m2-run.lock").open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        r = run(state, a.as_of, a.max_points, calendar, now, plan_only=not a.execute)
    print(json.dumps(dict(r, failedOrOmitted=len(r.get("failedOrOmitted", {}))), ensure_ascii=False))
    if r["status"] == "partial" or r.get("fitsCap") is False or r.get("canReachCoverageGate") is False:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
