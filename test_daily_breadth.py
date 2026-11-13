import copy
import datetime as dt
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from daily_breadth import refresh, validate_snapshot, run_lock, merge_verified_history
from market_breadth import ZONE
from complete_breadth import VERSION, BENCHMARKS
from publish_breadth import publish, publish_checkout, git, verify_live
from trading_calendar import load_calendar, expected_close, is_trading_day, parse_annual_page

CALENDAR = Path(__file__).with_name('market-trading-calendar.json').read_text()


def snapshot(date='2026-11-04'):
    row = dict(date=date, n=5000, ma20=dict(pct=50, above=2500, valid=5000), ma50=dict(pct=50, above=2500, valid=5000))
    return dict(schemaVersion=1, asOf=date, dates=[date], market=[row], generatedAt=date+'T16:40:00+08:00',
                universeCount=5000, latestHistoryCount=5000, coveragePct=100, barStatus='completed',
                universeLabel='沪深A股', availableMetrics=['ma20','ma50'], scopeVersion=VERSION,
                dailyHistory=dict(adjustment='qfq',cutoff=date),
                benchmarks=[dict(secid=s,name=n,asOf=date,close=100,ma50=99,ma50Slope20=1,historyCount=100) for s,n in BENCHMARKS],
                rows=[dict(industry=str(i), series=[copy.deepcopy(row)]) for i in range(50)])


class DailyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root/'market-trading-calendar.json').write_text(CALENDAR)
        self.target = self.root/'market-breadth.json'
        self.target.write_text(json.dumps(snapshot('2026-11-03')))
        self.now = dt.datetime(2026, 11, 4, 16, 40, tzinfo=ZONE)

    def tearDown(self):
        self.temp.cleanup()

    def test_real_holidays_and_weekend_workdays_are_closed(self):
        cal = load_calendar(self.root/'market-trading-calendar.json')
        self.assertEqual(expected_close(dt.datetime(2026, 10, 7, 18, tzinfo=ZONE), cal), '2026-09-30')
        self.assertFalse(is_trading_day(dt.date(2026, 10, 10), cal))
        self.assertEqual(expected_close(dt.datetime(2026, 11, 5, 10, tzinfo=ZONE), cal), '2026-11-04')
        with self.assertRaises(ValueError):
            is_trading_day(dt.date(2027, 1, 5), cal)
        with self.assertRaises(ValueError):
            parse_annual_page('2027年休市安排，只有周末', 2027)

    def test_before_close_and_holiday_do_not_fetch_or_relabel(self):
        before = self.target.read_bytes()
        with patch('complete_breadth.collect') as collect:
            result = refresh(self.root, self.now.replace(hour=12), scheduled=True)
            self.assertEqual(result['status'], 'skipped')
            collect.assert_not_called()
        self.assertEqual(before, self.target.read_bytes())

    def test_failed_acquisition_preserves_last_good_bytes(self):
        before = self.target.read_bytes()
        with patch('complete_breadth.collect', side_effect=ValueError('stale source')):
            with self.assertRaisesRegex(ValueError, 'stale source'):
                refresh(self.root, self.now, attempts=1, force=True)
        self.assertEqual(before, self.target.read_bytes())
        self.assertEqual(json.loads((self.root/'market-breadth-status.json').read_text())['status'], 'failed')

    def test_success_then_second_run_is_idempotent(self):
        with patch('complete_breadth.collect', return_value=snapshot()) as collect:
            self.assertEqual(refresh(self.root, self.now, force=True)['status'], 'success')
            status = (self.root/'market-breadth-status.json').read_bytes()
            retry = refresh(self.root, self.now)
            self.assertEqual(retry['status'], 'success')
            self.assertTrue(retry['alreadyCurrent'])
            self.assertEqual(status, (self.root/'market-breadth-status.json').read_bytes())
            self.assertEqual(collect.call_count, 1)
        self.assertEqual(json.loads(self.target.read_text())['market'][-1]['ma50']['pct'],50)
        self.assertTrue((self.root/'output/breadth-history/2026-11-04.json').exists())

    def test_rejects_future_low_coverage_and_wrong_fraction(self):
        for change in [lambda d:d.update(asOf='2026-11-05'), lambda d:d.update(coveragePct=94),
                       lambda d:d['market'][-1]['ma20'].update(pct=99),
                       lambda d:d['market'][-1]['ma50'].update(pct=None)]:
            data = snapshot()
            change(data)
            with self.assertRaises(ValueError):
                validate_snapshot(data, '2026-11-04')
        with self.assertRaisesRegex(ValueError, 'regression'):
            validate_snapshot(snapshot('2026-11-03'), '2026-11-03', snapshot())

    def test_prior_verified_market_point_is_not_discarded(self):
        old = snapshot('2026-11-03')
        data = snapshot()
        blank = copy.deepcopy(old['market'][0]); blank['ma20'] = dict(pct=None, above=0, valid=0)
        data['market'].insert(0, blank)
        merged = merge_verified_history(data, old)
        self.assertEqual(merged['market'][0]['ma20']['valid'], 5000)

    def test_legacy_ma20_snapshot_is_upgraded_not_treated_as_complete(self):
        legacy = snapshot()
        legacy.pop('scopeVersion'); legacy.pop('dailyHistory'); legacy.pop('benchmarks')
        legacy['availableMetrics'] = ['ma20']
        legacy['market'][-1]['ma50'] = dict(pct=None, above=0, valid=0)
        self.target.write_text(json.dumps(legacy))
        with patch('complete_breadth.collect', return_value=snapshot()) as collect:
            refresh(self.root, self.now, force=True)
            self.assertEqual(collect.call_count, 1)
        self.assertEqual(json.loads(self.target.read_text())['scopeVersion'], VERSION)

    def test_wrong_scope_cannot_merge_old_history(self):
        old, new = snapshot('2026-11-03'), snapshot()
        old['scopeVersion'] = 'different-basis'
        blank = copy.deepcopy(old['market'][0]); blank['ma20'] = dict(pct=None, above=0, valid=0)
        new['market'].insert(0, blank)
        self.assertEqual(merge_verified_history(new,old)['market'][0]['ma20']['valid'],0)

    def test_missing_wrong_date_duplicate_and_nonfinite_benchmarks_rejected(self):
        for change in [lambda d:d.update(benchmarks=[]),
                       lambda d:d['benchmarks'][0].update(asOf='2026-11-03'),
                       lambda d:d['benchmarks'][0].update(ma50=float('nan')),
                       lambda d:d['benchmarks'][0].update(secid=d['benchmarks'][1]['secid']),
                       lambda d:d['dailyHistory'].update(adjustment='raw')]:
            data=snapshot();change(data)
            with self.assertRaises(ValueError):validate_snapshot(data,'2026-11-04')

    def test_overlapping_processes_cannot_both_run(self):
        with run_lock(self.root/'lock'):
            with self.assertRaisesRegex(RuntimeError, 'lock'):
                with run_lock(self.root/'lock'):
                    self.fail('A second collector acquired the lock')

    def test_publish_preserves_unrelated_files_and_rejects_older_close(self):
        remote, seed = self.root/'remote.git', self.root/'seed'
        subprocess.run(['git', 'init', '--quiet', '--bare', str(remote)], check=True)
        subprocess.run(['git', 'init', '--quiet', '--initial-branch=main', str(seed)], check=True)
        (seed/'market-breadth.json').write_text(json.dumps(snapshot()))
        (seed/'m2-data.js').write_text('unrelated, must remain byte-identical')
        git(seed, 'add', '.')
        git(seed, '-c', 'user.name=test', '-c', 'user.email=test@example.com', 'commit', '-qm', 'seed')
        git(seed, 'remote', 'add', 'origin', str(remote)); git(seed, 'push', '-q', 'origin', 'main')
        git(remote, 'symbolic-ref', 'HEAD', 'refs/heads/main')
        self.target.write_text(json.dumps(snapshot()))
        (self.root/'market-breadth-status.json').write_text('{"status":"success","asOf":"2026-11-04"}')
        result = publish(self.root, str(remote))
        self.assertEqual(result['status'], 'pushed')
        self.assertEqual(git(remote, 'show', 'main:m2-data.js'), 'unrelated, must remain byte-identical')
        self.assertEqual(set(result['files']), {'market-breadth-status.json', 'market-trading-calendar.json'})
        self.target.write_text(json.dumps(snapshot('2026-11-03')))
        with self.assertRaisesRegex(ValueError, 'newer close'):
            publish(self.root, str(remote))

    def test_scheduled_publisher_cannot_release_unapproved_ma50_scope_upgrade(self):
        remote, seed = self.root/'guard-remote.git', self.root/'guard-seed'
        subprocess.run(['git','init','--quiet','--bare',str(remote)],check=True)
        subprocess.run(['git','init','--quiet','--initial-branch=main',str(seed)],check=True)
        legacy=snapshot();legacy.pop('scopeVersion');legacy['availableMetrics']=['ma20']
        legacy['market'][-1]['ma50']=dict(pct=None,above=0,valid=0)
        (seed/'market-breadth.json').write_text(json.dumps(legacy))
        git(seed,'add','.');git(seed,'-c','user.name=test','-c','user.email=test@example.com','commit','-qm','seed')
        git(seed,'remote','add','origin',str(remote));git(seed,'push','-q','origin','main');git(remote,'symbolic-ref','HEAD','refs/heads/main')
        self.target.write_text(json.dumps(snapshot()))
        (self.root/'market-breadth-status.json').write_text(json.dumps(dict(status='success',asOf='2026-11-04')))
        before=git(remote,'rev-parse','main')
        with self.assertRaisesRegex(ValueError,'explicit release approval'):publish(self.root,str(remote))
        self.assertEqual(git(remote,'rev-parse','main'),before)
        self.assertEqual(publish(self.root,str(remote),approve_scope_upgrade=True)['status'],'pushed')

    def test_reviewed_cloud_installation_is_scoped_and_head_guarded(self):
        from test_midday_breadth import candidate
        remote, seed = self.root/'cloud-release.git', self.root/'cloud-seed'
        subprocess.run(['git','init','--quiet','--bare',str(remote)],check=True)
        subprocess.run(['git','init','--quiet','--initial-branch=main',str(seed)],check=True)
        (seed/'market-breadth.json').write_text(json.dumps(snapshot('2026-11-10')))
        (seed/'m2-data.js').write_text('preserve unrelated website')
        git(seed,'add','.');git(seed,'-c','user.name=test','-c','user.email=test@example.com','commit','-qm','seed')
        git(seed,'remote','add','origin',str(remote));git(seed,'push','-q','origin','main');git(remote,'symbolic-ref','HEAD','refs/heads/main')
        head=git(remote,'rev-parse','main')
        self.target.write_text(json.dumps(snapshot('2026-11-11')))
        (self.root/'market-breadth-status.json').write_text('{}')
        (self.root/'market-breadth-midday.json').write_text(json.dumps(candidate()))
        (self.root/'market-breadth-midday-status.json').write_text('{}')
        (self.root/'allowed.py').write_text('reviewed release')
        (self.root/'handoff').mkdir();(self.root/'handoff/cloud-breadth.yml').write_text('permissions: {}')
        with patch('publish_breadth.CODE_FILES',('allowed.py',)):
            with self.assertRaisesRegex(ValueError,'head changed'):
                publish(self.root,str(remote),include_code=True,install_cloud=True,expected_remote_commit='0'*40)
            self.assertEqual(git(remote,'rev-parse','main'),head)
            result=publish(self.root,str(remote),include_code=True,install_cloud=True,expected_remote_commit=head)
        self.assertIn('.github/workflows/market-breadth.yml',result['files'])
        self.assertIn('market-breadth-midday.json',result['files'])
        self.assertEqual(git(remote,'show','main:m2-data.js'),'preserve unrelated website')
        self.assertEqual(git(remote,'show','main:.github/workflows/market-breadth.yml'),'permissions: {}')

    def test_checkout_publisher_uses_existing_checkout_and_rejects_races(self):
        remote, repo = self.root/'checkout-remote.git', self.root/'checkout'
        subprocess.run(['git', 'init', '--quiet', '--bare', str(remote)], check=True)
        subprocess.run(['git', 'init', '--quiet', '--initial-branch=main', str(repo)], check=True)
        (repo/'market-breadth.json').write_text(json.dumps(snapshot('2026-11-03')))
        (repo/'m2-data.js').write_text('preserve candidates')
        git(repo, 'add', '.')
        git(repo, '-c', 'user.name=test', '-c', 'user.email=test@example.com', 'commit', '-qm', 'seed')
        git(repo, 'remote', 'add', 'origin', str(remote)); git(repo, 'push', '-q', 'origin', 'main')
        (repo/'market-breadth.json').write_text(json.dumps(snapshot()))
        (repo/'market-breadth-status.json').write_text(json.dumps(dict(status='success', asOf='2026-11-04')))
        (repo/'output').mkdir(); (repo/'output'/'receipt.json').write_text('{}')
        publication = publish_checkout(repo, str(remote))
        self.assertEqual(publication['status'], 'pushed')
        self.assertEqual(git(remote, 'show', 'main:m2-data.js'), 'preserve candidates')
        self.assertEqual(publish_checkout(repo, str(remote))['status'], 'unchanged')
        self.assertEqual(publish_checkout(repo, str(remote).removesuffix('.git'))['status'], 'unchanged')
        with self.assertRaisesRegex(ValueError, 'unexpected repository'):
            publish_checkout(repo, str(remote)+'-different')
        (repo/'m2-data.js').write_text('unauthorized change')
        with self.assertRaisesRegex(ValueError, 'allowlist'):
            publish_checkout(repo, str(remote))
        git(repo, 'restore', 'm2-data.js')
        git(remote, 'update-ref', 'refs/heads/main', 'main^')
        with self.assertRaisesRegex(ValueError, 'advanced'):
            publish_checkout(repo, str(remote))

    def test_live_verification_rejects_same_date_old_generation(self):
        old, collected = snapshot(), snapshot()
        collected['generatedAt'] = '2026-11-04T18:00:00+08:00'
        with patch('publish_breadth.fetch', return_value=old):
            with self.assertRaisesRegex(RuntimeError, 'generation'):
                verify_live('2026-11-04', attempts=1, snapshot=collected)


if __name__ == '__main__':
    unittest.main()
