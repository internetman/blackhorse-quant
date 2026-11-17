import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import m2_incremental as m
import m2_risk_snapshot as r

DAY="2026-11-16"
SH,STAR,SZ,OTHER="603893.SH","688213.SH","300001.SZ","000001.SZ"


def evidence(board,role,codes,**change):
    host="www.sse.com.cn" if board.startswith("SH") else "www.szse.cn"
    return dict(codes=codes,receipt=dict(dict(source="https://"+host+"/edition",sourceDate=DAY,
                board=board,role=role,complete=True,sourceVersion="fixture",
                reviewedBy="fixture review",recordCount=len(codes),originalArtifactSha256="0"*64),**change))


class Tests(unittest.TestCase):
    def setUp(self):
        p=patch.object(m,"SECTORS",{"半导体":4})
        p.start()
        self.addCleanup(p.stop)
        self.manifest=dict(membershipSource="fixture",membershipDate=DAY,securities=[
          dict(code=c,name="普通简称",sector="半导体",risk="eligible") for c in (SH,STAR,SZ,OTHER)])

    def test_dated_complete_normal_board_and_positive_risk_partial_board(self):
        sources={"SH-main":{role:evidence("SH-main",role,[SH] if role=="active" else [])
                             for role in r.ROLES},
                 "SH-star":{"warning":evidence("SH-star","warning",[STAR])},
                 "SZ-gem":{"active":evidence("SZ-gem","active",[SZ])}}
        out=r.build(self.manifest,DAY,sources)
        self.assertEqual(out["statuses"],{SH:"eligible",STAR:"excluded",SZ:"unknown",OTHER:"unknown"})
        self.assertEqual(out["coverageBySector"],{"半导体":{"eligible":1,"excluded":1,"unknown":2}})

    def test_reject_later_or_wrong_board_evidence(self):
        board="SH-star"
        with self.assertRaisesRegex(ValueError,"date"):
            r.build(self.manifest,DAY,{board:{"active":evidence(board,"active",[STAR],sourceDate="2026-11-17")}})
        with self.assertRaisesRegex(ValueError,"wrong board"):
            r.build(self.manifest,DAY,{board:{"active":evidence(board,"active",[SH])}})
        with self.assertRaisesRegex(ValueError,"official"):
            r.build(self.manifest,DAY,{board:{"active":evidence(board,"active",[STAR],source="https://elsewhere.invalid")}})

    def test_sz_pages_date_and_total(self):
        def page(n,code):
            return [{"metadata":dict(tabkey="tab1",catalogid="fxjsb",subname=DAY+" ",
                     pagesize=1,pagecount=2,recordcount=2,pageno=n),"data":[{"zqdm":code}]}]
        self.assertEqual(r.codes_from_szse_pages([page(1,"000001"),page(2,"300001")],"warning",DAY),{OTHER,SZ})
        with self.assertRaisesRegex(ValueError,"missing pages"):
            r.codes_from_szse_pages([page(1,"000001")],"warning",DAY)
        with self.assertRaisesRegex(ValueError,"target"):
            r.codes_from_szse_pages([page(1,"000001")],"warning","2026-11-17")
        with self.assertRaisesRegex(ValueError,"date"):
            r.codes_from_szse_pages([[{"metadata":{"tabkey":"tab2","catalogid":"fxjsb","subname":""},
                                       "data":[]}]],"arrangement",DAY)

    def test_verify_original_checksum_before_private_export(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            raw=root/"official.json"
            raw.write_text("{}")
            doc=evidence("SH-star","active",[STAR],originalArtifact="official.json",
                         originalArtifactSha256=hashlib.sha256(raw.read_bytes()).hexdigest())
            src={"SH-star":{"active":doc}}
            r.verify_archived_artifacts(src,root)
            raw.write_text("changed")
            with self.assertRaisesRegex(ValueError,"checksum"):
                r.verify_archived_artifacts(src,root)


if __name__=="__main__":
    unittest.main()
