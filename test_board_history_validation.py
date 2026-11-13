import copy
import datetime as dt
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo
from board_history_validation import completed_dates,parse_board_history,validate_rows
import server

class BoardTests(unittest.TestCase):
 def setUp(self):
  self.now=dt.datetime(2026,11,13,12,tzinfo=ZoneInfo('Asia/Shanghai'))
  self.days=completed_dates(now=self.now)
  self.payload=dict(rc=0,data=dict(code='BK1300',market=90,klines=[f'{d},10,11,12,9,100,100000000,3,2,1,4' for d in self.days]))
 def test_noon_cutoff_excludes_intraday(self):
  self.assertEqual(self.days[-1],'2026-11-12')
  self.assertEqual(len(parse_board_history(self.payload,'BK1300',self.days)),10)
  self.payload['data']['klines'].append('2026-11-13,10,11,12,9,100,100000000,3,2,1,4')
  with self.assertRaises(ValueError):parse_board_history(self.payload,'BK1300',self.days)
 def test_wrong_identity_missing_day_duplicate_nonfinite(self):
  for action in [lambda p:p['data'].update(code='BK9999'),lambda p:p['data'].pop('market'),lambda p:p['data']['klines'].pop(2),lambda p:p['data']['klines'].append(p['data']['klines'][-1]),lambda p:p['data']['klines'].__setitem__(2,p['data']['klines'][2].replace(',11,',',nan,'))]:
   p=copy.deepcopy(self.payload);action(p)
   with self.assertRaises(ValueError):parse_board_history(p,'BK1300',self.days)
 def test_close_and_holiday_calendar(self):
  self.assertEqual(completed_dates(now=self.now.replace(hour=16))[-1],'2026-11-13')
  self.assertEqual(completed_dates(now=dt.datetime(2026,10,7,18,tzinfo=self.now.tzinfo))[-1],'2026-09-30')
 def test_server_requests_explicit_completed_end(self):
  with patch('board_history_validation.completed_dates',return_value=self.days),patch.object(server,'fetch_eastmoney_json',return_value=self.payload) as fetch:
   server.get_sector_klines('BK1300')
  self.assertIn('end=20261112',fetch.call_args.args[0])
 def test_unverified_cache_never_becomes_valid_history(self):
  with patch.dict(server._trend_cache,{'BK1300':{'rows':[],'ts':0}},clear=True):
   self.assertFalse(server.apply_trend_cache({},'BK1300',1,'cache'))
if __name__=='__main__':unittest.main()
