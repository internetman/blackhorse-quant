import json
import unittest

from m2_public_projection import build, SCOPE
from m2_incremental import SECTORS


class ProjectionTests(unittest.TestCase):
    def fixtures(self):
        self.date = "2026-11-16"
        self.n = sum(SECTORS.values())
        self.run = dict(status="candidate_ready",asOfDate=self.date,stopUncertain=False,
                        sectorValid=SECTORS.copy(),valid=self.n,expected=self.n,secret="private")
        self.review = dict(schemaVersion=1,mode="derived-pilot",runStatus="success",barStatus="completed",
                           asOfDate=self.date, candidateCount=1, candidates=[
                               dict(code="600000",name="测试",stage="S2",position="S2正常",asOfDate=self.date,
                                    price=10,reason="hidden",pivot=12)],
                           universe=dict(scopeId=SCOPE,valid=self.n,total=self.n,
                                         sectors=[dict(name=k,valid=v,total=v) for k,v in SECTORS.items()]),
                           diagnostic="secret-file")

    def test_rebuilds_review_without_raw_fields(self):
        self.fixtures()
        result = build(self.run,self.review,self.date)
        raw = json.dumps(result,ensure_ascii=False)
        for private in ("price","hidden","pivot","secret-file","diagnostic","private"):
            self.assertNotIn(private,raw)
        self.assertEqual(result["mode"],"derived-pilot")
        self.assertEqual(result["candidateCount"],1)
        self.assertEqual(result["candidates"][0]["code"],"600000")

    def test_explicit_succeeded_zero(self):
        self.fixtures()
        self.review.update(candidateCount=0,candidates=[])
        self.assertEqual(build(self.run,self.review,self.date)["candidateCount"],0)

    def test_rejects_incomplete_stale_and_nonpilot(self):
        for patch in [dict(stopUncertain=True),dict(status="partial"),dict(asOfDate="2026-11-13"),
                      dict(sectorValid={**SECTORS,"电子化学品":20}),dict(valid=12)]:
            self.fixtures()
            self.run.update(patch)
            with self.assertRaises(ValueError):
                build(self.run,self.review,self.date)
        self.fixtures()
        self.review["mode"]="close"
        with self.assertRaises(ValueError):
            build(self.run,self.review,self.date)

    def test_rejects_duplicates(self):
        self.fixtures()
        self.review["candidates"]*=2
        self.review["candidateCount"]=2
        with self.assertRaises(ValueError):
            build(self.run,self.review,self.date)
