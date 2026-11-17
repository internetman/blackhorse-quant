import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
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

    def test_multi_symbol_batch_is_single_thread_paced(self):
        report=self.execute(execute=True)
        self.assertEqual((report["requestsMade"],report["validatedNew"]),(2,2))
        self.assertEqual(self.delays,[t.REQUEST_INTERVAL])


if __name__=="__main__":
    unittest.main()
