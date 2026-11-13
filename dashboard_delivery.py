"""Serve dated observations promptly; never relabel them as live quotations."""
from __future__ import annotations
import concurrent.futures
import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo
import server

ROOT = Path(__file__).resolve().parent
ZONE = ZoneInfo('Asia/Shanghai')


def observed_payload(root=ROOT, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    saved = json.loads((Path(root)/'dashboard-observed.json').read_text())
    observation = dict(saved['observation'])
    observed = dt.datetime.fromisoformat(observation['finishedAt'])
    if observed.tzinfo is None or now.tzinfo is None:
        raise ValueError('Observation requires timezone-aware times')
    age = (now-observed).total_seconds()
    if age < -60:
        raise ValueError('Observation is in the future')
    data = dict(saved['payload'])
    if observation.get('quoteTimeVerified') is not False or not observation.get('runId'):
        raise ValueError('Observation provenance missing')
    # Never freeze the completed-close breadth inside an intraday observation.
    # Use the current deployed file, preserving its actual asOf and source.
    breadth = json.loads((Path(root)/'market-breadth.json').read_text())
    if breadth.get('coveragePct',0) < 95 or not breadth.get('market'):
        raise ValueError('Current breadth snapshot failed its original coverage gate')
    data['r02Breadth'] = breadth
    data['marketDistribution'] = dict(breadth['market'][-1],asOf=breadth['asOf'],
                                      source=breadth.get('source'),barStatus='completed')
    data['source'] = dict(data['source'],marketDistribution=breadth.get('source'),r02Breadth=breadth.get('source'))
    stale = age > 1800 or observed.astimezone(ZONE).date() != now.astimezone(ZONE).date()
    data['observation'] = dict(observation,mode='published_observation',ageSeconds=round(max(0,age)),stale=stale,
                               servedAt=now.isoformat(),quoteTimeVerified=False)
    data['moduleStatus'] = server.dashboard_module_status(data)
    data['warnings'] = list(data.get('warnings', []))+[
        '已发布观察快照，不是实时流；源行情时间未提供，不能认定为11:30截点。',
        '板块排名为东财496分类，与宽度86行业不等价；不是全行业趋势排名。',
        '5组板块日线缺失；正式R02记录为历史配置，未根据新闻重新确认。']
    if stale:
        data['warnings'].append('观察快照已滞后；仅供回顾，不代表当前市场。')
    return data


def build_delivery(force=False, *, root=ROOT, now=None, timeout=20, live_builder=None):
    saved = observed_payload(root,now)
    if not force and not saved['observation']['stale']:
        return saved
    # Bound the user-visible live attempt below Vercel's 30s function limit.
    # Existing free-source collector may finish later; never change the saved
    # observation or claim that a timeout refreshed its market timestamps.
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = pool.submit(live_builder or server.build_dashboard_payload, force=True)
    try:
        live = future.result(timeout=timeout)
        now_text = dt.datetime.now(dt.timezone.utc).isoformat()
        live['observation'] = dict(mode='live_fetch_attempt',runId='live-'+now_text,finishedAt=now_text,
                                   session='source_time_unverified',quoteTimeVerified=False,stale=False)
        live['moduleStatus'] = server.dashboard_module_status(live)
        live.setdefault('warnings',[]).extend([
            '本次抓取不是源行情时间，实时时效仍未核验。',
            '板块排名为东财496分类，与宽度86行业不等价；不是全行业趋势排名。',
            '量价观察未核新闻/公告；正式R02记录为历史配置，非本轮自动确认。'])
        return live
    except Exception as exc:
        saved['observation']['liveAttemptFailed'] = True
        saved['observation']['liveAttemptFailureType'] = type(exc).__name__
        saved['warnings'].append('实时刷新未在限定时间内完成或失败，保留原抓取时间的观察快照。')
        return saved
    finally:
        future.cancel()
        pool.shutdown(wait=False, cancel_futures=True)
