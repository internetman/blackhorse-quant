import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cloud_breadth as cloud
from close_target import close_target
from test_daily_breadth import CALENDAR
from test_midday_breadth import NOW


class CloseTargetTests(unittest.TestCase):
    def setUp(self):
        self.calendar = json.loads(CALENDAR)

    def test_default_catches_up_overnight_weekend_and_before_close(self):
        friday = NOW.replace(day=13, hour=16, minute=40)
        self.assertEqual(close_target(friday, self.calendar), '2026-11-13')
        self.assertEqual(close_target(friday + dt.timedelta(hours=8), self.calendar), '2026-11-13')
        self.assertEqual(close_target(friday.replace(day=16, hour=15, minute=40), self.calendar), '2026-11-13')
        self.assertEqual(close_target(friday.replace(day=16), self.calendar), '2026-11-16')
        self.assertEqual(close_target(friday.replace(day=16, hour=8), self.calendar, '2026-11-12'), '2026-11-12')

    def test_explicit_date_must_be_verified_and_finalized(self):
        preclose = NOW.replace(day=16, hour=15)
        for date in ('20261112', '2026-11-99', '2026-11-14', '2026-11-16', '2035-11-16', ''):
            with self.subTest(date=date), self.assertRaises(ValueError):
                close_target(preclose, self.calendar, date)

    def test_close_gets_target_but_late_noon_is_never_relabelled(self):
        fri = NOW.replace(day=13, hour=16, minute=40)
        late = fri + dt.timedelta(hours=8)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'market-trading-calendar.json').write_text(CALENDAR)
            with patch.object(cloud.daily, 'refresh', side_effect=AssertionError('cold collector called')):
                close = cloud.run(root, late, 'schedule', '40 8,9,10 * * 1-5')
                self.assertEqual(close['targetDate'], '2026-11-13')
                self.assertEqual(close['status'], 'blocked_incremental_unverified')
                self.assertEqual(close['historyCalls'], 0)
                self.assertEqual(cloud.run(root, late, 'schedule', '0,20 4 * * 1-5')['status'], 'skipped')
                with self.assertRaisesRegex(ValueError, 'current finalized close'):
                    cloud.run(root, late, 'workflow_dispatch', requested='close', target_date='2026-11-13', force=True)
                with self.assertRaisesRegex(ValueError, 'manual close job'):
                    cloud.run(root, fri, 'workflow_dispatch', requested='midday', target_date='2026-11-13')
                manual = cloud.run(root, late, 'workflow_dispatch', requested='close', target_date='2026-11-12')
                self.assertEqual(manual['targetDate'], '2026-11-12')
                (root/'market-breadth.json').write_text(json.dumps({'asOf': '2026-11-13'}))
                stale = cloud.run(root, late, 'workflow_dispatch', requested='close', target_date='2026-11-12')
                self.assertEqual(stale['status'], 'skipped_stale_target')
                self.assertEqual(stale['historyCalls'], 0)


if __name__ == '__main__':
    unittest.main()
