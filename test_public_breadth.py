import unittest
from unittest.mock import patch
from refresh_public_breadth import code,source_frame,preview,require_closed_quote

class PublicSourceTests(unittest.TestCase):
    def test_same_date_intraday_quote_cannot_be_used_as_close(self):
        require_closed_quote('2026-11-04T15:00:00+08:00','2026-11-04')
        for stamp in ['2026-11-04T14:59:59+08:00','2026-11-03T16:15:00+08:00','2026-11-04T16:15:00']:
            with self.assertRaises(ValueError):require_closed_quote(stamp,'2026-11-04')
    def test_float_codes_preserve_leading_zeroes(self):
        self.assertEqual(code(333.0),'000333')
        self.assertEqual(code('688825'),'688825')
        for bad in ['nan',123.5,-1,1000000]:
            with self.assertRaises(ValueError):code(bad)

    def test_actual_observation_date_beats_requested_range(self):
        p=dict(dates=['2026-11-03'],industries=[str(i) for i in range(50)],data=[[0,i,50] for i in range(50)],end_date='2026-11-04')
        self.assertEqual(source_frame(p)[2],'2026-11-03')
        p['data'][0][2]=101
        with self.assertRaises(ValueError):source_frame(p)

    def test_preview_never_averages_industries_into_market_or_fills_ma50(self):
        b=dict(dates=['2026-11-04'],industries=[str(i) for i in range(50)],data=[[0,i,90] for i in range(50)])
        q=dict(updatedAt='2026-11-04T16:15:00+08:00',quotes={str(i):dict(price=10,changePct=1 if i<3000 else -1) for i in range(4000)})
        def fake(url,**kwargs):return q if 'quotes' in url else b
        with patch('refresh_public_breadth.fetch',side_effect=fake):result=preview()
        self.assertEqual(result['participation']['upPct'],75)
        self.assertIsNone(result['market'][-1]['ma20']['pct'])
        self.assertIsNone(result['market'][-1]['ma50']['pct'])
        self.assertIsNone(result['rows'][0]['series'][0]['ma20']['valid'])
        self.assertEqual(result['rows'][0]['series'][0]['ma20']['pct'],90)

if __name__=='__main__':unittest.main()
