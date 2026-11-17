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

    def test_explicit_native_null_quarantines_specific_symbol_not_archive(self):
        bad = "603893.SH"
        archived = ffd()
        archived["raw_rows"] += ffd(bad)["raw_rows"]
        archived["raw_rows"][-2]["amt"] = None
        rows, held, keys = b.load_ffd_archive(archived)
        self.assertEqual(len(keys),6)
        self.assertEqual(held[bad],{DATES[-2]:["amt"]})
        self.assertEqual(set(b.load_ffd_rows(archived)),{CODE})
        merged, held, _ = b.merge_ffd_archives([archived],expected_symbols={CODE,bad})
        self.assertEqual(set(merged),{CODE})
        self.assertIn(bad,held)
        with self.assertRaisesRegex(ValueError,"duplicate"):
            b.merge_ffd_archives([archived,ffd(bad)])
        with self.assertRaisesRegex(ValueError,"identity"):
            b.merge_ffd_archives([archived],expected_symbols={CODE})

    def test_only_exact_overlap_nulls_quarantine_and_older_nulls_are_audited(self):
        solar="002623.SZ"
        archived=ffd(solar)
        outside=dict(archived["raw_rows"][0],time="2026-11-09",volume=None,amt=None)
        archived["raw_rows"].insert(0,outside)
        required=["2026-11-11","2026-11-12","2026-11-13"]
        rows, held, historical = b.merge_ffd_archives([archived],expected_symbols={solar},required_dates=required)
        self.assertEqual(list(rows[solar]),required)
        self.assertEqual(held,{})
        self.assertEqual(historical,{solar:{"2026-11-09":["volume","amt"]}})
        winner,_=b.bridge(tencent(solar),rows[solar],solar,PREV,required_dates=required)
        self.assertIsNone(next(x for x in winner if x["date"]=="2026-11-09")["amount"])
        self.assertTrue(all(x["amount"] is not None for x in winner[-3:]))
        malformed=ffd(solar)
        malformed["raw_rows"].append(dict(outside,trade_currency="USD"))
        with self.assertRaisesRegex(ValueError,"CNY"):
            b.merge_ffd_archives([malformed],required_dates=required)
        with self.assertRaisesRegex(ValueError,"duplicate"):
            b.merge_ffd_archives([archived,dict(archived,raw_rows=[outside])],required_dates=required)
        archived["raw_rows"][-1]["amount"] = 10
        archived["raw_rows"][-1]["amt"] = None
        _, held, historical = b.merge_ffd_archives([archived],required_dates=required)
        self.assertIn(solar,held)
        self.assertIn(solar,historical)

    def test_null_cannot_hide_global_invalid_data(self):
        def partial():
            payload=ffd()
            payload["raw_rows"][0]["amt"]=None
            return payload
        for edit,error in [({"trade_currency":"USD"},"CNY"),({"code":"600000"},"identity"),
                           ({"open":"broken"},"non-null"),({"open":-5},"price"),({"low":110},"OHLC")]:
            original=partial()
            original["raw_rows"][0].update(edit)
            with self.assertRaisesRegex(ValueError,error):
                b.load_ffd_rows(original)
        original=partial()
        original["raw_rows"].append(original["raw_rows"][0].copy())
        with self.assertRaisesRegex(ValueError,"duplicate"):
            b.load_ffd_rows(original)


if __name__ == "__main__":
    unittest.main()
