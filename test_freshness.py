import unittest
from server import dashboard_module_status
class FreshnessTests(unittest.TestCase):
 def test_receipt_never_becomes_quote_time(self):
  d=dict(generatedAt='2026-11-13T12:10:00+08:00',source={'indices':'Eastmoney'},indices=[{}],r02={'updated':'2026-06-29 收盘'},r02Breadth={'asOf':'2026-11-12','coveragePct':95},top5=[{'code':'BK0001','trend10':[{'date':'2026-11-10'},{'date':'2026-11-12'}],'trend10Cached':True}],sectorRankStatus={'cached':True,'cachedAt':'2026-11-12'})
  x=dashboard_module_status(d)
  self.assertIsNone(x['indices']['sourceTime'])
  self.assertEqual(x['closeBreadth']['asOf'],'2026-11-12')
  self.assertEqual(x['sectorTrends'][0]['lastDate'],'2026-11-12')
  self.assertFalse(x['r02Decision']['automaticRecalculation'])
  self.assertFalse(x['attribution']['newsVerified'])
if __name__=='__main__':unittest.main()
