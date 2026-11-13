import copy
import unittest
from sector_observation import build_sector_observation


def fixtures():
 stocks=[dict(code=f'{i:06d}',secid=f'0.{i:06d}',industry='A' if i<20 else 'B') for i in range(100)]
 base=dict(asOf='2026-11-12',universeCount=100,dailyHistory={'sourceStocks':stocks})
 records=[dict(code=s['code'],latest=10,changeRatio=2.5 if i%2 else -1.5,volume=0 if i==0 else 100,sourceTime='2026-11-13T12:20:00+08:00') for i,s in enumerate(stocks)]
 return base,records
class SectorTests(unittest.TestCase):
 def build(self,b,r):return build_sector_observation(b,r,day='2026-11-13')
 def test_native_percent_and_zero_volume(self):
  b,r=fixtures();d=self.build(b,r)
  self.assertEqual(d['market']['meanChangePct'],.5)
  self.assertEqual(d['market']['zeroVolumeCount'],1)
  self.assertEqual(d['market']['upPct'],50)
  self.assertFalse(d['exact1130Snapshot']);self.assertEqual(d['industries'][0]['top3'][0]['changeRatio'],2.5)
 def test_global_95_guard_and_original_denominator(self):
  b,r=fixtures();self.assertFalse(self.build(b,r[:94])['publishable'])
  self.assertTrue(self.build(b,r[:95])['publishable'])
  b['universeCount']=105;self.assertEqual(self.build(b,r)['market']['expected'],105)
 def test_industry_below_95_stays_null(self):
  b,r=fixtures();d=self.build(b,r[2:]);self.assertTrue(d['publishable'])
  self.assertIsNone(d['industries'][0]['meanChangePct']);self.assertEqual(d['industries'][0]['top3'],[])
 def test_duplicate_whole_run_rejected(self):
  b,r=fixtures()
  with self.assertRaises(ValueError):self.build(b,r+[r[0]])
 def test_missing_date_future_time_nan_unknown_do_not_fill(self):
  b,r=fixtures();r[0]['latest']=float('nan');r[1]['sourceTime']='2026-11-12T12:00:00+08:00';r[2]['sourceTime']='2026-11-13T13:01:00+08:00';r[3]['changeRatio']=None;r[4]['code']='600000.SZ'
  d=self.build(b,r);self.assertEqual(d['market']['valid'],95);self.assertEqual(len(d['invalidRecords']),5)
 def test_exact_afternoon_boundary_excluded(self):
  b,r=fixtures();r[0]['sourceTime']='2026-11-13T13:00:00+08:00'
  self.assertEqual(self.build(b,r)['market']['valid'],99)
 def test_mixed_time_range_kept(self):
  b,r=fixtures();r[0]['sourceTime']='2026-11-13T12:10:00+08:00'
  d=self.build(b,r);self.assertIn('12:10',d['market']['sourceTimeMin']);self.assertIn('12:20',d['market']['sourceTimeMax'])
if __name__=='__main__':unittest.main()
