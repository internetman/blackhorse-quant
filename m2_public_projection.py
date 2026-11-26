"""Generate a review-only projection in memory. Never writes, uploads, or deploys."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import unicodedata
from pathlib import Path

from market_breadth import ZONE
from m2_incremental import SECTORS
from trading_calendar import expected_close, load_calendar

POSITIONS = frozenset(("S2正常", "S2延伸", "S2位置待核"))
SCOPE = "four-sector-close-v1"


def build(run, review, target):
    if dt.date.fromisoformat(target).isoformat() != target:
        raise ValueError("target must be a canonical date")
    total = sum(SECTORS.values())
    counts = run.get("sectorValid")
    if (run.get("status") != "candidate_ready" or run.get("asOfDate") != target or
            run.get("stopUncertain") is not False or run.get("expected") != total or
            not isinstance(counts, dict) or set(counts) != set(SECTORS)):
        raise ValueError("run is not a verified private four-sector candidate result")
    if any(type(counts[k]) is not int or counts[k] > n or counts[k] * 100 < n * 95
           for k, n in SECTORS.items()):
        raise ValueError("four-sector coverage gate not met")
    valid = sum(counts.values())
    if type(run.get("valid")) is not int or run["valid"] != valid:
        raise ValueError("conflicting coverage total")
    u = review.get("universe") or {}
    if (review.get("schemaVersion") != 1 or review.get("mode") != "derived-pilot" or
            review.get("runStatus") != "success" or review.get("barStatus") != "completed" or
            review.get("asOfDate") != target or u.get("scopeId") != SCOPE or
            u.get("valid") != valid or u.get("total") != total or
            u.get("sectors") != [dict(name=k, valid=counts[k], total=n) for k, n in SECTORS.items()]):
        raise ValueError("private preview and run do not agree")
    entries = review.get("candidates")
    count = review.get("candidateCount")
    if not isinstance(entries, list) or type(count) is not int or len(entries) != count or count > valid:
        raise ValueError("candidate list/count mismatch")
    public = []
    seen = set()
    for c in entries:
        if not isinstance(c, dict):
            raise ValueError("candidate must be an object")
        code, name, pos = c.get("code"), c.get("name"), c.get("position")
        if (not isinstance(code, str) or not re.fullmatch(r"[036][0-9]{5}", code) or code in seen or
                c.get("asOfDate") != target or c.get("stage") != "S2" or pos not in POSITIONS or
                not isinstance(name, str) or not name.strip() or len(name) > 40 or
                any(unicodedata.category(x).startswith("C") for x in name)):
            raise ValueError("unknown, invalid, or duplicate review candidate")
        seen.add(code)
        # Rebuild from a small allowlist; never pass through a provider field,
        # numeric quote, raw request, free-text note, signal, or file path.
        public.append(dict(code=code, name=name.strip(), asOfDate=target, stage="S2", position=pos,
                           reasons=["满足四板块试跑的 S2 均线趋势及位置条件"],
                           pendingChecks=["复权事件、形态、量能和重大事件"]))
    return dict(schemaVersion=1, mode="derived-pilot", runStatus="success", barStatus="completed",
                asOfDate=target, candidateCount=count, candidates=public,
                source="经校验的日线增量与历史缓存",
                universe=dict(scopeId=SCOPE, valid=valid, total=total,
                              sectors=[dict(name=k, valid=counts[k], total=n) for k, n in SECTORS.items()]),
                limitations=["只筛四个板块的当前 S2，不是全市场或正式每日名单",
                             "未经人工核实，不构成确认突破或交易信号",
                             f"只覆盖 {valid}/{total} 只，未覆盖标的不作结论"])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--state", required=True, type=Path)
    p.add_argument("--as-of", required=True)
    p.add_argument("--review-scope-confirmed", action="store_true",
                   help="Require the operator to confirm current derived display rights separately from API access.")
    args = p.parse_args()
    now = dt.datetime.now(ZONE)
    if not args.review_scope_confirmed:
        p.error("derived public display rights must be verified; API access alone is not sufficient")
    if args.as_of != expected_close(now, load_calendar(year=now.year)):
        p.error("cannot prepare yesterday's review as current")
    if args.state.is_symlink() or args.state.stat().st_mode & 0o077:
        p.error("state must remain private")
    run, review = (json.loads((args.state/f"{key}-{args.as_of}.json").read_text())
                   for key in ("run","derived"))
    print(json.dumps(build(run, review, args.as_of), ensure_ascii=False))


if __name__ == "__main__":
    main()
