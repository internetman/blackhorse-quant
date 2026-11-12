import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from complete_breadth import (VERSION, BENCHMARKS, parse_tencent, parse_eastmoney, validate_bars,
                              get_history, stock_universe, build_snapshot)


def dates(count=100):
    date = dt.date(2026, 11, 10)
    result = []
    while len(result) < count:
        if date.weekday() < 5:
            result.append(date.isoformat())
        date -= dt.timedelta(days=1)
    return list(reversed(result))


def fixture():
    days = dates()
    history = [dict(date=d, close=10+i/100, volume=100) for i,d in enumerate(days)]
    stocks = [dict(code=f'{i:06d}',secid=f'0.{i:06d}',industry=f'Industry{i%2}',close=history[-1]['close']) for i in range(100)]
    histories = {s['code']:(copy.deepcopy(history),'Tencent','fixture-digest') for s in stocks}
    base = dict(asOf=days[-1], dates=days[-30:], universeCount=100, latestHistoryCount=100,
                universeLabel='沪深A股',rows=[dict(industry=f'Industry{i}') for i in range(2)],verification={})
    benchmarks = [dict(secid=s,name=n,asOf=days[-1],close=100,ma50=99,ma50Slope20=1,historyCount=100) for s,n in BENCHMARKS]
    return base,stocks,histories,benchmarks


class CompleteTests(unittest.TestCase):
    def test_stock_unadjusted_bars_cannot_substitute_for_qfq(self):
        raw = [['2026-11-10','10','10','10','10','100']]
        with self.assertRaisesRegex(ValueError,'adjusted'):
            parse_tencent(dict(code=0,data={'sz000001':dict(day=raw)}),'sz000001','2026-11-10')
        self.assertEqual(parse_tencent(dict(code=0,data={'sh000001':dict(day=raw)}),'sh000001','2026-11-10',True)[0]['close'],10)

    def test_rejects_wrong_identity_duplicate_future_stale_and_invalid_prices(self):
        good = dict(date='2026-11-10',close=10,volume=1)
        for rows in [[good,good],[dict(good,date='2026-11-11')],[dict(good,date='2026-11-09')],[dict(good,close=0)]]:
            with self.assertRaises(ValueError):validate_bars(rows,'2026-11-10')
        with self.assertRaisesRegex(ValueError,'market'):
            parse_eastmoney(dict(data=dict(code='000001',market=1,klines=['2026-11-10,10,10,10,10,100'])),'000001','2026-11-10',0)
        with self.assertRaisesRegex(ValueError,'identity'):
            parse_tencent(dict(code=0,data={'sh000001':{}}),'sz000001','2026-11-10')

    def test_corrupt_cache_refetches_and_retains_verifiable_raw_response(self):
        response=dict(code=0,data={'sz000001':dict(qfqday=[['2026-11-10','10','10','10','10','100']])})
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); (p/'0.000001.json').write_text('{broken')
            with patch('complete_breadth.fetch_history',return_value=response) as fetch:
                rows,provider,digest=get_history(dict(secid='0.000001',code='000001'),'2026-11-10',p)
                self.assertEqual(fetch.call_count,1)
            saved=json.loads((p/'0.000001.json').read_text())
            self.assertEqual(saved['effectiveKey'],'qfqday')
            self.assertEqual(saved['adjustment'],'qfq')
            self.assertEqual(digest,hashlib.sha256(json.dumps(response,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())
            with patch('complete_breadth.fetch_history') as fetch:
                get_history(dict(secid='0.000001',code='000001'),'2026-11-10',p)
                fetch.assert_not_called()
            saved['response']['code']=1;(p/'0.000001.json').write_text(json.dumps(saved))
            with patch('complete_breadth.fetch_history',return_value=response) as fetch:
                get_history(dict(secid='0.000001',code='000001'),'2026-11-10',p)
                self.assertEqual(fetch.call_count,1)

    def test_cold_universe_and_full_snapshot_reuse_need_no_local_quotes(self):
        base=dict(asOf='2026-11-10',latestHistoryCount=2,rows=[dict(industry='test')])
        response=dict(date='2026-11-10',industry='test',data=[dict(stock_code=i,date='2026-11-10',industry='test',close_price=10,change_percent=1) for i in [1,600000]])
        quotes=dict(updatedAt='2026-11-10T16:15:00+08:00',quotes={'000001.SZ':dict(price=10,changePct=1),'600000.SH':dict(price=10,changePct=1)})
        with tempfile.TemporaryDirectory() as d,patch('complete_breadth.fetch',side_effect=lambda url,**kw: quotes if 'quotes' in url else response) as fetch:
            stocks=stock_universe(base,Path(d)); self.assertEqual(len(stocks),2);self.assertEqual(fetch.call_count,2)
        base.update(latestHistoryCount=1,dailyHistory=dict(stockCount=2,sourceStocks=stocks))
        with tempfile.TemporaryDirectory() as d,patch('complete_breadth.fetch') as fetch:
            self.assertEqual(len(stock_universe(base,Path(d))),2);fetch.assert_not_called()

    def test_uniform_ma20_ma50_math_and_benchmark_provenance(self):
        base,stocks,histories,indices=fixture()
        result=build_snapshot(base,stocks,histories,indices,[])
        self.assertEqual(result['scopeVersion'],VERSION)
        self.assertEqual(result['market'][-1]['ma50'],dict(pct=100,above=100,valid=100))
        self.assertEqual(result['market'][-1]['ma20'],dict(pct=100,above=100,valid=100))
        self.assertEqual(len(result['dailyHistory']['sourceStocks']),100)
        self.assertEqual(result['benchmarks'],indices)

    def test_strict_above_ma_and_zero_volume(self):
        base,stocks,histories,indices=fixture()
        for s in stocks:s['close']=10
        for rows,_,_ in histories.values():
            for row in rows:row['close']=10
        result=build_snapshot(base,stocks,histories,indices,[])
        self.assertEqual(result['market'][-1]['ma50']['above'],0)
        histories[stocks[0]['code']][0][-1]['volume']=0
        self.assertEqual(build_snapshot(base,stocks,histories,indices,[])['market'][-1]['ma50']['valid'],99)

    def test_missing_or_newly_listed_stocks_do_not_become_zero_or_pass(self):
        base,stocks,histories,indices=fixture()
        for stock in stocks[:6]:histories.pop(stock['code'])
        with self.assertRaisesRegex(ValueError,'95%'):build_snapshot(base,stocks,histories,indices,[])
        base,stocks,histories,indices=fixture()
        for stock in stocks[:6]:histories[stock['code']]=(histories[stock['code']][0][-40:],'Tencent','fixture')
        with self.assertRaisesRegex(ValueError,'95%'):build_snapshot(base,stocks,histories,indices,[])

    def test_low_coverage_history_stays_null_and_sector_is_not_filled(self):
        base,stocks,histories,indices=fixture()
        for s in stocks[:4]:histories.pop(s['code'])
        # Both sectors still have96%; one sector now90% while market95% is allowed.
        histories.pop(stocks[4]['code'])
        result=build_snapshot(base,stocks,histories,indices,[])
        self.assertIsNone(result['rows'][0]['series'][-1]['ma50']['pct'])
        self.assertEqual(result['market'][-1]['ma50']['valid'],95)

    def test_price_mismatches_and_missing_duplicate_indices_cannot_pass(self):
        base,stocks,histories,indices=fixture()
        for s in stocks[:2]:s['close']*=2
        with self.assertRaisesRegex(ValueError,'disagree'):build_snapshot(base,stocks,histories,indices,[])
        base,stocks,histories,indices=fixture()
        for bad in [indices[:-1],indices[:-1]+[indices[0]],[dict(r,asOf='2026-11-09') for r in indices]]:
            with self.assertRaisesRegex(ValueError,'benchmark'):build_snapshot(base,stocks,histories,bad,[])

if __name__=='__main__':unittest.main()
