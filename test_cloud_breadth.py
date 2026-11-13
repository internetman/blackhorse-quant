import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cloud_breadth as cloud
from test_daily_breadth import snapshot, CALENDAR
from test_midday_breadth import candidate, NOW


class CloudTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root/'market-trading-calendar.json').write_text(CALENDAR)
        self.calendar = json.loads(CALENDAR)
        self.now = NOW.replace(hour=16, minute=40)
        self.write_pair('close')
        self.write_pair('midday')

    def tearDown(self):
        self.temp.cleanup()

    def write_pair(self, session):
        data = snapshot('2026-11-12') if session == 'close' else candidate()
        status = dict(status='success', asOf=data['asOf'])
        status['lastCollectedAt' if session == 'close' else 'generatedAt'] = data['generatedAt']
        for name, value in zip(cloud.FILES[session][:2], (data, status)):
            (self.root/name).write_text(json.dumps(value))
        return data

    def test_schedule_uses_event_cron_not_wall_clock(self):
        self.assertEqual(cloud.choose_session('schedule', '0,20 4 * * 1-5', 'close', self.now), 'midday')
        self.assertEqual(cloud.choose_session('schedule', '40 8,9,10 * * 1-5', 'midday', NOW), 'close')
        with self.assertRaises(ValueError): cloud.choose_session('schedule', 'unknown', 'auto', NOW)
        self.assertEqual(cloud.choose_session('push', '', 'midday', NOW), 'close')
        self.assertEqual(cloud.choose_session('workflow_dispatch', '', 'auto', NOW), 'midday')

    def test_late_noon_holidays_and_unknown_calendar_fail_closed(self):
        with patch.object(cloud.daily, 'refresh') as close, patch.object(cloud.midday, 'refresh') as noon:
            result = cloud.run(self.root, self.now, 'schedule', '0,20 4 * * 1-5')
            self.assertEqual(result['status'], 'skipped'); self.assertEqual(result['session'], 'midday')
            result = cloud.run(self.root, NOW.replace(day=14), 'push')
            self.assertEqual(result['status'], 'skipped')
            with self.assertRaises(ValueError): cloud.run(self.root, NOW.replace(year=2035), 'push')
            close.assert_not_called(); noon.assert_not_called()

    def test_pair_generation_and_adjustment_required(self):
        for session, now in [('close', self.now), ('midday', NOW)]:
            cloud.validate_pair(self.root, session, now, self.calendar)
            path = self.root/cloud.FILES[session][1]
            status = json.loads(path.read_text()); status['asOf'] = '2026-11-11'; path.write_text(json.dumps(status))
            with self.assertRaises(ValueError): cloud.validate_pair(self.root, session, now, self.calendar)

    def git_fake(self, changed='market-breadth.json', advance=False):
        state = {'staged': '', 'committed': False, 'pushed': False}
        def fake(root, *args):
            if args == ('rev-parse', '--show-toplevel'): return str(self.root)
            if args == ('remote', 'get-url', 'origin'): return cloud.REPOSITORY
            if args == ('rev-parse', 'HEAD'): return 'new' if state['committed'] else 'old'
            if args == ('rev-parse', 'FETCH_HEAD'): return 'other' if advance else 'old'
            if args[:1] == ('ls-tree',): return ''
            if args == ('diff', 'HEAD', '--name-only'): return changed
            if args == ('diff', '--cached', '--name-only'): return state['staged']
            if args[:1] == ('add',): state['staged'] = '\n'.join(args[2:]); return ''
            if 'commit' in args: state['committed'] = True; return ''
            if args[:1] == ('push',):
                self.assertEqual(args, ('push', 'origin', 'HEAD:main')); state['pushed'] = True; return ''
            if args[:1] == ('ls-remote',): return 'new\trefs/heads/main'
            return ''
        return fake, state

    def test_publish_allowlist_remote_head_and_nonforce_push(self):
        fake, state = self.git_fake()
        with patch.object(cloud, 'git', side_effect=fake):
            report = cloud.publish_session(self.root, 'close', self.now, self.calendar)
        self.assertEqual(report['commit'], 'new'); self.assertTrue(state['pushed'])
        for changed, advance in [('market-breadth-midday.json', False), ('market-breadth.js', False), ('market-breadth.json', True)]:
            fake, state = self.git_fake(changed, advance)
            with patch.object(cloud, 'git', side_effect=fake), self.assertRaises(ValueError):
                cloud.publish_session(self.root, 'close', self.now, self.calendar)
            self.assertFalse(state['pushed'])
        fake, state = self.git_fake('market-breadth-midday.json')
        with patch.object(cloud, 'git', side_effect=fake):
            self.assertEqual(cloud.publish_session(self.root, 'midday', NOW, self.calendar)['status'], 'pushed')

    def test_site_requires_identical_snapshot_status_and_calendar(self):
        def fetch(url, **kw): return json.loads((self.root/url.split('/')[-1].split('?')[0]).read_text())
        with patch.object(cloud, 'fetch', side_effect=fetch):
            self.assertEqual(cloud.verify_site(self.root, 'midday', attempts=1)['status'], 'verified')
        with patch.object(cloud, 'fetch', return_value={}):
            with self.assertRaisesRegex(RuntimeError, 'No additional credential'):
                cloud.verify_site(self.root, 'close', attempts=1)

    def test_forced_cold_run_and_cross_session_isolation(self):
        with patch.object(cloud, 'check_repository'), patch.object(cloud, 'changed_paths', return_value=set()), patch.object(cloud, 'git', return_value=''), patch.object(cloud, 'publish_session', return_value={'status':'unchanged'}) as pub, patch.object(cloud, 'verify_site', return_value={'status':'verified'}), patch.object(cloud.daily, 'refresh', return_value={'status':'success'}) as refresh:
            receipt = cloud.run(self.root, self.now, 'push')
            self.assertEqual(receipt['status'],'already_current'); refresh.assert_not_called()
            receipt = cloud.run(self.root, self.now, 'workflow_dispatch', force=True)
            self.assertTrue(receipt['forcedCollection']); self.assertTrue(refresh.call_args.kwargs['force'])
            def pollute(**kw):
                (self.root/'market-breadth-midday.json').write_text('{}')
                return {'status':'success'}
            refresh.side_effect = pollute; pub.reset_mock()
            with self.assertRaisesRegex(ValueError, 'other session'):
                cloud.run(self.root, self.now, 'workflow_dispatch', force=True)
            pub.assert_not_called()
            cache = self.root/'output'/'qfq-breadth-cache'; cache.mkdir(parents=True)
            (cache/'x.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'empty source caches'):
                cloud.run(self.root, self.now, 'workflow_dispatch', force=True)

    def test_verification_failure_preserves_published_commit_receipt(self):
        publication = dict(status='pushed', commit='verified-commit', files=['market-breadth.json'])
        with patch.object(cloud, 'check_repository'), patch.object(cloud, 'changed_paths', return_value=set()), patch.object(cloud, 'git', return_value=''), patch.object(cloud, 'publish_session', return_value=publication), patch.object(cloud, 'verify_site', side_effect=RuntimeError('Vercel not updated')), patch.object(cloud.daily, 'refresh', return_value={'status':'success'}):
            with self.assertRaises(cloud.PublicationVerificationError) as caught:
                cloud.run(self.root, self.now, 'workflow_dispatch', force=True)
        self.assertEqual(caught.exception.receipt['publication']['commit'], 'verified-commit')
        self.assertEqual(caught.exception.receipt['failedStage'], 'website_verification')

    def test_workflow_has_only_pinned_checkout_and_no_long_lived_secret(self):
        root = Path(__file__).parent
        path = root/'.github'/'workflows'/'market-breadth.yml'
        if not path.exists(): path = root/'handoff'/'cloud-breadth.yml'
        text = path.read_text()
        self.assertIn('actions/checkout@11d5960a326750d5838078e36cf38b85af677262', text)
        uses = [line.strip() for line in text.splitlines() if 'uses:' in line]
        self.assertTrue(1 <= len(uses) <= 2)
        self.assertTrue(all('actions/checkout@11d5960a326750d5838078e36cf38b85af677262' in line for line in uses))
        self.assertNotIn('secrets.', text)
        self.assertIn('contents: write', text)
        self.assertIn("'0,20 4 * * 1-5'", text)
        self.assertIn("'40 8,9,10 * * 1-5'", text)
        self.assertNotIn('market-breadth.json\'\n', text)  # data commits cannot retrigger cold run


if __name__ == '__main__':
    unittest.main()
