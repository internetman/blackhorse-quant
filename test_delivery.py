import copy
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
import dashboard_delivery as d

class DeliveryTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  fixture=dict(schemaVersion=1,observation=dict(runId='fixture-run',finishedAt='2026-11-13T04:00:17.560982+00:00',quoteTimeVerified=False,sectorClassificationCount=496),payload=dict(generatedAt='2026-11-13T04:00:17.560982+00:00',source={'indices':'fixture'},r02={'updated':'2026-06-29'},indices=[{'code':'000001'}],sectors=[],top5=[],warnings=[]))
  breadth=dict(asOf='2026-11-11',coveragePct=95,source='fixture',market=[{'date':'2026-11-11'}],rows=[])
  (self.root/'dashboard-observed.json').write_text(json.dumps(fixture))
  (self.root/'market-breadth.json').write_text(json.dumps(breadth))
  self.now=dt.datetime.fromisoformat('2026-11-13T04:10:00+00:00')
 def tearDown(self):self.temp.cleanup()
 def test_cached_observation_never_redates_quote(self):
  x=d.build_delivery(root=self.root,now=self.now)
  self.assertFalse(x['observation']['quoteTimeVerified'])
  self.assertFalse(x['observation']['stale'])
  y=d.build_delivery(root=self.root,now=self.now+dt.timedelta(days=1),live_builder=lambda **kw: (_ for _ in ()).throw(TimeoutError('test')))
  self.assertTrue(y['observation']['stale'])
  self.assertEqual(x['generatedAt'],y['generatedAt'])
  self.assertEqual(x['observation']['finishedAt'],y['observation']['finishedAt'])
 def test_close_read_at_delivery_not_frozen(self):
  b=json.loads((self.root/'market-breadth.json').read_text());b['asOf']='2026-11-12';b['market'][-1]['date']='2026-11-12'
  (self.root/'market-breadth.json').write_text(json.dumps(b))
  x=d.build_delivery(root=self.root,now=self.now)
  self.assertEqual(x['marketDistribution']['asOf'],'2026-11-12')
 def test_force_failure_retains_exact_observation(self):
  def fail(**kw):raise TimeoutError('test')
  x=d.build_delivery(True,root=self.root,now=self.now,live_builder=fail)
  self.assertTrue(x['observation']['liveAttemptFailed'])
  self.assertEqual(x['observation']['finishedAt'],'2026-11-13T04:00:17.560982+00:00')
 def test_stale_automatic_refresh_attempts_live(self):
  called=[]
  saved=d.observed_payload(self.root,self.now)
  def live(**kw):
   called.append(kw)
   return copy.deepcopy(saved)
  x=d.build_delivery(root=self.root,now=self.now+dt.timedelta(days=1),live_builder=live)
  self.assertEqual(len(called),1)
  self.assertEqual(x['observation']['mode'],'live_fetch_attempt')
  self.assertTrue(any('分类' in text for text in x['warnings']))
  self.assertTrue(any('未核新闻' in text for text in x['warnings']))
 def test_fresh_does_not_call_live(self):
  def forbidden(**kw):self.fail('fresh cache must not call network')
  d.build_delivery(root=self.root,now=self.now,live_builder=forbidden)
 def test_no_full_breadth_in_published_observation(self):
  x=json.loads((self.root/'dashboard-observed.json').read_text())
  self.assertNotIn('r02Breadth',x['payload'])
  self.assertNotIn('marketDistribution',x['payload'])
if __name__=='__main__':unittest.main()
