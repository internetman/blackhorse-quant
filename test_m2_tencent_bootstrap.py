import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import parse_qs,urlsplit

import m2_tencent_bootstrap as t
import m2_incremental as m
from test_m2_seed_bridge import tencent, ffd
from test_m2_incremental import PREV,NOW,CAL

SECTOR="半导体"
A,B="688213.SH","603893.SH"


class Tests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.state=Path(tmp.name)
        self.overlap=self.state/"private-ffd.json"
        base=ffd(A)
        base["raw_rows"] += ffd(B)["raw_rows"]
        self.overlap.write_text(json.dumps(base))
        self.manifest=dict(membershipSource="fixture",membershipDate=PREV,
                           securities=[dict(code=c,name="公开名",sector=SECTOR,risk="eligible") for c in (A,B)])
        self.calls=[]
        self.delays=[]
        for mod in (t,m):
            p=patch.object(mod,"SECTORS",{SECTOR:2})
            p.start()
            self.addCleanup(p.stop)

    def fetch(self,url):
        self.calls.append(url)
        sym=parse_qs(urlsplit(url).query)["param"][0].split(",")[0]
        return tencent(sym[2:]+".SH")

    def execute(self,**opts):
        args=dict(limit=2,fetch=self.fetch,sleep=self.delays.append)
        args.update(opts)
        return t.run(self.state,PREV,self.manifest,[self.overlap],CAL,NOW,**args)

    def test_plan_only_never_calls_or_creates_files(self):
        report=self.execute()
        self.assertEqual(report["planned"],2)
        self.assertEqual(report["qualifiedRiskAtSeedCutoffBySector"],{SECTOR:0})
        self.assertEqual(report["ffdCalls"],0)
        self.assertEqual(self.calls,[])
        self.assertEqual(list(self.state.iterdir()),[self.overlap])

    def test_single_capped_request_uses_exact_host_native_shape_and_reuses(self):
        first=self.execute(execute=True,limit=1,codes=[A])
        self.assertEqual((first["requestsMade"],first["validatedNew"]),(1,1))
        req = urlsplit(self.calls[0])
        self.assertEqual((req.scheme,req.netloc,req.path),("https","web.ifzq.gtimg.cn","/appstock/app/fqkline/get"))
        self.assertEqual(parse_qs(req.query),{"param":["sh688213,day,,2026-11-13,340,qfq"]})
        prior=json.loads((self.state/f"tencent-{PREV}"/f"{A}.json").read_text())
        self.assertEqual(prior["sha256"],t.digest(prior["response"]))
        self.assertEqual(len(prior["response"]["data"]["sh688213"]["qfqday"][0]),6)
        again=self.execute(execute=True,limit=1,codes=[A])
        self.assertEqual((again["reused"],again["requestsMade"]),(1,0))
        self.assertEqual(len(self.calls),1)

    def test_mismatch_stops_and_persists_hold_no_retry(self):
        def wrong_basis(url):
            self.calls.append(url)
            return {"code":0,"data":{"sh603893":{"day":[]}}}
        result=self.execute(execute=True,fetch=wrong_basis)
        self.assertEqual(result["status"],"held_provider_or_validation")
        self.assertEqual(result["requestsMade"],1)
        again=self.execute(execute=True)
        self.assertEqual(again["status"],"held_saved_attempt_requires_reconciliation")
        self.assertEqual(result["failureReason"],"explicit_qfq_missing")
        other=self.execute(execute=True,limit=1,codes=[A])
        self.assertEqual(other["status"],"held_saved_attempt_requires_reconciliation")
        self.assertEqual(other["globalReconciliationHolds"],1)
        self.assertEqual(len(self.calls),1)

    def test_provider_data_gaps_and_invalid_stock_are_rejected(self):
        with self.assertRaisesRegex(ValueError,"frozen scope"):
            self.execute(codes=["600000.SH"],execute=True)
        def truncated(url):
            original=self.fetch(url)
            for value in original["data"].values():
                value["qfqday"].pop(2)
            return original
        result=self.execute(execute=True,limit=1,codes=[A],fetch=truncated)
        self.assertEqual(result["status"],"held_provider_or_validation")
        self.assertEqual(result["validatedNew"],0)
        self.assertEqual(result["failureReason"],"history_trading_dates")

    def test_multi_symbol_batch_is_single_thread_paced(self):
        report=self.execute(execute=True)
        self.assertEqual((report["requestsMade"],report["validatedNew"]),(2,2))
        self.assertEqual(self.delays,[t.REQUEST_INTERVAL])

    def test_archive_quarantine_removes_only_impacted_symbol_from_canary_plan(self):
        original=json.loads(self.overlap.read_text())
        original["raw_rows"][-1]["amt"]=None
        self.overlap.write_text(json.dumps(original))
        canary=self.execute(execute=True,limit=1,codes=[A])
        self.assertEqual(canary["ffdQuarantinedSymbolCount"],1)
        self.assertEqual(canary["validatedNew"],1)
        self.assertFalse(canary["theoreticalHistoryGatePossible"])
        held=self.execute(execute=True,limit=1,codes=[B])
        self.assertEqual(held["status"],"no_verified_bootstrap_candidates")
        self.assertEqual(held["requestsMade"],0)

    def test_out_of_window_solar_shape_is_verified_and_privately_audited(self):
        original=json.loads(self.overlap.read_text())
        older=dict(original["raw_rows"][-1],time="2026-11-09",volume=None,amt=None)
        original["raw_rows"].append(older)
        self.overlap.write_text(json.dumps(original))
        preview=self.execute(limit=1,codes=[B])
        self.assertEqual(preview["requiredOverlapDates"],["2026-11-11","2026-11-12","2026-11-13"])
        self.assertEqual(preview["ffdOutOfWindowNullRowCount"],1)
        self.assertEqual(preview["ffdQuarantinedSymbolCount"],0)
        self.assertTrue(preview["theoreticalHistoryGatePossible"])
        self.assertEqual(self.calls,[])
        self.assertFalse((self.state/f"tencent-receipts-{PREV}").exists())
        actual=self.execute(execute=True,limit=1,codes=[B])
        self.assertEqual(actual["validatedNew"],1)
        audit=json.loads((self.state/f"tencent-receipts-{PREV}"/"archive-null-audit.json").read_text())
        self.assertEqual(audit["outsideWindow"],{B:{"2026-11-09":["volume","amt"]}})
        self.assertEqual(audit["inWindow"],{})

    def test_finite_transport_failure_never_exposes_payload_or_charges(self):
        marker="SHOULD-NOT-LEAVE-PROVIDER-ERROR"
        def throttled(url):
            self.calls.append(url)
            raise HTTPError(url,429,marker,{'authorization':'SECRET_HEADER'},None)
        result=self.execute(execute=True,limit=1,codes=[A],fetch=throttled)
        receipt=(self.state/f"tencent-receipts-{PREV}"/f"{A}.json").read_text()
        self.assertIn("provider_http_rate_limited",receipt)
        self.assertEqual(result["failureReason"],"provider_http_rate_limited")
        self.assertNotIn(marker,receipt+json.dumps(result))
        self.assertNotIn("SECRET_HEADER",receipt+json.dumps(result))
        self.assertEqual(result["ffdPointsUsed"],0)
        self.assertEqual(len(self.calls),1)

    def test_legacy_hold_cannot_be_skipped_by_requesting_a_different_symbol(self):
        directory=self.state/f"tencent-receipts-{PREV}"
        directory.mkdir(mode=0o700)
        path=directory/f"{B}.json"
        old=json.dumps(dict(code=B,cutoff=PREV,state="reconciliation_needed",exceptionType="ValueError"))
        path.write_text(old)
        result=self.execute(execute=True,limit=1,codes=[A])
        self.assertEqual(result["globalReconciliationHolds"],1)
        self.assertEqual(result["status"],"held_saved_attempt_requires_reconciliation")
        self.assertFalse(self.calls)
        self.assertEqual(path.read_text(),old)

    def test_native_validation_reasons_are_specific_without_values(self):
        report=self.execute()
        self.assertEqual(report["requestsMade"],0)
        native=self.fetch(t.request_url(A,PREV))
        overlap=t.prepare(self.manifest,PREV,[self.overlap],CAL,NOW)
        evidence,_,_,required,_,_=overlap
        rows=native["data"]["sh688213"]["qfqday"]
        original=rows[-1][:]
        rows[-1][1]="10.01"
        for field,value,expected in ((1,"10.01","overlap_ohlc_mismatch"),
                                     (5,"5555","overlap_volume_units"),
                                     (0,"2026-11-13 SECRET","history_trading_dates")):
            rows[-1][:]=original
            rows[-1][field]=value
            with self.assertRaises(t.BridgeValidationError) as caught:
                t.validated_history(native,evidence[A],A,PREV,CAL,required)
            self.assertEqual(t.failure_reason(caught.exception,"validate"),expected)
            if field==0:
                self.assertNotIn("SECRET",str(caught.exception))


if __name__=="__main__":
    unittest.main()
