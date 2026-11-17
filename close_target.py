"""Resolve the trading date independently of when a cloud job is delivered."""
from __future__ import annotations

from datetime import date

from trading_calendar import expected_close, is_trading_day


def close_target(now, calendar, requested_date=None):
    """Latest finalized trading date by default; reject invalid explicit dates.

    Derive the default from the exchange calendar, not the local date. This
    makes a delayed Friday close event eligible to catch up on Saturday.
    History collection must still request only missing bars through this date.
    """
    latest = expected_close(now, calendar)
    if requested_date is None:
        return latest
    if not isinstance(requested_date, str):
        raise ValueError('Close target must be YYYY-MM-DD')
    try:
        parsed = date.fromisoformat(requested_date)
    except ValueError as exc:
        raise ValueError('Close target must be YYYY-MM-DD') from exc
    if parsed.isoformat() != requested_date:
        raise ValueError('Close target must be YYYY-MM-DD')
    if not is_trading_day(parsed, calendar):
        raise ValueError('Close target is not a verified exchange trading day')
    if requested_date > latest:
        raise ValueError('Close target is not finalized')
    return requested_date
