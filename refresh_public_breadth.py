"""Recover current MA20 breadth from the public web APIs, without inventing MA50."""
from __future__ import annotations
import argparse
import concurrent.futures
import datetime as dt
import json
import math
import statistics
import urllib.parse
from collections import defaultdict
from pathlib import Path

from market_breadth import ROOT, ZONE, atomic_json, fetch, summarize

BETA = 'https://beta.dapanyuntu.com'
SCKD = 'https://sckd.dapanyuntu.com/api/api'


def code(value):
    number = float(value)
    if not math.isfinite(number) or not number.is_integer() or not 0 <= number <= 999999:
        raise ValueError('Invalid stock code')
    return f'{int(number):06d}'


def finite(value):
    return isinstance(value, (int, float)) and math.isfinite(value)


def source_frame(payload):
    dates, names = payload['dates'], payload['industries']
    if len(dates) != len(set(dates)) or dates != sorted(dates):
        raise ValueError('Invalid source dates')
    index = {(dates[d], names[i]): value for d, i, value in payload['data']}
    if not index or any(not finite(v) or not 0 <= v <= 100 for v in index.values()):
        raise ValueError('Invalid reported breadth ratio')
    latest = max(date for date, industry in index)
    if len(names) < 50:
        raise ValueError('Industry universe unexpectedly small')
    return dates, names, latest, index


def preview():
    """Lightweight online fallback: live participation and reported industry MA20.

    No fabricated all-market MA values or inferred stock-count denominators.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        fq=pool.submit(fetch,BETA+'/api/heatmap/quotes?period=day',attempts=1,timeout=10)
        fb=pool.submit(fetch,SCKD+'/industry_ma20_analysis_page?page=0',attempts=1,timeout=10)
        quotes,breadth=fq.result(),fb.result()
    dates,names,latest,index=source_frame(breadth)
    prices=[dict(close=q['price'],pct=q['changePct'],ma20=None,ma50=None) for q in quotes['quotes'].values()
            if finite(q.get('price')) and q['price']>0 and finite(q.get('changePct'))]
    if len(prices)<4000:
        raise ValueError('Beta quote universe is incomplete')
    p=summarize(prices)
    market=[dict(date=date,**(p if date==latest and quotes['updatedAt'][:10]==latest else summarize([]))) for date in dates]
    rows=[]
    for industry in names:
        series=[]
        for date in dates:
            s=dict(date=date,**summarize([]))
            s['ma20']=dict(pct=index.get((date,industry)),above=None,valid=None,reported=True)
            series.append(s)
        rows.append(dict(industry=industry,series=series,latest=series[-1]['ma20']['pct']))
    return dict(schemaVersion=1,dataMode='public-aggregates',availableMetrics=['ma20'],
        asOf=latest,dates=dates,market=market,rows=rows,barStatus='partial',coveragePct=None,
        universeCount=len(prices),latestHistoryCount=None,
        generatedAt=dt.datetime.now(ZONE).isoformat(timespec='seconds'),
        source='大盘云图公开API（在线备用）：beta个股报价及sckd东财行业MA20聚合值',
        method='在线备用模式：行业MA20为上游聚合值，未提供每格分母；不做行业均值冒充全市场MA20。全市场MA20/MA50均留空，等待逐股收盘快照。beta涨跌分布独立按最新报价计算，时间与行业MA20分开显示。',
        participation=dict(asOf=quotes['updatedAt'][:10],updatedAt=quotes['updatedAt'],source=BETA+'/api/heatmap/quotes?period=day',**p))


def collect(days=6, workers=4, expected=None):
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        fq=pool.submit(fetch, BETA+'/api/heatmap/quotes?period=day', attempts=2, timeout=15)
        fo=pool.submit(fetch, BETA+'/api/heatmap/overview?period=day', attempts=2, timeout=15)
        fb=pool.submit(fetch, SCKD+'/industry_ma20_analysis_page?page=0', attempts=2, timeout=15)
        quotes, overview, breadth = fq.result(), fo.result(), fb.result()
    dates, names, latest, index = source_frame(breadth)
    now=dt.datetime.now(ZONE)
    if expected is None:
        from trading_calendar import expected_close
        expected=expected_close(now)
    if latest != expected:
        raise ValueError(f'Source close {latest} is not expected exchange close {expected}')
    if latest > now.date().isoformat() or latest == now.date().isoformat() and now.hour < 16:
        raise ValueError('Source contains an incomplete close')
    if quotes['updatedAt'][:10] != latest:
        raise ValueError('Quote date and MA20 date disagree')
    overview_all=next(x for x in overview['markets'] if x['market']=='all')
    if overview_all['updatedAt'][:10] != latest:
        raise ValueError('Overview date and MA20 date disagree')
    raw_quotes=quotes['quotes']
    all_clean_quotes={key: value for key,value in raw_quotes.items()
                  if finite(value.get('price')) and value['price']>0 and finite(value.get('changePct'))}
    clean_quotes={key.split('.')[0]:value for key,value in all_clean_quotes.items() if key.endswith(('.SH','.SZ'))}
    universe_count=sum(x['stockCount'] for x in overview['markets'] if x['market'] in ('sse','szse'))
    if len(clean_quotes) < 4000 or len(clean_quotes)/universe_count < .95:
        raise ValueError('Beta quote coverage below 95%')
    cache=ROOT/'output'/'public-breadth-cache'
    cache.mkdir(parents=True, exist_ok=True)
    atomic_json(cache/f'quotes-{latest}.json', quotes)
    atomic_json(cache/f'overview-{latest}.json', overview)
    atomic_json(cache/f'industry-{latest}.json', breadth)
    selected=dates[-days:]
    day_rows=defaultdict(dict)
    sector_rows=defaultdict(list)
    errors=[]
    def one(task):
        date, industry=task
        # File identity is numeric and independent of untrusted industry names.
        path=cache/f'{date}-industry-{names.index(industry):03d}.json'
        if path.exists():
            response=json.loads(path.read_text())
            if response.get('date')!=date or response.get('industry')!=industry:
                response=None
        else:
            response=None
        if response is None:
            query=urllib.parse.urlencode(dict(industry=industry,date=date))
            response=fetch(SCKD+'/stock_daily_data_by_industry_and_date?'+query,attempts=2,timeout=10)
            if response.get('date')!=date or response.get('industry')!=industry or 'data' not in response:
                raise ValueError('Industry/date identity mismatch')
            atomic_json(path,response)
        rows=[]
        for r in response['data']:
            if r.get('date')!=date or r.get('industry')!=industry:
                raise ValueError('Mixed industry date')
            if not finite(r.get('close_price')) or r['close_price']<=0 or not finite(r.get('change_percent')):
                continue
            rows.append(dict(code=code(r['stock_code']),industry=industry,close=r['close_price'],pct=r['change_percent'],
                             ma20=r['ma20'] if finite(r.get('ma20')) and r['ma20']>0 else None,ma50=None))
        return date,industry,rows
    tasks=[(date,industry) for date in selected for industry in names]
    print(f'Public source actual close={latest}; quotes={len(clean_quotes)}; requests={len(tasks)}',flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        jobs={pool.submit(one,task):task for task in tasks}
        for done,future in enumerate(concurrent.futures.as_completed(jobs),1):
            date,industry=jobs[future]
            try:
                date,industry,rows=future.result()
                sector_rows[(date,industry)]=rows
                for row in rows:
                    if row['code'] not in clean_quotes:
                        continue
                    if row['code'] in day_rows[date]:
                        raise ValueError('Duplicate stock across industries')
                    day_rows[date][row['code']]=row
            except Exception as exc:
                errors.append(dict(date=date,industry=industry,error=str(exc)[:160]))
            if done%86==0:
                print(f'Industry snapshots {done}/{len(tasks)} failures={len(errors)}',flush=True)
    market=[]
    for date in dates:
        values=list(day_rows[date].values())
        if date in selected and len(values)/universe_count < .95:
            raise ValueError(f'{date} stock coverage below 95% ({len(values)}/{universe_count})')
        summary=summarize(values)
        if date in selected and summary['ma20']['valid']/universe_count<.95:
            raise ValueError(f'{date} valid MA20 coverage below 95%')
        market.append(dict(date=date,**summary))
    current=day_rows[latest]
    matched=[(row,clean_quotes[c]) for c,row in current.items() if c in clean_quotes]
    mismatch=[(r['code'],r['close'],q['price']) for r,q in matched if abs(r['close']/q['price']-1)>.005]
    if len(matched)/len(current)<.95 or len(mismatch)/max(1,len(matched))>.01:
        raise ValueError('Latest close cross-check failed')
    rows=[]
    for industry in names:
        series=[]
        for date in dates:
            values=sector_rows.get((date,industry))
            if values is not None:
                summary=summarize(values)
            else:
                summary=summarize([])
                reported=index.get((date,industry))
                summary['ma20']=dict(pct=reported,above=None,valid=None,reported=True)
            series.append(dict(date=date,**summary))
        recent=[s['ma20']['pct'] for s in series[-5:]]
        prior=[s['ma20']['pct'] for s in series[-10:-5]]
        values=[s['ma20']['pct'] for s in series]
        rows.append(dict(industry=industry,series=series,latest=series[-1]['ma20']['pct'],
                         avg5=round(statistics.mean(recent),2) if all(finite(v) for v in recent) else None,
                         slope5=round(statistics.mean(recent)-statistics.mean(prior),2) if len(prior)==5 and all(finite(v) for v in recent+prior) else None,
                         days70=sum(finite(v) and v>=70 for v in values),daysTotal=sum(finite(v) for v in values),isCurrentR02=False))
    participation=summarize([dict(close=q['price'],pct=q['changePct'],ma20=None,ma50=None) for q in all_clean_quotes.values()])
    latest_count=len(current)
    return dict(schemaVersion=1,asOf=latest,dateStart=dates[0],dateEnd=latest,dates=dates,market=market,rows=rows,
        generatedAt=now.isoformat(timespec='seconds'),barStatus='completed',availableMetrics=['ma20'],
        universeLabel='沪深A股',excludedMarkets=['北交所'],
        universeCount=universe_count,historyCount=latest_count,latestHistoryCount=latest_count,
        coveragePct=round(latest_count/universe_count*100,2),
        providerCounts={'DapanyuntuSCKD':latest_count},benchmarks=[],
        source='大盘云图公开API：beta个股报价 + sckd东财行业收盘价/MA20；本地逐股汇总',
        method='沪深A股合计按逐股分子/分母计算，含ST、不含北交所，按当前沪深报价名单回溯，存在存续样本偏差；未独立验证复权因子。行业格按sckd实际行业样本，可能含少量北交所，不能与沪深合计直接相加。行业为东财86板块，不与旧128行业序列拼接。最近6交易日逐股重算，保留之前已校验的同口径历史点；更早行业格为上游聚合值，分子分母未知。beta涨跌参与度单独覆盖沪深京。MA50未提供，全部留空，不能据此确认中期顺风或放大仓位。',
        participation=dict(asOf=latest,updatedAt=quotes['updatedAt'],source=BETA+'/api/heatmap/quotes?period=day',**participation),
        verification=dict(matched=len(matched),priceMismatchCount=len(mismatch),priceMismatchSamples=mismatch[:10],failedRequests=errors),
        sources=[dict(url=BETA+'/api/heatmap/quotes?period=day',updatedAt=quotes['updatedAt']),
                 dict(url=SCKD+'/industry_ma20_analysis_page?page=0',actualLastDate=latest)])


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--days',type=int,default=6)
    p.add_argument('--workers',type=int,default=4)
    args=p.parse_args()
    status=ROOT/'market-breadth-status.json'
    attempted=dt.datetime.now(ZONE).isoformat(timespec='seconds')
    try:
        result=collect(args.days,args.workers)
        from daily_breadth import validate_snapshot, merge_verified_history
        from trading_calendar import expected_close
        previous=json.loads((ROOT/'market-breadth.json').read_text()) if (ROOT/'market-breadth.json').exists() else None
        validate_snapshot(result, expected_close(), previous)
        result=merge_verified_history(result,previous)
        atomic_json(ROOT/'market-breadth.json',result)
        atomic_json(status,dict(status='success',attemptedAt=attempted,asOf=result['asOf'],availableMetrics=['ma20'],note='MA20已更新；MA50未提供，禁止进攻仓位确认'))
        print(json.dumps({k:result[k] for k in ['asOf','coveragePct','universeCount','latestHistoryCount','verification']},ensure_ascii=False),flush=True)
    except Exception as exc:
        atomic_json(status,dict(status='failed',attemptedAt=attempted,error=str(exc)[:250]))
        raise


if __name__=='__main__':
    main()
