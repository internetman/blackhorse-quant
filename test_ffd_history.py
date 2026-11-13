import copy
import datetime as dt
import json
from pathlib import Path
import tempfile
import io
import urllib.error
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
            files=list(Path(self.temp.name).glob('[0-9a-f]'*64+'.json'));self.assertEqual(len(files),1)
            receipt=json.loads(files[0].read_text());self.assertEqual(receipt['state'],'pending')
            self.assertEqual(receipt['clientRequestId'],kwargs['headers']['X-Request-ID'])
            self.assertEqual(kwargs['headers']['X-Request-ID'],kwargs['headers']['X-FFD-Client-Request-ID'])
            self.assertNotIn('secret',files[0].read_text())
            raise TimeoutError('secret')
        c=self.client(4,api_key='secret',post=fail)
        with self.assertRaisesRegex(ValueError,'TimeoutError'):c.history('600000.SH','2026-11-11','2026-11-12')
        receipt=json.loads(next(Path(self.temp.name).glob('[0-9a-f]'*64+'.json')).read_text())
        self.assertEqual(receipt['state'],'unknown');self.assertEqual(receipt['exceptionType'],'TimeoutError')
        post=Mock();new=self.client(4,api_key='secret',post=post)
        with self.assertRaisesRegex(ValueError,'existing attempt'):new.history('600000.SH','2026-11-11','2026-11-12')
        post.assert_not_called()
    def test_http_status_retained_without_message(self):
        response=Mock(status_code=503);response.raise_for_status.side_effect=RuntimeError('secret')
        c=self.client(4,api_key='secret',post=Mock(return_value=response))
        with self.assertRaises(ValueError):c.history('600000.SH','2026-11-11','2026-11-12')
        receipt=json.loads(next(Path(self.temp.name).glob('[0-9a-f]'*64+'.json')).read_text())
        self.assertEqual(receipt['httpStatus'],503);self.assertNotIn('secret',json.dumps(receipt))
    def test_native_rest_does_not_require_mcp_annotations(self):
        p=payload();p['coverage']={'complete':True,'status':'complete','requested_codes':['600000.SH'],'missing_cell_count':0}
        self.assertEqual(self.parse(p)[-1]['close'],10.21)
        p['data']['code'][0]='000001.SH'
        with self.assertRaises(ValueError):self.parse(p)
    def test_urllib_wire_matches_public_rest_contract_offline(self):
        from ffd_history import _urllib_post, ENDPOINT, _NoRedirect
        response=Mock(status=200,headers={});response.read.return_value=b'{"code":200}'
        response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False)
        opener=Mock();opener.open.return_value=response
        body={'function':'history','codes':'600000.SH','indicators':'close,volume','options':'CPS:2','start_date':'2026-11-11','end_date':'2026-11-12','coverage_policy':'strict'}
        with patch('ffd_history.urllib.request.build_opener',return_value=opener):
            r=_urllib_post(ENDPOINT,headers={'Authorization':'Bearer offline','Content-Type':'application/json'},json=body,timeout=(10,180))
        request=opener.open.call_args.args[0]
        self.assertEqual(request.full_url,'https://ffd.findesk.cn/api/query');self.assertEqual(request.get_method(),'POST')
        self.assertEqual(json.loads(request.data),body);self.assertEqual(r.json(),{'code':200})
        self.assertIsNone(_NoRedirect().redirect_request(None,None,302,'',{},'https://elsewhere.invalid'))
    def test_structured_http_error_preserves_safe_contract(self):
        body={'detail':{'error_code':'HISTORY_DATA_INCONSISTENT','request_id':'service-123','data_charge_status':'not_charged','message':'secret'}}
        error=urllib.error.HTTPError('https://ffd.findesk.cn/api/query',422,'secret',{},io.BytesIO(json.dumps(body).encode()))
        c=self.client(4,api_key='secret',post=Mock(side_effect=error))
        with self.assertRaisesRegex(ValueError,'HTTP 422'):c.history('600000.SH','2026-11-11','2026-11-12')
        receipt=json.loads(next(Path(self.temp.name).glob('[0-9a-f]'*64+'.json')).read_text())
        self.assertEqual(receipt['state'],'http_error');self.assertEqual(receipt['httpStatus'],422)
        self.assertEqual(receipt['errorCode'],'HISTORY_DATA_INCONSISTENT');self.assertEqual(receipt['serviceRequestId'],'service-123')
        self.assertEqual(receipt['dataChargeStatus'],'not_charged');self.assertNotIn('secret',json.dumps(receipt))
    def test_failed_validation_preserves_paid_response_before_parser(self):
        value=payload();value['coverage']['complete']=False;value['quota_used']=4
        value['debug']='reflected secret';value['headers']={'Authorization':'Bearer secret'}
        response=Mock(status_code=200);response.json.return_value=value
        c=self.client(4,api_key='secret',post=Mock(return_value=response))
        with self.assertRaisesRegex(ValueError,'validation failed'):c.history('600000.SH','2026-11-11','2026-11-12')
        receipt=json.loads(next(Path(self.temp.name).glob('[0-9a-f]'*64+'.json')).read_text())
        self.assertEqual(receipt['state'],'validation_failed')
        text=(Path(self.temp.name)/receipt['responseFile']).read_text();saved=json.loads(text)
        self.assertEqual(saved['data']['close'],[10.17,10.21]);self.assertEqual(saved['quota_used'],4)
        self.assertNotIn('secret',text);self.assertNotIn('headers',saved)
        self.assertEqual(saved['debug'],'reflected [REDACTED]')
    def test_missing_source_coverage_requires_exact_calendar_matrix(self):
        p=payload();p.pop('coverage')
        with self.assertRaisesRegex(ValueError,'calendar proof'):self.parse(p)
        expected=['2026-11-11','2026-11-12']
        rows=parse_history(p,'600000.SH','2026-11-11','2026-11-12',expected_dates=expected)
        self.assertEqual(len(rows),2);self.assertNotIn('coverage',p)
        with self.assertRaisesRegex(ValueError,'calendar coverage gap'):
            parse_history(p,'600000.SH','2026-11-10','2026-11-12',expected_dates=['2026-11-10']+expected)
        p['coverage']={'complete':False}
        with self.assertRaises(ValueError):parse_history(p,'600000.SH','2026-11-11','2026-11-12',expected_dates=expected)
    def test_many_rows_do_not_hide_missing_calendar_session(self):
        start=dt.date(2026,8,1);dates=[(start+dt.timedelta(days=i)).isoformat() for i in range(70)]
        p=payload();p.pop('coverage');p['data']={'time':list(dates),'code':['600000.SH']*70,'close':[10.0]*70,'volume':[100]*70}
        for key in p['data']:p['data'][key].pop(35)
        with self.assertRaisesRegex(ValueError,'calendar coverage gap'):
            parse_history(p,'600000.SH',dates[0],dates[-1],expected_dates=dates)
    def test_unadjusted_index_omits_legacy_cps1(self):
        p=payload();p['data']['code']=['000001.SH']*2
        p['coverage']['returned_codes']=['000001.SH'];p['adjustment_execution']={'requested':'none','effective':'none'}
        response=Mock(status_code=200);response.json.return_value=p;post=Mock(return_value=response)
        c=self.client(4,api_key='secret',post=post)
        c.history('000001.SH','2026-11-11','2026-11-12',index=True)
        self.assertEqual(post.call_args.kwargs['json']['options'],'')
        p['adjustment_execution']['effective']='qfq'
        with self.assertRaises(ValueError):parse_history(p,'000001.SH','2026-11-11','2026-11-12',index=True)
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
