"""The frozen pilot includes BSE, but current adapters cannot screen that venue."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import m2_incremental as m
import m2_risk_snapshot as r
import m2_seed_bridge as b
import m2_tencent_bootstrap as t
from test_m2_incremental import CAL, DATES, NOW, PREV, TARGET, bar
from test_m2_seed_bridge import ffd, tencent

BJ,SECTOR="920167.BJ","光伏设备"


class BJTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.state=Path(tmp.name)
        sectors={SECTOR:20}
        for mod in (m,b,t):
            p=patch.object(mod,"SECTORS",sectors)
            p.start()
            self.addCleanup(p.stop)
        self.codes=[f"6000{i:02}.SH" for i in range(19)]
        self.securities=[dict(code=c,name="参考简称",sector=SECTOR,risk="eligible",
              riskAsOf=TARGET,riskEvidence="fixture") for c in [*self.codes,BJ]]
        self.manifest=dict(membershipSource="test original freeze",membershipDate=PREV,
                       securities=self.securities)
        self.receive=ffd()
        self.receive["raw_rows"]=sum((ffd(c)["raw_rows"] for c in [*self.codes,BJ]),[])
        self.ffd=self.state/"original-ffd.json"
        self.ffd.write_text(json.dumps(self.receive))

    def test_original_mixed_ffd_scope_does_not_abort_bridge_or_relabel(self):
        self.assertIn(BJ,b.load_ffd_rows(self.receive))
        for c in self.codes:
            (self.state/f"{c}.json").write_text(json.dumps(tencent(c)))
        seed,report,_,omissions=b.build(self.manifest,PREV,self.state,[self.ffd])
        self.assertEqual(len(seed["securities"]),20)
        self.assertEqual(seed["securities"][-1]["code"],BJ)
        self.assertEqual(seed["securities"][-1]["risk"],"unknown")
        self.assertNotIn(BJ,seed["histories"])
        self.assertEqual(omissions[BJ],m.UNVERIFIED_VENUE)
        self.assertTrue(report["canReachHistoricalGate"])
        self.assertEqual(report["heldUnverifiedVenue"],1)

    def test_private_run_refuses_bj_even_with_bars_and_claimed_risk(self):
        seed=dict(schemaVersion=1,adjustment="qfq",volumeUnit="share",amountUnit="CNY",
                  provenance="fixture",membershipDate=PREV,securities=self.securities,
                  histories={c:[bar(d,20+i) for i,d in enumerate(DATES)] for c in [*self.codes,BJ]})
        m.write(self.state/"seed.json",seed)
        m.write(self.state/f"risk-{TARGET}.json",dict(asOfDate=TARGET,evidence="fixture",
                   statuses={c:"eligible" for c in [*self.codes,BJ]}))
        report=m.run(self.state,TARGET,1500,CAL,NOW,plan_only=True)
        self.assertEqual(report["plannedRequests"],19)
        self.assertEqual(report["possiblePerSector"],{SECTOR:19})
        self.assertTrue(report["canReachCoverageGate"])
        self.assertEqual((report["riskUnknown"],report["heldUnverifiedVenue"]),(1,1))

    def test_bj_readable_manifest_but_no_old_source_or_risk_guess(self):
        risk=r.build(self.manifest,TARGET,{})
        self.assertEqual(risk["statuses"][BJ],"unknown")
        self.assertEqual(risk["coverageByBoard"]["BJ-unverified"]["unknown"],1)
        with self.assertRaisesRegex(ValueError,"Shanghai/Shenzhen"):
            t.request_url(BJ,PREV)
        calls=[]
        report=t.run(self.state,PREV,self.manifest,[self.ffd],CAL,NOW,
                     limit=1,execute=True,codes=[BJ],fetch=calls.append)
        self.assertEqual(report["requestsMade"],0)
        self.assertEqual(report["heldUnverifiedVenue"],1)
        self.assertEqual(calls,[])


if __name__=="__main__":
    unittest.main()
