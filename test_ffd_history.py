import copy
import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from ffd_history import HistoryClient, parse_history, EXPERIMENT_SCOPE


def payload():
    return dict(code=200,data=dict(time=['2026-11-11','2026-11-12'],code=['600000.SH']*2,
                                  close=[10.17,10.21],volume=[100,200]),
                coverage=dict(complete=True,returned_codes=['600000.SH'],code_identity_checked=True),
                adjustment_execution=dict(requested='qfq',effective='qfq'))

class FFDTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
    def client(self,*args,**kwargs):
        return HistoryClient(*args,receipt_dir=self.temp.name,**kwargs)
    def parse(self,p):return parse_history(p,'600000.SH','2026-11-01','2026-11-12')
    def test_pending_receipt_written_before_post_and_unknown_blocks_new_client(self):
        def fail(*args,**kwargs):
            files=list(Path(self.temp.name).glob('*.json'));self.assertEqual(len(files),1)
            receipt=json.loads(files[0].read_text());self.assertEqual(receipt['state'],'pending')
            self.assertEqual(receipt['clientRequestId'],kwargs['headers']['X-Request-ID'])
            self.assertEqual(kwargs['headers']['X-Request-ID'],kwargs['headers']['X-FFD-Client-Request-ID'])
            self.assertNotIn('secret',files[0].read_text())
            raise TimeoutError('secret')
        c=self.client(4,api_key='secret',post=fail)
        with self.assertRaisesRegex(ValueError,'TimeoutError'):c.history('600000.SH','2026-11-11','2026-11-12')
        receipt=json.loads(next(Path(self.temp.name).glob('*.json')).read_text())
        self.assertEqual(receipt['state'],'unknown');self.assertEqual(receipt['exceptionType'],'TimeoutError')
        post=Mock();new=self.client(4,api_key='secret',post=post)
        with self.assertRaisesRegex(ValueError,'existing attempt'):new.history('600000.SH','2026-11-11','2026-11-12')
        post.assert_not_called()
    def test_http_status_retained_without_message(self):
        response=Mock(status_code=503);response.raise_for_status.side_effect=RuntimeError('secret')
        c=self.client(4,api_key='secret',post=Mock(return_value=response))
        with self.assertRaises(ValueError):c.history('600000.SH','2026-11-11','2026-11-12')
        receipt=json.loads(next(Path(self.temp.name).glob('*.json')).read_text())
        self.assertEqual(receipt['httpStatus'],503);self.assertNotIn('secret',json.dumps(receipt))
    def test_valid(self):self.assertEqual(self.parse(payload())[-1]['close'],10.21)
    def test_rejects_wrong_identity_date_adjustment_partial_unknown_and_values(self):
        mutations=[lambda p:p['data']['code'].__setitem__(0,'000001.SH'),
                   lambda p:p['data']['time'].__setitem__(1,'2026-11-13'),
                   lambda p:p['data']['time'].__setitem__(1,'2026-11-11'),
                   lambda p:p['adjustment_execution'].__setitem__('effective','none'),
                   lambda p:p['coverage'].__setitem__('complete',None),
                   lambda p:p['coverage'].__setitem__('partial',True),
                   lambda p:p['coverage'].__setitem__('missing_cells',[{}]),
                   lambda p:p['data']['close'].__setitem__(0,None),
                   lambda p:p['data']['close'].__setitem__(0,float('nan')),
                   lambda p:p['data']['volume'].__setitem__(0,-1),
                   lambda p:p['data']['volume'].__setitem__(0,True)]
        for mutate in mutations:
            p=payload();mutate(p)
            with self.assertRaises(ValueError):self.parse(p)
    def test_budget_reserved_before_post_and_not_retried(self):
        post=Mock(side_effect=RuntimeError('SECRET'))
        c=self.client(10,api_key='SECRET',post=post)
        with self.assertRaisesRegex(ValueError,'unknown') as error:c.history('600000.SH','2026-11-11','2026-11-12')
        self.assertNotIn('SECRET',str(error.exception));self.assertEqual(c.reserved,4)
        with self.assertRaisesRegex(ValueError,'halted'):c.history('600000.SH','2026-11-11','2026-11-12')
        self.assertEqual(post.call_count,1)
    def test_budget_denies_without_network(self):
        post=Mock();c=self.client(3,api_key='x',post=post)
        with self.assertRaisesRegex(ValueError,'budget'):c.history('600000.SH','2026-11-11','2026-11-12')
        post.assert_not_called();self.assertEqual(c.reserved,0)
    def test_request_tls_default_and_no_secrets_in_return(self):
        response=Mock();response.json.return_value=payload();post=Mock(return_value=response)
        c=self.client(4,api_key='secret',post=post);c.history('600000.SH','2026-11-11','2026-11-12')
        kw=post.call_args.kwargs;self.assertNotIn('verify',kw);self.assertEqual(kw['json']['options'],'CPS:2')
        self.assertEqual(kw['json']['coverage_policy'],'strict')
    def test_future_probe_refuses_before_network(self):
        from ffd_breadth_probe import probe
        client=Mock()
        with patch('ffd_breadth_probe.expected_close',return_value='2026-11-12'):
            with self.assertRaises(ValueError):probe('600000.SH','2026-11-13',client=client)
        client.history.assert_not_called()

if __name__=='__main__':unittest.main()
