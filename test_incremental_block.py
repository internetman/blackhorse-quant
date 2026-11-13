import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import cloud_breadth as cloud
import daily_breadth as daily
import midday_breadth as midday
from test_daily_breadth import snapshot,CALENDAR
from test_midday_breadth import NOW

class BlockTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  (self.root/'market-trading-calendar.json').write_text(CALENDAR)
  self.now=NOW.replace(hour=16,minute=40)
 def tearDown(self):self.temp.cleanup()
 def test_cloud_schedule_push_manual_without_force_never_collect_or_publish(self):
  before={p.name:p.read_bytes() for p in self.root.iterdir()}
  with patch.object(daily,'refresh',side_effect=AssertionError('collector')),patch.object(midday,'refresh',side_effect=AssertionError('collector')),patch.object(cloud,'publish_session',side_effect=AssertionError('publish')):
   for event,cron,force in [('schedule','40 8,9,10 * * 1-5',False),('push','',False),('workflow_dispatch','',False),('schedule','40 8,9,10 * * 1-5',True),('push','',True)]:
    result=cloud.run(self.root,self.now,event,cron,requested='close',force=force)
    self.assertEqual(result['status'],'blocked_incremental_unverified')
  self.assertEqual(before,{p.name:p.read_bytes() for p in self.root.iterdir()})
 def test_current_pair_no_calls(self):
  d=snapshot(self.now.date().isoformat());(self.root/'market-breadth.json').write_text(json.dumps(d))
  (self.root/'market-breadth-status.json').write_text(json.dumps(dict(status='success',asOf=d['asOf'],lastCollectedAt=d['generatedAt'])))
  with patch.object(daily,'refresh',side_effect=AssertionError('collector')):
   self.assertEqual(cloud.run(self.root,self.now,'push')['status'],'already_current')
 def test_local_missing_data_blocks(self):
  with patch('complete_breadth.collect',side_effect=AssertionError('collector')),patch.object(midday,'collect',side_effect=AssertionError('collector')):
   self.assertEqual(daily.refresh(self.root,self.now,scheduled=True)['status'],'blocked_incremental_unverified')
   self.assertEqual(midday.refresh(self.root,NOW,scheduled=True)['status'],'blocked_incremental_unverified')
 def test_manual_force_only_enters_bootstrap(self):
  with patch.object(cloud,'check_repository',side_effect=RuntimeError('bootstrap gate')):
   with self.assertRaisesRegex(RuntimeError,'bootstrap gate'):
    cloud.run(self.root,self.now,'workflow_dispatch',requested='close',force=True)
 def test_calendar_still_prevents_weekend(self):
  self.assertEqual(cloud.run(self.root,NOW.replace(day=14),'push')['status'],'skipped')
if __name__=='__main__':unittest.main()
