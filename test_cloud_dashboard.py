import datetime as dt
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import cloud_dashboard as c

ENV={'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':'internetman/blackhorse-quant','GITHUB_REF':'refs/heads/main'}
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.status=dict(status='partial',asOf='2026-11-13',session='close',runId='r1',ffdCalls=0)
        self.write(c.STATUS,self.status)
        self.write(c.SNAPSHOT,dict(observation=dict(self.status,indexCount=1)))
    def tearDown(self):self.tmp.cleanup()
    def write(self,n,v):(self.root/n).write_text(json.dumps(v))
    def test_actions_gate(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(ValueError):c.require_actions()
    def test_matching_and_mismatch(self):
        c.validate(self.root,'close','2026-11-13')
        self.status['runId']='other';self.write(c.STATUS,self.status)
        with self.assertRaises(ValueError):c.validate(self.root,'close','2026-11-13')
    def test_failed_cannot_change_snapshot(self):
        self.status['status']='failed';self.write(c.STATUS,self.status)
        with patch.object(c.cloud,'changed_paths',return_value={c.SNAPSHOT}):
            with self.assertRaises(ValueError):c.publish(self.root,'close','2026-11-13')
    def test_width_not_allowlisted(self):
        with patch.object(c.cloud,'changed_paths',return_value={'market-breadth-status.json'}):
            with self.assertRaises(ValueError):c.publish(self.root,'close','2026-11-13')
    def test_remote_advance(self):
        def git(root,*args):return 'new' if args==('rev-parse','FETCH_HEAD') else ('old' if args==('rev-parse','HEAD') else '')
        with patch.object(c.cloud,'changed_paths',return_value={c.STATUS}),patch.object(c.cloud,'git',side_effect=git) as g:
            with self.assertRaises(ValueError):c.publish(self.root,'close','2026-11-13')
            self.assertFalse(any('push' in call.args for call in g.call_args_list))
    def test_site_exact_json(self):
        def fetch(url,**kw):return c.read(self.root,c.SNAPSHOT if '/'+c.SNAPSHOT in url else c.STATUS)
        with patch.object(c,'fetch',side_effect=fetch):self.assertEqual(c.verify_site(self.root,1)['runId'],'r1')
        with patch.object(c,'fetch',return_value={}):
            with self.assertRaises(RuntimeError):c.verify_site(self.root,1)
    def test_session_and_duplicate(self):
        with patch.dict(os.environ,ENV),patch.object(c,'load_calendar',return_value={}),patch.object(c.collector,'check_session',return_value=True),patch.object(c.cloud,'check_repository'),patch.object(c.cloud,'changed_paths',return_value=set()),patch.object(c.cloud,'git',return_value=''),patch.object(c,'publish',return_value={}),patch.object(c,'verify_site',return_value={}),patch.object(c.collector,'collect') as collect:
            result=c.run(self.root,now=dt.datetime(2026,11,13,17,tzinfo=c.ZONE),requested='close')
            self.assertEqual(result['status'],'already_attempted');collect.assert_not_called()
    def test_closed_session(self):
        with patch.dict(os.environ,ENV),patch.object(c,'load_calendar',return_value={}),patch.object(c.collector,'check_session',return_value=False),patch.object(c.collector,'collect') as collect:
            self.assertEqual(c.run(self.root,requested='midday')['status'],'skipped');collect.assert_not_called()
    def test_dirty_refused(self):
        with patch.dict(os.environ,ENV),patch.object(c,'load_calendar',return_value={}),patch.object(c.collector,'check_session',return_value=True),patch.object(c.cloud,'check_repository'),patch.object(c.cloud,'changed_paths',return_value={'market-breadth-status.json'}):
            with self.assertRaises(ValueError):c.run(self.root,requested='close')
if __name__=='__main__':unittest.main()
