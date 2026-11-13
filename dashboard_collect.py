"""One free-source dashboard observation per verified exchange session.

No FFD calls or breadth collection. Publish only dashboard-observed.json and its
status; raw receipts remain under output/. Source quote time is never invented.
"""
from __future__ import annotations
import argparse
import datetime as dt
import fcntl
import hashlib
import json
import threading
import urllib.parse
import uuid
from pathlib import Path
from zoneinfo import ZoneInfo
import server
from trading_calendar import load_calendar, is_trading_day
from market_breadth import atomic_json

ZONE=ZoneInfo('Asia/Shanghai')
ROOT=Path(__file__).resolve().parent


def observation_warnings(observation):
    count=observation.get('missingSectorHistoryCount')
    total=observation.get('sectorClassificationCount')
    breadth=observation.get('breadthClassificationCount')
    return [
        '观察抓取时间不等于源行情时间；未核验精确午盘/收盘截点。',
        f'东财板块总数：{total if total is not None else "未返回"}；宽度行业数：{breadth if breadth is not None else "未知"}。分类不保证等价，涨幅排名不是全行业趋势排名。',
        f'板块日线缺失组数：{count if count is not None else "未知"}；量价观察未核新闻/公告，正式R02仍为带日期的历史记录。']


def check_session(session, now, calendar):
    local=now.astimezone(ZONE)
    if session not in ('midday','close'):
        raise ValueError('Unknown observation session')
    if not is_trading_day(local.date(),calendar):
        return False
    clock=local.time().replace(tzinfo=None)
    return (dt.time(11,35)<=clock<dt.time(12,55)) if session=='midday' else clock>=dt.time(16)


def collect(session, *, root=ROOT, now=None, force=False, builder=None):
    root=Path(root);now=now or dt.datetime.now(dt.timezone.utc)
    calendar=load_calendar(root/'market-trading-calendar.json',year=now.astimezone(ZONE).year,allow_fetch=False)
    if not check_session(session,now,calendar):
        return dict(status='skipped',reason='Outside verified exchange session')
    day=now.astimezone(ZONE).date().isoformat()
    target=root/'dashboard-observed.json'
    output=root/'output'/'dashboard-observations';output.mkdir(parents=True,exist_ok=True)
    with (output/'collection.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        existing=json.loads(target.read_text()) if target.exists() else None
        old=(existing or {}).get('observation',{})
        if old.get('asOf','') > day:
            raise ValueError('Refusing observation date regression')
        if not force and old.get('asOf')==day and old.get('session')==session:
            return dict(status='already_collected',runId=old.get('runId'),ffdCalls=0)
        started=now.isoformat()
        runid=f'dashboard-{day}-{session}-'+now.strftime('%H%M%S%f')
        archive=output/runid;archive.mkdir(exist_ok=False)
        records=[];mutex=threading.Lock();totals=[]
        original=server.fetch_json
        def audited(url,referer,timeout=None):
            begin=dt.datetime.now(dt.timezone.utc).isoformat()
            record=dict(url=url,startedAt=begin)
            try:
                data=original(url,referer,timeout)
                # Capture the server-declared classification total, not 30 ranked rows.
                query=urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                if query.get('fs')==['m:90 t:2'] or query.get('fs')==['m:90+t:2']:
                    total=(data.get('data') or {}).get('total')
                    if isinstance(total,int) and not isinstance(total,bool):totals.append(total)
                with mutex:
                    name='response-'+uuid.uuid4().hex+'.json'
                    encoded=json.dumps(data,ensure_ascii=False,sort_keys=True).encode()
                    (archive/name).write_bytes(encoded)
                    record.update(responseFile=name,sha256=hashlib.sha256(encoded).hexdigest())
                return data
            except Exception as exc:
                record.update(errorType=type(exc).__name__)
                raise
            finally:
                record['finishedAt']=dt.datetime.now(dt.timezone.utc).isoformat()
                with mutex:records.append(record)
        server.fetch_json=audited
        try:
            data=(builder or server.build_dashboard_payload)(force=True)
        except Exception as exc:
            atomic_json(root/'dashboard-observed-status.json',dict(status='failed',asOf=day,session=session,runId=runid,errorType=type(exc).__name__,ffdCalls=0))
            raise
        finally:
            server.fetch_json=original
            atomic_json(archive/'requests.json',dict(requests=records,ffdCalls=0))
        finished=dt.datetime.now(dt.timezone.utc).isoformat()
        breadth=json.loads((root/'market-breadth.json').read_text())
        top=data.get('top5') or []
        missing=sum(not row.get('trend10') for row in top)
        observation=dict(runId=runid,asOf=day,session=session,startedAt=started,finishedAt=finished,
                         quoteTimeVerified=False,ffdCalls=0,missingSectorHistoryCount=missing,
                         sectorClassificationCount=totals[-1] if totals and len(set(totals))==1 else None,
                         breadthClassificationCount=len(breadth.get('rows') or []),
                         indexCount=len(data.get('indices') or []),rankedSectorCount=len(data.get('sectors') or []),
                         leaderCount=sum(len(row.get('leaders10') or []) for row in top))
        # Preserve financial fields, not duplicated close data or raw transport errors.
        payload={key:value for key,value in data.items() if key not in ('marketDistribution','r02Breadth','moduleStatus','observation')}
        payload['warnings']=observation_warnings(observation)
        doc=dict(schemaVersion=1,observation=observation,payload=payload)
        json.dumps(doc, allow_nan=False)  # Reject non-finite source values before publication.
        atomic_json(archive/'candidate.json',doc)
        # Empty/failed live data never replace the prior useful observation.
        acceptable=observation['indexCount']>0 or observation['rankedSectorCount']>0
        status=dict(status='partial' if acceptable else 'failed',asOf=day,session=session,runId=runid,
                    finishedAt=finished,ffdCalls=0,observation=observation)
        if acceptable:
            atomic_json(target,doc)
            status['savedObservation']=True
        atomic_json(root/'dashboard-observed-status.json',status)
        return status


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--session',choices=['midday','close'],required=True)
    p.add_argument('--force',action='store_true');args=p.parse_args()
    print(json.dumps(collect(args.session,force=args.force),ensure_ascii=False))
