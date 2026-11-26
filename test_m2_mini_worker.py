import datetime as dt
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import m2_mini_worker as w
from mac_mini_scheduler import tick, ZONE
from trading_calendar import load_calendar


TARGET = "2026-11-16"


class MiniWorkerTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.m2 = self.root/"m2"
        self.m2.mkdir(mode=0o700)
        (self.m2/"seed.json").write_text("{}")
        self.calls=[]
        self.plan = dict(status="plan_only",asOfDate=TARGET,worstCasePoints=36,
                         plannedRequests=1,canReachCoverageGate=True,fitsCap=True)
        self.receipt = dict(status="candidate_ready",asOfDate=TARGET,historyCalls=1,valid=360)
        self.preview = dict(mode="derived-pilot",asOfDate=TARGET,runStatus="success",barStatus="completed",
                            universe={"scopeId":w.SCOPE,"valid":360,"total":360})
        self.code = 0

    def fake_run(self, args, **kw):
        self.calls.append((args,kw))
        if "--plan-only" in args:
            self.assertNotIn("FFD_API_KEY",kw["env"])
            return subprocess.CompletedProcess(args,0,json.dumps(self.plan),"")
        self.assertIn("--execute",args)
        (self.m2/f"derived-{TARGET}.json").write_text(json.dumps(self.preview))
        return subprocess.CompletedProcess(args,self.code,json.dumps(self.receipt),"")

    def configure(self, **opts):
        path = self.root/"m2-worker.json"
        path.touch(mode=0o600)
        path.write_text(json.dumps(dict({"executionEnabled":True,"maxPoints":36},**opts)))

    def call(self,session="close"):
        return w.result_for(session,TARGET,self.root,run=self.fake_run)

    def test_preflight_by_default_never_triggers_query_or_implies_deploy(self):
        response=self.call()
        self.assertEqual((response["status"],response["historyCalls"]),(w.SAFE,0))
        self.assertFalse(response["publicationVerified"])
        self.assertEqual(len(self.calls),1)

    def test_midday_is_not_close_fallback(self):
        self.configure()
        self.assertEqual(self.call("midday")["status"],w.SAFE)
        self.assertFalse(self.calls)

    def test_gate_failure_refuses_execute(self):
        self.configure(maxPoints=35)
        self.assertEqual(self.call()["reason"],"m2_coverage_or_budget_gate")
        self.assertEqual(len(self.calls),1)

    def test_private_success_with_app_opt_in(self):
        self.configure()
        response=self.call()
        self.assertEqual(response["status"],w.LOCAL)
        self.assertEqual(response["verifiedDate"],TARGET)
        self.assertEqual(response["historyCalls"],1)
        self.assertFalse(response["publicationVerified"])
        self.assertEqual(len(self.calls),2)

    def test_paid_failure_must_reconcile(self):
        self.configure()
        self.code = 2
        self.receipt["status"] = "partial"
        self.assertEqual(self.call()["status"],"uncertain")
        self.assertEqual(len(self.calls),2)

    def test_does_not_accept_non_private_application_settings(self):
        self.configure()
        (self.root/"m2-worker.json").chmod(0o644)
        self.assertEqual(self.call()["status"],w.SAFE)
        self.assertFalse(self.calls)

    def test_scheduler_records_private_success_and_does_not_retry(self):
        self.configure()
        calendar=load_calendar(year=2026)
        def fake_outer(args,**kw):
            out=w.result_for(args[2],args[4],Path(args[6]),run=self.fake_run)
            return subprocess.CompletedProcess(args,0,json.dumps(out),"")
        worker=Path("/not-executed/m2_mini_worker.py")
        slot=lambda hour: dt.datetime(2026,11,16,hour,45,tzinfo=ZONE)
        logged=tick(slot(16),calendar,self.root,worker,True,run=fake_outer)
        self.assertEqual(logged["status"],w.LOCAL)
        self.assertFalse(logged["publicationVerified"])
        self.assertEqual(tick(slot(17),calendar,self.root,worker,True,run=fake_outer)["status"],"already_attempted")
        self.assertEqual(len(self.calls),2)

    def test_scheduler_never_accepts_midday_or_unscoped_private_success(self):
        calendar=load_calendar(year=2026)
        worker=Path("/not-executed/m2_mini_worker.py")
        for hour,minute,session,scope in [(12,7,"midday",w.SCOPE),(16,45,"close","wrong")]:
            with tempfile.TemporaryDirectory() as alt:
                def fake_outer(args,**kw):
                    out = dict(status=w.LOCAL,targetDate=TARGET,verifiedDate=TARGET,
                               publicationVerified=False,historyCalls=1,session=session,scope=scope)
                    return subprocess.CompletedProcess(args,0,json.dumps(out),"")
                now = dt.datetime(2026,11,16,hour,minute,tzinfo=ZONE)
                self.assertEqual(tick(now,calendar,Path(alt),worker,True,run=fake_outer)["status"],"uncertain")


if __name__ == "__main__":
    unittest.main()
