import datetime as dt
import unittest

from market_breadth import calculate, summarize


class BreadthTests(unittest.TestCase):
    def test_equal_ma_is_not_above_and_missing_is_not_zero(self):
        data = summarize([
            dict(close=10, pct=0, ma20=10, ma50=None),
            dict(close=11, pct=2, ma20=10, ma50=10),
        ])
        self.assertEqual(data['ma20'], dict(pct=50.0, above=1, valid=2))
        self.assertEqual(data['ma50'], dict(pct=100.0, above=1, valid=1))
        self.assertEqual((data['up'], data['down'], data['flat']), (1, 0, 1))
        self.assertIsNone(summarize([])['ma20']['pct'])

    def fixture(self):
        dates = [(dt.date(2026, 1, 1)+dt.timedelta(days=i)).isoformat() for i in range(100)]
        stocks = [dict(secid=str(i), code=str(i), industry='test') for i in range(100)]
        history = {s['secid']: [dict(date=d, close=10+i, volume=10, pct=1) for i,d in enumerate(dates)] for s in stocks}
        return stocks, history, dates[-1]

    def test_full_history_and_no_lookahead(self):
        stocks, history, end = self.fixture()
        result = calculate(stocks, history, end)
        self.assertEqual(len(result['dates']), 30)
        self.assertEqual(result['market'][-1]['ma50']['pct'], 100)
        before = result['market'][-2]
        history['0'][-1]['close'] = 1
        changed = calculate(stocks, history, end)
        self.assertEqual(changed['market'][-2], before)
        self.assertEqual(changed['market'][-1]['ma20']['pct'], 99)

    def test_missing_latest_bars_rejects_snapshot(self):
        stocks, history, end = self.fixture()
        for i in range(6):
            history[str(i)] = history[str(i)][:-1]
        with self.assertRaisesRegex(ValueError, 'coverage'):
            calculate(stocks, history, end)

    def test_zero_volume_and_short_history_denominators(self):
        stocks, history, end = self.fixture()
        history['0'][-1]['volume'] = 0
        history['1'] = history['1'][-10:]
        result = calculate(stocks, history, end)
        self.assertEqual(result['market'][-1]['n'], 99)
        self.assertEqual(result['market'][-1]['ma20']['valid'], 98)

    def test_empty_source_does_not_overwrite(self):
        with self.assertRaisesRegex(ValueError, 'No valid'):
            calculate([], {}, '2026-11-03')


if __name__ == '__main__':
    unittest.main()
