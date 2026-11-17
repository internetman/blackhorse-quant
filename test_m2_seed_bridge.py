import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import m2_incremental as m
import m2_seed_bridge as b
from test_m2_incremental import DATES, PREV

CODE = "688213.SH"


def tencent(code=CODE, volume=10, cutoff=PREV):
    sym = b.vendor_symbol(code)
    return {"code":0,"data":{sym:{"qfqday":[[d,"10","11","12","9",str(volume)]
                                             for d in DATES if d <= cutoff]}}}


def ffd(code=CODE, volume=1000):
    return {"code":200,"adjustment_execution":{"requested":"qfq","effective":"qfq"},"field_metadata":{"volume":{"unit":"shares","scale":1},
            "amt":{"unit":"CNY","scale":1}},"raw_rows":[
             {"time":d,"code":code,"open":10,"close":11,"high":12,"low":9,"volume":volume,"amt":40000,
              "trade_currency":"CNY"} for d in DATES[-3:]]}


class Tests(unittest.TestCase):
    def test_lot_conversion_and_true_overlap_amount(self):
        rows,evidence=b.bridge(tencent(),b.load_ffd_rows(ffd())[CODE],CODE,PREV)
        self.assertEqual((len(rows),evidence["volumeScale"]),(320,100))
        self.assertTrue(all(r["volume"]==1000 for r in rows))
        self.assertTrue(all(r["amount"] is None for r in rows[:-3]))
        self.assertTrue(all(r["amount"]==40000 for r in rows[-3:]))

    def test_explicit_qfq_and_unambiguous_volume_units(self):
        eviction=tencent()
        eviction["data"]["sh688213"]["day"]=eviction["data"]["sh688213"].pop("qfqday")
        with self.assertRaisesRegex(ValueError,"qfq"):
            b.bridge(eviction,b.load_ffd_rows(ffd())[CODE],CODE,PREV)
        with self.assertRaisesRegex(ValueError,"volume units"):
            b.bridge(tencent(volume=0),b.load_ffd_rows(ffd(volume=0))[CODE],CODE,PREV)

    def test_rejects_basis_identity_and_ohlc_mismatch(self):
        altered=ffd()
        altered["adjustment_execution"]["effective"]="none"
        with self.assertRaisesRegex(ValueError,"qfq"):
            b.load_ffd_rows(altered)
        altered=ffd()
        altered["raw_rows"][1]["open"]=10.01
        with self.assertRaisesRegex(ValueError,"OHLC disagree"):
            b.bridge(tencent(),b.load_ffd_rows(altered)[CODE],CODE,PREV)

    def test_risk_cannot_be_inferred_from_name(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(b,"SECTORS",{"半导体":1}), patch.object(m,"SECTORS",{"半导体":1}):
            root=Path(tmp)
            (root/f"{CODE}.json").write_text(json.dumps(tencent()))
            overlap=root/"overlap.json"
            overlap.write_text(json.dumps({"result":{"content":[{"text":json.dumps(ffd())}]}}))
            manifest={"membershipSource":"fixture universe","membershipDate":PREV,"securities":[
                {"code":CODE,"sector":"半导体","name":"思特威","risk":"eligible"}]}
            seed,r,_,_=b.build(manifest,PREV,root,[overlap])
            self.assertEqual(r["bridged"],1)
            self.assertEqual(seed["securities"][0]["risk"],"unknown")
            self.assertFalse(r["canReachCoverageGate"])
            manifest["securities"][0].update(riskAsOf=PREV,riskEvidence="fixture verified listing status")
            seed,r,_,_=b.build(manifest,PREV,root,[overlap])
            self.assertTrue(r["canReachCoverageGate"])
            self.assertEqual(seed["securities"][0]["riskAsOf"],PREV)


if __name__ == "__main__":
    unittest.main()
