import copy
import unittest
from dashboard_last_good import merge_modules
class LastGoodTests(unittest.TestCase):
 def prior(self):
  return dict(observation=dict(runId='old',finishedAt='2026-11-13T04:00:00+00:00',asOf='2026-11-13',sectorClassificationCount=496),payload=dict(indices=[{'price':1}],sectors=[{'code':'A'}],top5=[dict(code='A',leaders10=[{'price':1}],trend10=[])]))
 def test_partial_does_not_clear_rank(self):
  new=dict(indices=[{'price':2}],sectors=[],top5=[])
  obs=dict(runId='new',finishedAt='2026-11-13T08:00:00+00:00',asOf='2026-11-13')
  data,result=merge_modules(new,obs,self.prior())
  self.assertEqual(data['indices'][0]['price'],2)
  self.assertEqual(data['sectors'][0]['code'],'A')
  self.assertEqual(data['top5'][0]['leaders10'][0]['price'],1)
  self.assertEqual(result['modules']['sectorRank']['runId'],'old')
  self.assertTrue(result['modules']['sectorRank']['stale'])
  self.assertEqual(data['top5'][0]['observedModules']['leaders']['finishedAt'],'2026-11-13T04:00:00+00:00')
 def test_second_fallback_does_not_retimestamp_old_module(self):
  obs=dict(runId='new',finishedAt='2026-11-13T08:00:00+00:00')
  data,meta=merge_modules(dict(indices=[{}]),obs,self.prior())
  _,nextmeta=merge_modules(dict(indices=[{}]),dict(runId='later',finishedAt='2026-11-14T04:00:00+00:00'),dict(payload=data,observation=meta))
  self.assertEqual(nextmeta['modules']['sectorRank']['runId'],'old')
 def test_no_top5_is_unknown_not_zero_missing(self):
  _,meta=merge_modules(dict(indices=[{}]),dict(runId='new'))
  self.assertIsNone(meta['missingSectorHistoryCount'])
 def test_different_sector_never_borrows_old_leaders(self):
  data,_=merge_modules(dict(sectors=[{'code':'B'}],top5=[{'code':'B','leaders10':[]}]),dict(runId='new'),self.prior())
  self.assertEqual(data['top5'][0]['leaders10'],[])
if __name__=='__main__':unittest.main()
