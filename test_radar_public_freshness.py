import copy
import datetime as dt
import threading
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import server
from board_history_validation import completed_dates


class RadarPublicTests(unittest.TestCase):
    def setUp(self):
        self.stamp = int(server.time.time())
        self.row = dict(f12='BK1616', f14='白银', f2=100, f3=5,
                        f124=self.stamp, f128='盛达资源', f140='000603', f136=10)

    def test_encoded_scope_public_token_and_empty_data_fails_over(self):
        good = dict(rc=0, data=dict(total=1, diff=[self.row]))
        with patch.object(server, 'fetch_json', side_effect=[dict(rc=0, data=None), good]) as fetch:
            rows = server.get_sector_rank(1)
        self.assertEqual(rows[0]['classificationCount'], 1)
        urls = [call.args[0] for call in fetch.call_args_list]
        self.assertIn('push2delay.eastmoney.com', urls[1])
        for call in fetch.call_args_list:
            query = parse_qs(urlsplit(call.args[0]).query)
            self.assertEqual(query['fs'], ['m:90+t:2'])
            self.assertEqual(query['ut'], [server.EASTMONEY_QUOTE_UT])
            self.assertIn('_', query)
            self.assertLessEqual(call.kwargs['timeout'], 1.5)
        self.assertEqual(rows[0]['sourceTime'], server.quote_source_time(self.stamp))

    def test_invalid_rank_never_becomes_ready(self):
        for rows, total in [([self.row, self.row], 2),
                            ([dict(self.row, f3=float('nan'))], 1),
                            ([dict(self.row, f124=self.stamp+3600)], 1),
                            ([self.row], 30)]:
            with self.subTest(rows=rows, total=total):
                with patch.object(server, 'fetch_eastmoney_json', return_value=dict(rc=0, data=dict(total=total, diff=rows))):
                    with self.assertRaises(server.FetchError):
                        server.get_sector_rank(2)

    def test_yesterday_quotes_not_relabelled_current(self):
        row = dict(code='BK1616', pct=5, sourceTime=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(days=1)).isoformat())
        status = server.build_sector_rank_status([row])
        self.assertFalse(status['ready'])
        self.assertEqual(status['reason'], 'stale_source_time')

    def test_leaders_keep_board_identity_and_source_time(self):
        data = dict(rc=0, data=dict(total=1, diff=[dict(self.row, f12='000603')]))
        with patch.object(server, 'fetch_eastmoney_json', return_value=data) as fetch:
            leaders = server.get_sector_leaders('BK1616')
        self.assertEqual(leaders[0]['boardCode'], 'BK1616')
        self.assertEqual(leaders[0]['code'], '000603')
        self.assertIsNotNone(leaders[0]['sourceTime'])
        self.assertNotIn('pe', leaders[0])  # f10 is volume ratio, not PE.
        self.assertEqual(parse_qs(urlsplit(fetch.call_args.args[0]).query)['fs'], ['b:BK1616'])

    def test_all_five_histories_start_concurrently_and_are_completed(self):
        days = completed_dates()
        trend = [dict(date=d, open=10, close=11, high=12, low=9, volume=100,
                      amountYi=1, amplitude=3, pct=2, change=1, turnover=4) for d in days]
        barrier = threading.Barrier(5)
        def history(code, count):
            barrier.wait(timeout=2)
            return copy.deepcopy(trend)
        rows = [dict(code=f'BK{i:04}', pct=5-i, sourceTime=server.quote_source_time(self.stamp),
                     leaderCode='000603', leaderPct=10, classificationCount=496) for i in range(5)]
        with patch.object(server, 'get_sector_rank', return_value=rows), \
             patch.object(server, 'get_market_indices', return_value=[]), \
             patch.object(server, 'get_market_distribution', return_value={}), \
             patch.object(server, 'get_r02_breadth', return_value={}), \
             patch.object(server, 'get_sector_klines', side_effect=history), \
             patch.object(server, 'get_sector_leaders', return_value=[dict(code='000603', pct=10, sourceTime=server.quote_source_time(self.stamp))]), \
             patch.dict(server._trend_cache, {}, clear=True), \
             patch.dict(server._sector_rank_cache, dict(ts=0, rows=[]), clear=True):
            result = server.build_dashboard_payload(force=True)
        self.assertEqual([len(r['trend10']) for r in result['top5']], [10]*5)
        self.assertTrue(all(r['trend10Verified'] for r in result['top5']))
        self.assertTrue(all(r['leaderMatchesConstituents'] for r in result['top5']))
        self.assertTrue(all(r['completedCloseVerified'] for r in result['moduleStatus']['sectorTrends']))
        self.assertEqual(result['moduleStatus']['sectorRank']['sourceTime'], rows[0]['sourceTime'])
        self.assertFalse(result['moduleStatus']['r02Decision']['automaticRecalculation'])
        self.assertEqual(result['warnings'], [])


if __name__ == '__main__':
    unittest.main()
