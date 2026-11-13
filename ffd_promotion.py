"""Explicit offline promotion guards. No network, collection, or publication."""
import copy
import datetime as dt
import re
from collections import Counter
from trading_calendar import load_calendar, is_trading_day

FFD_SCOPE = 'qfq-shsz-ffd-experimental-v1'
ADJUSTED_SCOPES = frozenset(('qfq-shsz-v1', FFD_SCOPE))


def require_publishable(data):
    if data.get('candidateOnly') or data.get('publicationApproved') is False:
        raise ValueError('Candidate requires explicit reviewed promotion before publication')
    if data.get('scopeVersion') == FFD_SCOPE and data.get('publicationApproved') is not True:
        raise ValueError('FFD publication requires explicit reviewed promotion')


def validate_ffd_provenance(data):
    cutoff = data['asOf']
    end = dt.date.fromisoformat(cutoff)
    start = end-dt.timedelta(days=90)
    calendar = load_calendar(allow_fetch=False)
    dates = [(start+dt.timedelta(days=i)).isoformat() for i in range(91)
             if is_trading_day(start+dt.timedelta(days=i), calendar)]
    v = data.get('verification', {})
    if (not dates or dates[-1] != cutoff or len(dates) < 50
            or v.get('ffdCalendarExpectedDates') != dates
            or v.get('ffdExperimental') is not True
            or v.get('ffdCorporateActionsIndependentlyReconciled') is not False):
        raise ValueError('FFD calendar/experimental provenance missing or inconsistent')
    h = data.get('dailyHistory', {})
    stocks, manifest = h.get('sourceStocks', []), h.get('manifest', [])
    codes = {s.get('code') for s in stocks}
    if (not stocks or len(codes) != len(stocks) or h.get('stockCount') != len(stocks)
            or len(stocks) > data['universeCount'] or len(stocks)/data['universeCount'] < .95):
        raise ValueError('FFD frozen universe invalid; never reduce full-market denominator')
    for s in stocks:
        code = s.get('code', '')
        if not re.fullmatch('[036][0-9]{5}', code) or s.get('secid') != ('1.' if code.startswith('6') else '0.')+code:
            raise ValueError('FFD source stock identity invalid')
    if (not manifest or len({m.get('code') for m in manifest}) != len(manifest)
            or h.get('validHistories') != len(manifest) or data.get('historyCount') != len(manifest)):
        raise ValueError('FFD manifest count/identity mismatch')
    for m in manifest:
        if (m.get('code') not in codes or m.get('provider') not in ('Tencent','Eastmoney','FFD')
                or m.get('lastDate') != cutoff or not re.fullmatch('[a-f0-9]{64}', m.get('sha256',''))):
            raise ValueError('FFD manifest identity/date/digest invalid')
        if m['provider'] == 'FFD' and (m.get('firstDate') != dates[0] or m.get('bars') != len(dates)):
            raise ValueError('FFD must be a complete same-cutoff calendar window, never stitched')
    counts = dict(Counter(m['provider'] for m in manifest))
    if not counts.get('FFD') or counts != data.get('providerCounts'):
        raise ValueError('FFD provider totals differ from manifest')
    if 'FFD' not in data.get('source','') or '未独立' not in data.get('method',''):
        raise ValueError('FFD source and adjustment limitation must be disclosed')


def promote_candidate(data, expected, *, approved=False, previous=None):
    """Return a new validated object only. Caller owns explicit release approval."""
    if approved is not True or data.get('candidateOnly') is not True or data.get('publicationApproved') is not False:
        raise ValueError('Explicit approval and an unpromoted candidate are required')
    if data.get('scopeVersion') != FFD_SCOPE:
        raise ValueError('Only the independently scoped FFD candidate is eligible')
    from daily_breadth import validate_snapshot
    validate_snapshot(data, expected, previous)
    result = copy.deepcopy(data)
    result.pop('candidateOnly')
    result['publicationApproved'] = True
    require_publishable(result)
    return result


def allow_verified_original_source_rollback(previous, current):
    """Only FFD experiment -> original fully validated free-source scope."""
    if previous.get('scopeVersion') != FFD_SCOPE or current.get('scopeVersion') != 'qfq-shsz-v1':
        return False
    require_publishable(current)
    from daily_breadth import validate_snapshot
    validate_snapshot(current, current['asOf'], previous)
    if any(value.get('provider') == 'FFD' for value in current.get('benchmarks', [])) or current.get('providerCounts', {}).get('FFD'):
        raise ValueError('Original-source rollback must not disguise FFD provenance')
    if any(m.get('provider') == 'FFD' for m in current.get('dailyHistory', {}).get('manifest', [])):
        raise ValueError('Original-source rollback contains FFD manifest')
    return True
