"""Independent equal-weight sector snapshot; never a sector index or MA signal."""
from __future__ import annotations
import argparse
import datetime as dt
import json
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo
ZONE=ZoneInfo('Asia/Shanghai')


def finite(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)


def identity(value):
    if not isinstance(value,str) or not re.fullmatch(r'[036][0-9]{5}(?:\.(?:SH|SZ))?',value):
        raise ValueError('Invalid Shanghai/Shenzhen stock identity')
    code=value[:6]
    if '.' in value and value[7:] != ('SH' if code.startswith('6') else 'SZ'):
        raise ValueError('Code/exchange mismatch')
    return code


def summarize(rows, expected, names):
    n=len(rows); valid=n/expected>=.95 if expected else False
    pct=[r['changeRatio'] for r in rows]
    dates=[r['sourceTime'] for r in rows]
    up=sum(v>0 for v in pct);down=sum(v<0 for v in pct);flat=sum(v==0 for v in pct)
    leaders=sorted(rows,key=lambda r:(-r['changeRatio'],r['code']))[:3]
    leader_values=[dict(code=r['code'],name=names.get(r['code']),changeRatio=r['changeRatio'],latest=r['latest'],sourceTime=r['sourceTime']) for r in leaders]
    return dict(valid=n,expected=expected,missing=expected-n,coveragePct=round(n/expected*100,4) if expected else None,
                sufficientCoverage=valid,zeroVolumeCount=sum(r['volume']==0 for r in rows),
                sourceTimeMin=min(dates) if dates else None,sourceTimeMax=max(dates) if dates else None,
                meanChangePct=statistics.mean(pct) if valid else None,medianChangePct=statistics.median(pct) if valid else None,
                upCount=up,downCount=down,flatCount=flat,
                upPct=100*up/n if valid else None,downPct=100*down/n if valid else None,flatPct=100*flat/n if valid else None,
                top3=leader_values if valid else [])


def build_sector_observation(base, records, *, day, names=None):
    names=names or {};dt.date.fromisoformat(day)
    stocks=base.get('dailyHistory',{}).get('sourceStocks') or []
    universe=base.get('universeCount')
    if not isinstance(universe,int) or universe<=0 or not stocks or base.get('asOf','')>=day:
        raise ValueError('Require frozen prior-close stock list and original total denominator')
    bycode={}
    for stock in stocks:
        code=identity(stock['code'])
        if code in bycode or not stock.get('industry') or stock.get('secid') != ('1.' if code.startswith('6') else '0.')+code:
            raise ValueError('Invalid or duplicate frozen membership')
        bycode[code]=stock
    if len(stocks)>universe or len(stocks)/universe<.95:
        raise ValueError('Frozen membership coverage below 95%')
    seen=set();accepted=[];invalid=[];byindustry=defaultdict(list)
    for i,record in enumerate(records):
        raw=record.get('code') if isinstance(record,dict) else None
        try:code=identity(raw)
        except ValueError:
            invalid.append(dict(recordIndex=i,code=raw,reason='invalid_identity'));continue
        if code in seen:raise ValueError('Duplicate quote identity: '+code)
        seen.add(code)
        if code not in bycode:
            invalid.append(dict(recordIndex=i,code=code,reason='outside_frozen_membership'));continue
        if any(not finite(record.get(k)) for k in ('latest','changeRatio','volume')) or record['latest']<=0 or record['volume']<0 or record['changeRatio'] < -100:
            invalid.append(dict(recordIndex=i,code=code,reason='missing_or_invalid_native_values'));continue
        try:
            stamp=dt.datetime.fromisoformat(record['sourceTime'])
            if stamp.tzinfo is None:raise ValueError('Timezone required')
            stamp=stamp.astimezone(ZONE)
            if stamp.date().isoformat()!=day or stamp.time().replace(tzinfo=None)>=dt.time(13):raise ValueError('Wrong session')
        except (KeyError,TypeError,ValueError):
            invalid.append(dict(recordIndex=i,code=code,reason='invalid_or_outside_day_before_1300_source_time'));continue
        item=dict(code=code,latest=record['latest'],changeRatio=record['changeRatio'],volume=record['volume'],sourceTime=stamp.isoformat())
        accepted.append(item);byindustry[bycode[code]['industry']].append(item)
    groups=defaultdict(list)
    for code,stock in bycode.items():groups[stock['industry']].append(code)
    industry_rows=[]
    for name,codes in sorted(groups.items()):
        rows=byindustry[name];entry=dict(industry=name,**summarize(rows,len(codes),names))
        entry['missingCodes']=sorted(set(codes)-{r['code'] for r in rows});industry_rows.append(entry)
    market=summarize(accepted,universe,names)
    top=sorted((r for r in industry_rows if r['sufficientCoverage']),key=lambda r:(-r['meanChangePct'],r['industry']))[:15]
    return dict(schemaVersion=1,scopeVersion='ffd-frozen-industry-midday-observation-v1',asOf=day,session='midday_source_observation',
                generatedAt=dt.datetime.now(ZONE).isoformat(),candidateOnly=True,publishable=market['sufficientCoverage'],
                membershipDate=base['asOf'],universeCount=universe,sourceStockCount=len(stocks),industryCount=len(groups),
                stocksWithoutVerifiedMembership=universe-len(stocks),source='FFD snapshot native latest/changeRatio/volume/sourceTime',
                nativeTimeLabelValidated=True,quoteTimeVerified=False,exact1130Snapshot=False,changeRatioUnit='percent_native_scale_1',volumeUnit='累计手',
                market=market,top15=top,industries=industry_rows,invalidRecords=invalid,
                missingQuoteCodes=sorted(set(bycode)-{r['code'] for r in accepted}),
                method='冻结前收盘行业名单的个股原生涨跌幅等权均值/中位数；上涨、下跌、平盘比例按有效报价计。原生百分数不再乘100。零成交单独统计，不补造涨幅。全市场分母不缩小，市场/行业有效报价不足95%指标留空。',
                limitations=['非东财板块指数；不替换原496分类榜','非MA50/非行业宽度均线信号/非多日趋势排行',
                             '批次源时间不同，不是11:30精确截点；源标签不是已独立核实的最后成交时刻','沿用当前冻结名单，存在存续样本偏差','领涨股仅为本次有效样本排序，不是买入建议'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--records',type=Path,required=True)
    p.add_argument('--day',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--names',type=Path)
    a=p.parse_args()
    if a.output.name!='sector-observation.json':raise SystemExit('Output must be independent sector-observation.json')
    result=build_sector_observation(json.loads(a.base.read_text()),json.loads(a.records.read_text()),day=a.day,names=json.loads(a.names.read_text()) if a.names else None)
    if not result['publishable']:
        print(json.dumps(dict(status='coverage_blocked',market=result['market']),ensure_ascii=False));raise SystemExit(2)
    from market_breadth import atomic_json
    atomic_json(a.output,result)
    print(json.dumps(dict(status='candidate_only',market=result['market'],industryCount=result['industryCount']),ensure_ascii=False))
