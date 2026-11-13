"""Manual, one-security FFD smoke test. Never writes a published snapshot."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from ffd_history import HistoryClient
from market_breadth import ROOT, ZONE, atomic_json
from trading_calendar import expected_close, load_calendar, is_trading_day


def probe(code, cutoff, max_points=200, *, client=None):
    if cutoff > expected_close():
        raise ValueError('Refusing future or unfinished daily close')
    start = (dt.date.fromisoformat(cutoff)-dt.timedelta(days=90)).isoformat()
    # Existing exchange-calendar asset only; never fetch/guess future holidays.
    calendar = load_calendar()
    first, last = dt.date.fromisoformat(start), dt.date.fromisoformat(cutoff)
    expected_dates = [(first+dt.timedelta(days=i)).isoformat()
                      for i in range((last-first).days+1)
                      if is_trading_day(first+dt.timedelta(days=i), calendar)]
    if not expected_dates or expected_dates[-1] != cutoff:
        raise ValueError('Cutoff is not a verified exchange trading day')
    client = client or HistoryClient(max_points)
    rows, payload = client.history(code, start, cutoff, expected_dates=expected_dates)
    if len(rows) < 50:
        raise ValueError('Fewer than 50 observed daily bars; not MA50 eligible')
    return dict(status='sample_verified_not_production', code=code, asOf=cutoff, start=start,
                generatedAt=dt.datetime.now(ZONE).isoformat(timespec='seconds'),
                source='FFD history', adjustment='qfq', historyCount=len(rows), rows=rows,
                ma50=sum(row['close'] for row in rows[-50:])/50,
                coverage=payload.get('coverage'),
                localVerification=dict(identityMatrixChecked=True, calendarComplete=True,
                                       expectedTradingDays=len(expected_dates),
                                       calendarSources={year:entry.get('source') for year,entry in calendar['years'].items()
                                                        if first.year <= int(year) <= last.year},
                                       sourceCoverageDeclared=bool((payload.get('coverage') or {}).get('complete') is True)),
                adjustmentExecution=payload.get('adjustment_execution'),
                requestId=payload.get('request_id'), customerBilling=payload.get('customer_billing'),
                quotaUsed=payload.get('quota_used'), budgetReserved=client.reserved,
                responseSha256=hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),
                limitations=['One-security sample, not full-market coverage',
                             'Corporate-action factor reconciliation not independently verified',
                             'No production snapshot or cloud schedule changed'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cutoff', required=True)
    parser.add_argument('--code', default='600000.SH')
    parser.add_argument('--max-points', type=int, default=200)
    args=parser.parse_args()
    report=probe(args.code,args.cutoff,args.max_points)
    out=ROOT/'output'/'ffd-probe'/f'{args.cutoff}-{args.code}.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    atomic_json(out,report)
    print(json.dumps({k:report[k] for k in ['status','code','asOf','historyCount','ma50','quotaUsed','budgetReserved']},ensure_ascii=False))

if __name__=='__main__':main()
