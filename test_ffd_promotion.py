import copy
import datetime as dt
import unittest
from test_daily_breadth import snapshot
from daily_breadth import validate_snapshot
from ffd_promotion import FFD_SCOPE, promote_candidate, require_publishable, allow_verified_original_source_rollback
from trading_calendar import load_calendar, is_trading_day


def candidate():
    d=snapshot('2026-11-12')
    first=dt.date(2026,8,14)
    cal=load_calendar()
    dates=[(first+dt.timedelta(days=i)).isoformat() for i in range(91) if is_trading_day(first+dt.timedelta(days=i),cal)]
    stocks=[dict(code=f'{i:06d}',secid=f'0.{i:06d}',close=10,industry='test') for i in range(5000)]
    manifest=[dict(code=s['code'],provider='FFD',firstDate=dates[0],lastDate=d['asOf'],bars=len(dates),sha256='a'*64) for s in stocks]
    d.update(scopeVersion=FFD_SCOPE, candidateOnly=True, publicationApproved=False, historyCount=5000,
             source='FFD整段前复权',method='未独立重建除权因子', providerCounts={'FFD':5000},
             verification=dict(ffdCalendarExpectedDates=dates,ffdExperimental=True,ffdCorporateActionsIndependentlyReconciled=False))
    d['dailyHistory'].update(stockCount=5000,sourceStocks=stocks,validHistories=5000,manifest=manifest)
    return d


class PromotionTests(unittest.TestCase):
    def test_explicit_offline_promotion_keeps_original(self):
        d=candidate()
        with self.assertRaises(ValueError): promote_candidate(d,d['asOf'])
        with self.assertRaises(ValueError): require_publishable(d)
        result=promote_candidate(d,d['asOf'],approved=True)
        require_publishable(result)
        self.assertTrue(d['candidateOnly'])
        self.assertNotIn('candidateOnly',result)
        self.assertEqual(result['scopeVersion'],FFD_SCOPE)

    def test_original_gates_apply_to_new_scope(self):
        changes=[lambda d:d.update(coveragePct=94),lambda d:d['market'][-1]['ma50'].update(valid=1),
                 lambda d:d['benchmarks'].pop(),lambda d:d['benchmarks'][0].update(historyCount=69),
                 lambda d:d['benchmarks'][0].update(asOf='2026-11-11'),
                 lambda d:d['dailyHistory'].update(adjustment='raw')]
        for change in changes:
            d=candidate();change(d)
            with self.assertRaises(ValueError): validate_snapshot(d,'2026-11-12')

    def test_provenance_fail_closed(self):
        changes=[lambda d:d['verification']['ffdCalendarExpectedDates'].pop(),
                 lambda d:d['dailyHistory']['manifest'][0].update(bars=58),
                 lambda d:d['dailyHistory']['manifest'][0].update(sha256='fake'),
                 lambda d:d['dailyHistory']['manifest'][0].update(lastDate='2026-11-11'),
                 lambda d:d['providerCounts'].update(FFD=4999),
                 lambda d:d['verification'].update(ffdCorporateActionsIndependentlyReconciled=True),
                 lambda d:d['dailyHistory'].update(stockCount=4999)]
        for change in changes:
            d=candidate();change(d)
            with self.assertRaises(ValueError): validate_snapshot(d,'2026-11-12')

    def test_only_verified_original_source_rollback_is_automatic(self):
        before = promote_candidate(candidate(), '2026-11-12', approved=True)
        current = snapshot('2026-11-13')
        self.assertTrue(allow_verified_original_source_rollback(before,current))
        self.assertFalse(allow_verified_original_source_rollback(current,before))
        self.assertFalse(allow_verified_original_source_rollback({'scopeVersion':'unknown'},current))
        self.assertFalse(allow_verified_original_source_rollback(before,{'scopeVersion':'unknown'}))
        for change in (lambda d:d.update(coveragePct=94), lambda d:d['benchmarks'].pop(),
                       lambda d:d['benchmarks'][0].update(historyCount=69),
                       lambda d:d.update(providerCounts={'FFD':1})):
            invalid=copy.deepcopy(current);change(invalid)
            with self.assertRaises(ValueError): allow_verified_original_source_rollback(before,invalid)
        with self.assertRaises(ValueError): allow_verified_original_source_rollback(before,snapshot('2026-11-11'))

    def test_cannot_publish_unapproved_ffd_without_candidate_flag(self):
        d=candidate();d.pop('candidateOnly');d.pop('publicationApproved')
        with self.assertRaises(ValueError): require_publishable(d)

if __name__=='__main__':unittest.main()
