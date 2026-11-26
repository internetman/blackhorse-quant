"""Four-sector pipeline tests use only synthetic data and a fake quota transport."""
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import m2_incremental as m
from ffd_history import HistoryClient, parse_history

CAL = {"years": {str(i): {"closures": []} for i in (2024, 2025, 2026)}}
NOW = dt.datetime(2026, 11, 17, 9, tzinfo=m.ZONE)
PREV, TARGET = "2026-11-13", "2026-11-16"
DATES = m.days_between("2025-01-02", PREV, CAL)[-320:]
SECTORS = {key: 1 for key in m.SECTORS}


def bar(day, level):
    return dict(date=day, close=level, open=level, high=level+1, low=level-1, volume=1000, amount=100000)


def payload(code, dates, rows):
    return dict(code=200, quota_used=len(dates)*6,
                adjustment_execution=dict(requested="qfq",effective="qfq"),
                coverage=dict(complete=True), data=dict(time=dates, code=[code]*len(dates), **{
                    ("amt" if field=="amount" else field): [row[field] for row in rows]
                    for field in m.FIELDS}))


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name)
        self.patch = patch.object(m, "SECTORS", SECTORS); self.patch.start(); self.addCleanup(self.patch.stop)
        self.securities = [dict(code=f"60000{i}.SH", sector=sector, risk="eligible", riskAsOf=TARGET, riskEvidence="synthetic test",name=f"测试{i}")
                           for i, sector in enumerate(SECTORS)]
        rows = [bar(day, 20+i) for i,day in enumerate(DATES)]
        self.base = dict(schemaVersion=1, adjustment="qfq", volumeUnit="share", amountUnit="CNY",
                         provenance="synthetic test", membershipDate=PREV,
                         securities=self.securities,histories={s["code"]: rows for s in self.securities})
        self.calls = []
        self.write_seed()

    def write_seed(self):
        m.write(self.state/"seed.json", self.base)

    def factory(self, cap, *, receipt_dir):
        outer = self
        class Mock:
            halted, reserved = False, 0
            def history(self, code, start, cutoff, expected_dates, *, fields,reuse_completed):
                outer.calls.append((code,start,cutoff,expected_dates,fields,reuse_completed))
                prev = outer.base["histories"][code][-3:]
                self.reserved += 36
                return [*prev, bar(cutoff, prev[-1]["close"]+1)], {"quota_used":24}
        return Mock()

    def run_local(self, **opts):
        args = dict(state=self.state, cutoff=TARGET, budget=144, calendar=CAL, now=NOW,
                    client_factory=self.factory, plan_only=False)
        args.update(opts)
        return m.run(**args)

    def test_default_plan_has_no_requests_or_files(self):
        r = self.run_local(plan_only=True)
        self.assertEqual((r["plannedRequests"],r["worstCasePoints"]), (4,144))
        self.assertEqual(self.calls,[])
        self.assertEqual(list(self.state.glob("*.json")), [self.state/"seed.json"])

    def test_idempotent_incremental_and_derived_only(self):
        r = self.run_local()
        self.assertEqual((r["status"],r["valid"],r["reportedSuccessPoints"]), ("candidate_ready",4,96))
        self.assertEqual({tuple(x[3]) for x in self.calls}, {(*DATES[-3:],TARGET)})
        result = json.loads((self.state/f"derived-{TARGET}.json").read_text())
        self.assertEqual((result["mode"],result["universe"]["scopeId"]), ("derived-pilot","four-sector-close-v1"))
        self.assertTrue(all("复权事件" in p["pendingChecks"] for p in result["candidates"]))
        self.assertTrue(all(set(p) == {"code","name","asOfDate","stage","position","reasons","pendingChecks"}
                            for p in result["candidates"]))
        self.assertEqual(self.run_local()["plannedRequests"],0)
        self.assertEqual(len(self.calls),4)

    def test_fail_if_budget_or_seed_cannot_reach_gate(self):
        with self.assertRaisesRegex(ValueError,"exceeds cap"):
            self.run_local(budget=143)
        self.base["histories"].pop(self.securities[0]["code"])
        self.write_seed()
        with self.assertRaisesRegex(ValueError,"coverage"):
            self.run_local()
        self.assertEqual(self.calls,[])

    def test_target_and_overlap_mismatch(self):
        for day in ("2026-11-15", "2026-11-17"):
            with self.assertRaisesRegex(ValueError,"completed trading date"):
                self.run_local(cutoff=day)
        with self.assertRaisesRegex(ValueError,"price basis"):
            m.reconcile([bar(d,20) for d in DATES[-3:]], [*[bar(d,25) for d in DATES[-3:]],bar(TARGET,26)])

    def test_unknown_risk_is_not_counted_as_screened(self):
        self.base["securities"][0]["risk"] = "unknown"
        self.write_seed()
        plan = self.run_local(plan_only=True)
        self.assertEqual(plan["riskUnknown"], 1)
        self.assertFalse(plan["canReachCoverageGate"])
        self.assertEqual(self.calls, [])

    def test_unreconciled_ledger_blocks_new_requests(self):
        ledger = self.state/"receipts"
        ledger.mkdir()
        m.write(ledger/"test.json", {"state": "pending"})
        plan = self.run_local(plan_only=True)
        self.assertTrue(plan["canReachCoverageGate"])
        with self.assertRaisesRegex(ValueError,"unreconciled attempt"):
            self.run_local()
        self.assertEqual(self.calls, [])

    def test_missing_historical_calendar_refuses_without_network(self):
        no_2025 = {"years": {"2026":{"closures":[]}}}
        assert DATES[0].startswith("2025")
        plan = self.run_local(calendar=no_2025,plan_only=True)
        self.assertFalse(plan["canReachCoverageGate"])
        self.assertEqual(self.calls, [])

    def test_nullable_older_amount_does_not_weaken_overlap(self):
        rows = [dict(bar(d,20+i), amount=None if i < len(DATES)-3 else 1000)
                for i,d in enumerate(DATES)]
        with self.assertRaisesRegex(ValueError,"historical field"):
            m.valid_rows(rows)
        self.assertEqual(m.valid_rows(rows,permit_older_missing_amount=True), rows)
        rows[-3]["amount"] = None
        with self.assertRaisesRegex(ValueError,"historical field"):
            m.valid_rows(rows,permit_older_missing_amount=True)

    def test_stale_risk_requires_target_day_document(self):
        for sec in self.base["securities"]:
            sec["riskAsOf"] = PREV
        self.write_seed()
        report = self.run_local(plan_only=True)
        self.assertFalse(report["canReachCoverageGate"])
        self.assertEqual(report["riskUnknown"],4)
        m.write(self.state/f"risk-{TARGET}.json", dict(asOfDate=TARGET,evidence="fixture source",
            statuses={s["code"]:"eligible" for s in self.base["securities"]}))
        self.assertTrue(self.run_local(plan_only=True)["canReachCoverageGate"])

    def test_vendor_uses_amt_and_ledger_reuse(self):
        code = self.securities[0]["code"]
        dates = [PREV,TARGET]
        rows = [bar(PREV,25),bar(TARGET,26)]
        data = payload(code,dates,rows)
        class Response:
            status_code = 200
            def raise_for_status(self): pass
            def json(self): return data
        def post(url,headers,json,timeout):
            self.calls.append(json)
            return Response()
        ledger = self.state/"receipts"
        c = HistoryClient(30,api_key="fake-key",post=post,receipt_dir=ledger)
        observed,_ = c.history(code,PREV,TARGET,expected_dates=dates,fields=m.FIELDS,reuse_completed=True)
        self.assertEqual(self.calls[0]["indicators"],"open,high,low,close,volume,amt")
        self.assertEqual(observed,rows)
        c2 = HistoryClient(1,api_key="fake-key",post=post,receipt_dir=ledger)
        self.assertTrue(c2.history(code,PREV,TARGET,expected_dates=dates,fields=m.FIELDS,reuse_completed=True)[1]["_ledgerReused"])
        self.assertEqual(len(self.calls),1)
        self.assertEqual(c2.reserved,0)
        self.assertEqual(parse_history(data,code,PREV,TARGET,expected_dates=dates,fields=m.FIELDS),rows)


if __name__ == "__main__":
    unittest.main()
