"""Independent free-source observation job; requires a fresh production checkout.

Use a separate Actions job with contents:write, checkout ref main, and the same
publication concurrency group as breadth. No PAT, secret, deploy API or force
option is supported. Prefer this job before breadth, with a separate fresh checkout for breadth.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import time
import cloud_breadth as cloud
import dashboard_collect as collector
from market_breadth import ROOT, ZONE, fetch
from trading_calendar import load_calendar

SNAPSHOT='dashboard-observed.json'
STATUS='dashboard-observed-status.json'
FILES={SNAPSHOT,STATUS}


def require_actions():
    if (os.environ.get('GITHUB_ACTIONS')!='true' or
        os.environ.get('GITHUB_REPOSITORY')!='internetman/blackhorse-quant' or
        os.environ.get('GITHUB_REF')!='refs/heads/main'):
        raise ValueError('Only production main Actions job-token publication is supported')


def read(root,name):
    path=root/name
    return json.loads(path.read_text()) if path.exists() else None


def validate(root,session,day):
    status=read(root,STATUS)
    if not status or status.get('asOf')!=day or status.get('session')!=session or not status.get('runId'):
        raise ValueError('Missing matching observation status')
    if status.get('ffdCalls')!=0:
        raise ValueError('Unexpected paid collection')
    if status.get('status') not in ('partial','success','failed','empty'):
        raise ValueError('Unexpected observation status')
    if status['status'] in ('partial','success'):
        obs=(read(root,SNAPSHOT) or {}).get('observation',{})
        if any(obs.get(k)!=status.get(k) for k in ('runId','asOf','session')):
            raise ValueError('Observation/status identity mismatch')
        if obs.get('ffdCalls')!=0 or not (obs.get('indexCount',0)>0 or obs.get('rankedSectorCount',0)>0):
            raise ValueError('Empty or paid observation')
    return status


def publish(root,session,day):
    status=validate(root,session,day)
    changed=cloud.changed_paths(root)
    allowed={STATUS} if status['status'] in ('failed','empty') else FILES
    if not changed<=allowed or cloud.git(root,'diff','--cached','--name-only'):
        raise ValueError('Unexpected changes; fresh checkout required, no breadth files permitted')
    cloud.git(root,'fetch','--quiet','origin','main')
    head=cloud.git(root,'rev-parse','HEAD')
    if head!=cloud.git(root,'rev-parse','FETCH_HEAD'):
        raise ValueError('Remote HEAD advanced; refuse merge or force push')
    if changed:
        cloud.git(root,'add','--',*sorted(changed))
        if set(cloud.git(root,'diff','--cached','--name-only').splitlines())!=changed:
            raise ValueError('Unexpected staging')
        cloud.git(root,'-c','user.name=github-actions[bot]','-c',
                  'user.email=41898282+github-actions[bot]@users.noreply.github.com',
                  'commit','-m',f'Observe dashboard {day} {session}')
        head=cloud.git(root,'rev-parse','HEAD')
        cloud.git(root,'push','origin','HEAD:main')
        remote=cloud.git(root,'ls-remote','origin','refs/heads/main').split()
        if not remote or remote[0]!=head:
            raise RuntimeError('Published commit is not remote HEAD')
    return dict(status='pushed' if changed else 'unchanged',commit=head,files=sorted(changed))


def verify_site(root,attempts=18,delay=10):
    # Also prove a failed collection left the prior website observation intact.
    expected={name:read(root,name) for name in FILES if (root/name).exists()}
    for attempt in range(attempts):
        try:
            for name,value in expected.items():
                actual=fetch(f'{cloud.SITE}/{name}?dashboard_verify={time.time_ns()}',attempts=1,timeout=10)
                if actual!=value:
                    raise ValueError('Website observation/status generation mismatch')
            return dict(status='verified',runId=expected[STATUS]['runId'],
                        observationRunId=(expected.get(SNAPSHOT) or {}).get('observation',{}).get('runId'))
        except Exception:
            if attempt+1<attempts:time.sleep(delay)
    raise RuntimeError('Website JSON not verified; job-token push is not proof of deployment')


def run(root=ROOT,now=None,event='workflow_dispatch',cron='',requested='auto'):
    require_actions()
    root=Path(root);now=(now or dt.datetime.now(ZONE)).astimezone(ZONE)
    session=cloud.choose_session(event,cron,requested,now)
    calendar=load_calendar(root/'market-trading-calendar.json',now.year,allow_fetch=False)
    if not collector.check_session(session,now,calendar):
        return dict(status='skipped',reason='Outside verified exchange session window',session=session)
    cloud.check_repository(root)
    if cloud.changed_paths(root) or cloud.git(root,'diff','--cached','--name-only'):
        raise ValueError('Fresh clean checkout required; never reuse failed breadth worktree')
    day=now.date().isoformat()
    old=read(root,STATUS) or {}
    if old.get('asOf','')>day:
        raise ValueError('Refusing observation status date regression')
    # A saved failed attempt is also terminal for this session: never refetch it.
    if old.get('asOf')==day and old.get('session')==session and old.get('runId'):
        report=dict(status='already_attempted',runId=old['runId'])
    else:
        try:report=collector.collect(session,root=root,now=now)
        except Exception:
            # Publish only matching failed status; snapshot is untouched or fail closed.
            report=dict(status='failed',reason='Collector failed; inspect private job logs')
    publication=publish(root,session,day)
    receipt=dict(report,session=session,publication=publication)
    try:receipt['verification']=verify_site(root)
    except Exception as exc:raise cloud.PublicationVerificationError(receipt,exc) from exc
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--session',choices=['auto','midday','close'],default='auto')
    args=p.parse_args();receipt={}
    try:
        require_actions()
        event=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
        receipt=run(event=os.environ['GITHUB_EVENT_NAME'],cron=event.get('schedule',''),requested=args.session)
    except Exception as exc:
        receipt=getattr(exc,'receipt',dict(status='failed',errorType=type(exc).__name__))
        raise
    finally:
        print(json.dumps(receipt,ensure_ascii=False),flush=True)
        if os.environ.get('GITHUB_STEP_SUMMARY'):
            with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:
                f.write('### Dashboard observation\n```json\n'+json.dumps(receipt,ensure_ascii=False)+'\n```\n')

if __name__=='__main__':main()
