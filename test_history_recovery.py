import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from complete_breadth import collect_histories

class RecoveryTests(unittest.TestCase):
    def test_only_failed_samples_are_retried(self):
        stocks = [dict(code='a'),dict(code='b')]
        calls=[]
        def get(stock, cutoff, cache):
            calls.append(stock['code'])
            if stock['code']=='b' and calls.count('b')==1:
                raise ValueError('temporary')
            return ([{'date':cutoff}], 'Tencent', 'hash')
        with tempfile.TemporaryDirectory() as d, patch('complete_breadth.get_history', side_effect=get), patch('complete_breadth.time.sleep'):
            histories, failures=collect_histories(stocks,'2026-11-11',Path(d),workers=1)
        self.assertEqual(calls,['a','b','b'])
        self.assertEqual(set(histories),{'a','b'})
        self.assertEqual(failures,[])

    def test_persistent_failure_is_bounded_and_reported(self):
        with tempfile.TemporaryDirectory() as d, patch('complete_breadth.get_history', side_effect=ValueError('no valid bars')) as get, patch('complete_breadth.time.sleep'):
            histories, failures=collect_histories([dict(code='a')],'2026-11-11',Path(d),workers=1)
        self.assertEqual(get.call_count,3)
        self.assertEqual(histories,{})
        self.assertEqual(failures,[dict(code='a',error='no valid bars')])

    def test_no_repair_after_time_budget(self):
        with tempfile.TemporaryDirectory() as d, patch('complete_breadth.get_history', side_effect=ValueError('missing')) as get, patch('complete_breadth.time.monotonic',side_effect=[0,2800]):
            histories, failures=collect_histories([dict(code='a')],'2026-11-11',Path(d),workers=1)
        self.assertEqual(get.call_count,1)
        self.assertEqual(len(failures),1)
