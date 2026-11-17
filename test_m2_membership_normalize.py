import unittest
from m2_incremental import SECTORS
from m2_membership_normalize import exact_membership, numeric_code


class ExactMembershipTests(unittest.TestCase):
    def setUp(self):
        self.day='2026-11-11'
        self.archive=[]
        self.b=[]
        n=1
        for sector,count in SECTORS.items():
            rows=[]
            for j in range(count):
                code=f'{n:06d}'
                if sector=='光伏设备' and j==0: code='920167'
                name='*ST名只用于展示' if j==1 else f'Security-{n}'
                self.archive.append(dict(code=code,bars=330,asOfDate=self.day,sha256='0'*64))
                rows.append(dict(stock_code=f'{int(code)}.0',stock_name=name,date=self.day,industry=sector))
                n+=1
            self.b.append(dict(date=self.day,industry=sector,data=rows))

    def test_exact_union_and_risk_unknown(self):
        result=exact_membership(self.archive,self.b,self.day)
        got=result['securities']
        self.assertEqual(len(got),360)
        self.assertTrue(all(x['risk']=='unknown' for x in got))
        self.assertEqual(next(x for x in got if x['code']=='920167.BJ')['sector'],'光伏设备')

    def test_correct_count_wrong_union_fails(self):
        self.b[0]['data'][0]['stock_code']='999991'
        with self.assertRaisesRegex(ValueError,'union differs'):
            exact_membership(self.archive,self.b,self.day)

    def test_duplicate_or_mixed_dates_fail(self):
        self.b[0]['data'][0]['date']='2026-11-12'
        with self.assertRaisesRegex(ValueError,'row date'):
            exact_membership(self.archive,self.b,self.day)
        self.b[0]['data'][0]['date']=self.day
        self.b[0]['data'][0]['stock_code']=self.b[1]['data'][0]['stock_code']
        with self.assertRaisesRegex(ValueError,'duplicate identity'):
            exact_membership(self.archive,self.b,self.day)

    def test_fractional_or_null_identity_rejected(self):
        for x in (None, True, '2129.01','2.129e3','-2129','+2129'):
            with self.subTest(x=x), self.assertRaises(ValueError): numeric_code(x)
        self.assertEqual(numeric_code('2129.0'),'002129')
        self.assertEqual(numeric_code('002129'),'002129')
