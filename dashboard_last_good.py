"""Merge failed modules without changing their original observation identity."""
import copy
import datetime as dt


def merge_modules(data, observation, previous=None):
    data=copy.deepcopy(data);previous=previous or {}
    prior=previous.get('payload',{});old=previous.get('observation',{})
    oldmeta=old.get('modules',{})
    def provenance(key, retained=False, specific=None):
        source=(specific or oldmeta.get(key) or old) if retained else observation
        return dict(runId=source.get('runId'),finishedAt=source.get('finishedAt'),
                    asOf=source.get('asOf'),cached=retained,stale=retained,
                    quoteTimeVerified=False)
    modules={}
    if not data.get('indices') and prior.get('indices'):
        data['indices']=copy.deepcopy(prior['indices']);modules['indices']=provenance('indices',True)
    else:modules['indices']=provenance('indices')
    retain_rank=not data.get('sectors') and bool(prior.get('sectors'))
    if retain_rank:
        data['sectors']=copy.deepcopy(prior['sectors'])
        data['top5']=copy.deepcopy(prior.get('top5',[]))
        meta=provenance('sectorRank',True)
        data['sectorRankStatus']=dict(ready=True,cached=True,reason='last_good_module',cachedAt=meta['finishedAt'],
                                     message='保留此前板块观察，非本轮行情',runId=meta['runId'],stale=True)
        observation['sectorClassificationCount']=old.get('sectorClassificationCount')
    modules['sectorRank']=provenance('sectorRank',retain_rank)
    oldrows={r.get('code'):r for r in prior.get('top5',[])}
    for row in data.get('top5',[]):
        priorrow=oldrows.get(row.get('code'),{})
        detail={}
        for field,key in [('leaders10','leaders'),('trend10','history')]:
            retained=retain_rank or (not row.get(field) and bool(priorrow.get(field)))
            if retained and priorrow.get(field):row[field]=copy.deepcopy(priorrow[field])
            olddetail=priorrow.get('observedModules',{}).get(key)
            detail[key]=provenance('sectorRank',retained,olddetail)
            detail[key]['missing']=not bool(row.get(field))
        row['observedModules']=detail
        if detail['history']['cached']:
            row.update(trend10Cached=True,trend10CachedAt=detail['history']['finishedAt'])
    observation['modules']=modules
    top=data.get('top5') or []
    observation.update(indexCount=len(data.get('indices') or []),rankedSectorCount=len(data.get('sectors') or []),
                       leaderCount=sum(len(r.get('leaders10') or []) for r in top),
                       missingSectorHistoryCount=sum(not r.get('trend10') for r in top) if top else None)
    return data,observation
