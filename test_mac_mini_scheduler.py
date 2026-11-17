import datetime as dt
import fcntl
import json
import plistlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from zoneinfo import ZoneInfo

from mac_mini_scheduler import candidate, tick
from trading_calendar import load_calendar


class MacSchedulerTests(unittest.TestCase):
    def setUp(self):
        self.calendar = load_calendar(year=2026)
        self.root = Path(__file__).parent
        self.worker = Path('/not-executed/heima')
        self.tmp = tempfile.TemporaryDirectory()
        self.state = Path(self.tmp.name) / 'private'
        self.calls = []

    def tearDown(self):
        self.tmp.cleanup()

    def time(self, value):
        return dt.datetime.fromisoformat(value).replace(tzinfo=ZoneInfo('Asia/Shanghai'))

    def run_job(self, value, status='verified'):
        def runner(args, **kw):
            self.calls.append(args)
            self.assertIn((self.state / 'launchd-receipts.json').read_text().count('"inflight"'), (1,))
            session = args[2]
            date = args[4]
            payload = dict(status=status, targetDate=date, session=session, verifiedDate=date,
                           publicationVerified=True, historyCalls=0)
            return subprocess.CompletedProcess(args, 0, json.dumps(payload), '')
        return tick(self.time(value), self.calendar, self.state, self.worker, True, run=runner)

    def test_market_zone_and_noon_cutoff(self):
        now = self.time('2026-11-16T12:07').astimezone(ZoneInfo('America/Los_Angeles'))
        self.assertEqual(candidate(now, self.calendar), ('midday','2026-11-16',1))
        self.assertIsNone(candidate(self.time('2026-11-16T12:55'), self.calendar))
        self.assertEqual(candidate(self.time('2026-11-14T08:45'), self.calendar), ('close','2026-11-13',4))
        self.assertEqual(candidate(self.time('2026-11-16T16:40'), self.calendar), ('close','2026-11-16',1))

    def test_preview_and_persisted_success_prevent_duplicate_dispatch(self):
        r = tick(self.time('2026-11-16T12:07'), self.calendar, self.state, self.worker)
        self.assertEqual(r['status'], 'preview_no_worker')
        self.assertFalse(self.state.exists())
        self.assertEqual(self.run_job('2026-11-16T12:07')['status'], 'verified')
        self.assertEqual(self.run_job('2026-11-16T12:27')['status'], 'already_attempted')
        self.assertEqual(len(self.calls), 1)

    def test_retry_only_next_slot_after_verified_no_query(self):
        self.assertEqual(self.run_job('2026-11-16T12:07','retryable_no_paid_query')['status'], 'retryable_no_paid_query')
        self.assertEqual(self.run_job('2026-11-16T12:08')['status'], 'already_attempted')
        self.assertEqual(self.run_job('2026-11-16T12:27')['status'], 'verified')
        self.assertEqual(len(self.calls), 2)

    def test_uncertain_result_blocks_later_paid_retry_across_lanes(self):
        self.assertEqual(self.run_job('2026-11-16T12:07','unknown')['status'], 'uncertain')
        self.assertEqual(self.run_job('2026-11-16T16:40')['status'], 'reconcile_pending_run')
        self.assertEqual(len(self.calls), 1)

    def test_shared_lock_refuses_concurrent_launch(self):
        self.state.mkdir(mode=0o700)
        with (self.state / 'run.lock').open('w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            reply = self.run_job('2026-11-16T12:07')
            self.assertEqual(reply['status'], 'busy')
            self.assertEqual(len(self.calls), 0)

    def test_template_defaults_to_preview(self):
        doc = plistlib.loads((self.root/'deployment/com.heima.refresh.plist.example').read_bytes())
        self.assertEqual(doc['StartInterval'], 60)
        self.assertNotIn('--execute',doc['ProgramArguments'])


if __name__ == '__main__':
    unittest.main()
