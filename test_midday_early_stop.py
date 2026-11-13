import unittest
from midday_breadth import coverage_still_reachable
class EarlyStopTests(unittest.TestCase):
 def test_original_denominator_and_exact_gate(self):
  self.assertTrue(coverage_still_reachable(5114,152,5223))
  self.assertFalse(coverage_still_reachable(5114,153,5223))
  self.assertFalse(coverage_still_reachable(5114,366,5223))
 def test_no_weakened_gate(self):
  self.assertTrue(coverage_still_reachable(100,5,100))
  self.assertFalse(coverage_still_reachable(100,6,100))
