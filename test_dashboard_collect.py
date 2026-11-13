import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import dashboard_collect as c
class CollectTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  for name in ['market-trading-calendar.json','market-breadth.json']:(self.root/name).write_bytes((c.ROOT/name).read_bytes())
  self.now=dt.datetime.fromisoformat('2026-11-13T12:00:00+08:00')
 def tearDown(self):self.tmp.cleanup()
 def build(self,**kwargs):return dict(indices=[{'code':'1'}],sectors=[{'code':'A'}],top5=[{'trend10':[{'date':'2026-11-12'}],'leaders10':[{}]}],source={},r02={})
 def test_session_idempotence_and_no_paid_calls(self):
  result=c.collect('midday',root=self.root,now=self.now,builder=self.build)
  self.assertTrue(result['savedObservation']);self.assertEqual(result['observation']['missingSectorHistoryCount'],0)
  self.assertIsNone(result['observation']['sectorClassificationCount'])
  with patch.object(c.server,'build_dashboard_payload',side_effect=AssertionError('no request')):
   self.assertEqual(c.collect('midday',root=self.root,now=self.now)['status'],'already_collected')
  self.assertEqual(result['ffdCalls'],0)
 def test_close_different_run_and_no_breadth_freeze(self):
  a=c.collect('midday',root=self.root,now=self.now,builder=self.build)
  b=c.collect('close',root=self.root,now=self.now.replace(hour=16),builder=self.build)
  self.assertNotEqual(a['runId'],b['runId'])
  data=json.loads((self.root/'dashboard-observed.json').read_text())
  self.assertNotIn('r02Breadth',data['payload'])
 def test_nontrading_and_wrong_session_skip(self):
  for session,now in [('close',self.now),('midday',self.now+dt.timedelta(days=1))]:
   self.assertEqual(c.collect(session,root=self.root,now=now)['status'],'skipped')
 def test_empty_preserves_prior(self):
  c.collect('midday',root=self.root,now=self.now,builder=self.build)
  before=(self.root/'dashboard-observed.json').read_bytes()
  out=c.collect('close',root=self.root,now=self.now.replace(hour=16),builder=lambda **kw:{})
  self.assertEqual(out['status'],'failed')
  self.assertEqual(before,(self.root/'dashboard-observed.json').read_bytes())
if __name__=='__main__':unittest.main()
