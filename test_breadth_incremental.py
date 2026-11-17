import datetime as dt
import unittest

from breadth_incremental import SCHEMA, canonical_digest, make_plan, stage, trading_dates
from trading_calendar import is_trading_day, load_calendar


class IncrementalBreadth(unittest.TestCase):
    def setUp(self):
        self.cal = load_calendar(year=2026)
        self.base, self.target = '2026-11-12', '2026-11-16'
        day = dt.date(2026,11,12)
        dates = []
        while len(dates) < 60:
            if is_trading_day(day,self.cal):
                dates.insert(0,day.isoformat())
            day -= dt.timedelta(days=1)
        self.codes = [f'600{i:03}' for i in range(20)]
        self.members = dict(schema=SCHEMA,asOf=self.base,source='verified fixture',universeCount=20,
                            stocks={c: ('small' if i==0 else 'large') for i,c in enumerate(self.codes)})
        self.seed = dict(schema=SCHEMA,cutoff=self.base,source='verified fixture',series={})
        self.deltas, self.quotes = {}, {d:{} for d in ('2026-11-13',self.target)}
        for c in self.codes:
            bars = [dict(date=d,close=10+i,volume=500) for i,d in enumerate(dates)]
            self.seed['series'][c] = dict(code=c,cutoff=self.base,provider='FFD',adjustment='qfq',
                                          bars=bars,barSha256=canonical_digest(bars))
            self.deltas[c] = dict(code=c,cutoff=self.target,provider='FFD',adjustment='qfq',
                 requestId='fixture',corporateActions=dict(code=c,state='complete_no_rebase',
                     source='fixture',evidenceId='fixture',verifiedFrom=dates[0],verifiedThrough=self.target),
                 bars=[dict(r) for r in bars[-3:]]+[dict(date=d,close=70+i,volume=700) for i,d in enumerate(self.quotes)])
            for i,d in enumerate(self.quotes):
                self.quotes[d][c] = dict(code=c,asOf=d,provider='sckd',session='completed_close',sourceTime=d+'T16:00:00+08:00',close=70+i)

    def run_stage(self):
        return stage(self.members,self.seed,self.deltas,self.quotes,self.target,self.cal)

    def test_gap_plan_skips_weekend_and_never_pulls_49_bars(self):
        plan = make_plan(self.members,self.seed,self.target,self.cal)
        self.assertEqual(plan['dates'],['2026-11-13','2026-11-16'])
        self.assertEqual(len(plan['requests'][self.codes[0]]['expectedDates']),5)

    def test_aggregate_pass_sector_blank_and_no_raw_data(self):
        del self.deltas[self.codes[0]]
        result, updated = self.run_stage()
        self.assertTrue(result['coveragePass'])
        self.assertFalse(result['publishable'])
        self.assertFalse(result['benchmarkGatePassed'])
        m = result['sessions'][self.target]
        self.assertEqual(m['market']['ma50'],dict(above=19,valid=19,eligible=20,pct=100.,insufficientCoverage=False))
        self.assertIsNone(m['sectors']['small']['ma50']['pct'])
        self.assertNotIn('bars', str(result))
        self.assertEqual(len(updated['series']),19)

    def test_exclude_unsafe_stitches_and_fail_market_gate(self):
        self.deltas[self.codes[0]]['corporateActions']['verifiedThrough'] = self.base
        self.deltas[self.codes[1]]['bars'][0]['close'] = 12.3
        self.deltas[self.codes[2]]['provider'] = 'Eastmoney'
        self.quotes[self.target][self.codes[3]]['session'] = 'midday'
        self.quotes[self.target][self.codes[4]]['close'] = 40
        self.deltas[self.codes[5]]['bars'][-1]['volume'] = 0
        result, updated = self.run_stage()
        self.assertFalse(result['coveragePass'])
        self.assertEqual(result['failureCounts'],{'notVerified':5,'closeMismatch':1})
        self.assertFalse(result['independentCloseGatePassed'])
        self.assertIsNone(result['sessions'][self.target]['market']['ma20']['pct'])
        self.assertEqual(len(updated['series']),14)

    def test_no_shrink_or_invalid_dates(self):
        self.members['universeCount'] = 24
        with self.assertRaisesRegex(ValueError,'fixed coverage'):
            self.run_stage()
        self.members['universeCount'] = 20
        with self.assertRaisesRegex(ValueError,'trading session'):
            make_plan(self.members,self.seed,'2026-11-15',self.cal)

    def test_five_benchmark_gate_and_dated_slopes(self):
        from complete_breadth import BENCHMARKS
        days = []
        d = dt.date.fromisoformat(self.base)
        while len(days)<70:
            if is_trading_day(d,self.cal):
                days.insert(0,d.isoformat())
            d-=dt.timedelta(days=1)
        bars = [dict(date=d,close=i+10,volume=500) for i,d in enumerate(days)]
        more = [dict(date=d,close=i+80,volume=500) for i,d in enumerate(self.quotes)]
        data = {}
        for secid,_ in BENCHMARKS:
            common = dict(secid=secid,adjustment='none',provider='FFD')
            data[secid] = dict(seed=dict(common,bars=bars,barSha256=canonical_digest(bars)),
                               delta=dict(common,bars=bars[-3:]+more,requestId='fixture'))
        result,_ = stage(self.members,self.seed,self.deltas,self.quotes,self.target,self.cal,data)
        self.assertTrue(result['benchmarkGatePassed'])
        for item in result['sessions'][self.target]['benchmarks'].values():
            self.assertTrue(item['aboveMA50'])
            self.assertAlmostEqual(item['ma50Slope20'],100*(56.5/36.5-1),6)
        data.popitem()
        result,_ = stage(self.members,self.seed,self.deltas,self.quotes,self.target,self.cal,data)
        self.assertFalse(result['benchmarkGatePassed'])
        self.assertEqual(result['failureCounts']['benchmarkValidation'],1)
