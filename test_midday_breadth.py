import copy
import datetime as dt
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import midday_breadth as midday
from market_breadth import ZONE
from test_daily_breadth import snapshot, CALENDAR

DAY='2026-11-12'
PRIOR='2026-11-11'
NOW=dt.datetime(2026,11,12,12,0,tzinfo=ZONE)
STOCK=dict(code='600000',secid='1.600000',industry='银行')


def response(today=False):
    rows=[]
    date=dt.date(2026,8,20)
    while date<=dt.date.fromisoformat(PRIOR):
        if date.weekday()<5: rows.append([date.isoformat(),'10','10','10','10','100'])
        date+=dt.timedelta(days=1)
    if today: rows.append([DAY,'11','11','11','11','100'])
    qt=['']*33
    for i,v in {2:'600000',3:'11',4:'10',6:'100',30:'20261112115900',32:'10'}.items():qt[i]=v
    return dict(code=0,data={'sh600000':dict(qfqday=rows,qt={'sh600000':qt})})


def candidate():
    m=dict(n=5000,up=5000,down=0,flat=0,upPct=100,ma20=dict(valid=5000,above=3000,pct=60),ma50=dict(valid=5000,above=2500,pct=50))
    return dict(schemaVersion=1,scopeVersion=midday.MIDDAY_VERSION,session='midday',barStatus='intraday',
        asOf=DAY,observedAt=DAY+'T11:59:00+08:00',generatedAt=DAY+'T12:10:00+08:00',
        previousCloseDate=PRIOR,membershipDate=PRIOR,availableMetrics=['ma20','ma50'],universeCount=5000,
        latestHistoryCount=5000,coveragePct=100,market=m,rows=[dict(industry=str(i),ma20=m['ma20'],ma50=m['ma50']) for i in range(50)])


class MiddayTests(unittest.TestCase):
    def test_dynamic_ma_uses_19_49_prior_closes_not_today_k(self):
        for today in (False,True):
            sample,manifest=midday.extract_sample(response(today),STOCK,dict(price=11,changePct=10),DAY,PRIOR,NOW)
            self.assertAlmostEqual(sample['ma20'],10.05)
            self.assertAlmostEqual(sample['ma50'],10.02)
            self.assertEqual(manifest['historyLastDate'],PRIOR)

    def test_wrong_quote_identity_time_price_and_adjustment_rejected(self):
        cases=[(2,'000001'),(3,'11.01'),(4,'9.9'),(6,'0'),(30,'20261111115900'),(30,'20261112112959'),(30,'20261112130000'),(30,'20261112123000')]
        for idx,value in cases:
            p=response();p['data']['sh600000']['qt']['sh600000'][idx]=value
            with self.subTest(idx=idx,value=value),self.assertRaises(ValueError):
                midday.extract_sample(p,STOCK,dict(price=11,changePct=10),DAY,PRIOR,NOW)
        p=response();p['data']['sh600000']['day']=p['data']['sh600000'].pop('qfqday')
        with self.assertRaises(ValueError):midday.extract_sample(p,STOCK,dict(price=11,changePct=10),DAY,PRIOR,NOW)

    def test_stale_history_and_partial_history_are_not_imputed(self):
        p=response();p['data']['sh600000']['qfqday'].pop()
        with self.assertRaises(ValueError):midday.extract_sample(p,STOCK,dict(price=11,changePct=10),DAY,PRIOR,NOW)
        p=response();p['data']['sh600000']['qfqday']=p['data']['sh600000']['qfqday'][-25:]
        m,_=midday.extract_sample(p,STOCK,dict(price=11,changePct=10),DAY,PRIOR,NOW)
        self.assertIsNone(m['ma50']);self.assertIsNotNone(m['ma20'])

    def test_wrong_session_low_coverage_and_bad_denominator_rejected(self):
        midday.validate_midday(candidate(),DAY)
        for change in [lambda d:d.update(barStatus='completed'),lambda d:d.update(session='close'),lambda d:d.update(coveragePct=94),lambda d:d['market']['ma50'].update(pct=55),lambda d:d.update(previousCloseDate=DAY),lambda d:d.update(generatedAt=DAY+'T13:01:00+08:00')]:
            d=candidate();change(d)
            with self.assertRaises(ValueError):midday.validate_midday(d,DAY)

    def test_lunch_windows_exchange_holidays_and_no_close_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'market-trading-calendar.json').write_text(CALENDAR)
            close=root/'market-breadth.json';close.write_text(json.dumps(snapshot(PRIOR)))
            status=root/'market-breadth-status.json';status.write_text('{"close":"preserve"}')
            original=(close.read_bytes(),status.read_bytes())
            with patch('midday_breadth.collect',return_value=candidate()) as collect:
                for date in [NOW.replace(hour=10),NOW.replace(hour=13),NOW.replace(hour=12,minute=55),NOW.replace(day=14),NOW.replace(month=10,day=1)]:
                    self.assertEqual(midday.refresh(root,date,scheduled=True)['status'],'skipped')
                collect.assert_not_called()
                self.assertEqual(midday.refresh(root,NOW,force=True)['status'],'success')
                self.assertTrue(midday.refresh(root,NOW)['alreadyCurrent'])
                self.assertEqual(collect.call_count,1)
            self.assertEqual(original,(close.read_bytes(),status.read_bytes()))
            before=(root/'market-breadth-midday.json').read_bytes()
            with patch('midday_breadth.collect',side_effect=ValueError('stale quote')):
                with self.assertRaises(ValueError):midday.refresh(root,NOW,force=True)
            self.assertEqual(before,(root/'market-breadth-midday.json').read_bytes())
            self.assertEqual(midday.refresh(root,NOW)['status'],'blocked_incremental_unverified')
            restored=json.loads((root/'market-breadth-midday-status.json').read_text())
            self.assertEqual(restored['status'],'failed')
            self.assertEqual(restored['requestedDate'],NOW.date().isoformat())
            self.assertEqual(original,(close.read_bytes(),status.read_bytes()))
            self.assertFalse((root/'output'/'breadth-history').exists())
            self.assertFalse((root/'output'/'qfq-breadth-cache').exists())

    def test_source_wrong_date_and_coverage_rejected(self):
        quotes=dict(updatedAt=DAY+'T11:59:00+08:00',quotes={f'{i:06d}.SZ':dict(price=10,changePct=0,turnoverAmount=1) for i in range(5000)})
        overview=dict(markets=[dict(market=k,stockCount=2500,updatedAt=quotes['updatedAt']) for k in ('sse','szse')])
        self.assertEqual(midday.verified_sources(quotes,overview,DAY,NOW)[1],5000)
        for bad in ['2026-11-11T11:59:00+08:00',DAY+'T15:00:00+08:00']:
            q=copy.deepcopy(quotes);q['updatedAt']=bad
            with self.assertRaises(ValueError):midday.verified_sources(q,overview,DAY,NOW)
        quotes['quotes']=dict(list(quotes['quotes'].items())[:4700])
        with self.assertRaises(ValueError):midday.verified_sources(quotes,overview,DAY,NOW)

    def test_shadow_output_and_reused_stale_membership_are_rejected(self):
        for path in [midday.ROOT/'market-breadth.json', midday.ROOT/'market-breadth-status.json', midday.ROOT/'output/breadth-history/x.json', midday.ROOT/'output/qfq-breadth-cache/x.json']:
            with self.assertRaises(ValueError): midday.safe_shadow_output(path)
        d=candidate();d['previousCloseDate']=d['membershipDate']='2026-11-10'
        with self.assertRaisesRegex(ValueError, 'preceding'):midday.validate_midday(d,DAY)

    def test_afternoon_crossover_rejects_batch(self):
        with self.assertRaisesRegex(ValueError,'afternoon'):
            midday.build_snapshot({},[],{},[],{},5000,NOW,NOW.replace(hour=13))

if __name__=='__main__':unittest.main()
