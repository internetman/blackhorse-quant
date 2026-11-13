"""Opt-in FFD history experiment; no credentials, retries or automatic publication.

Each request reserves the maximum calendar-day cells, not an optimistic trading
calendar. Reservations are not refunded on errors. One client per run serializes
all network requests and stops after an uncertain outcome.
"""
from __future__ import annotations
import datetime as dt
import json
import math
import os
import re
import threading
import hashlib
import uuid
from pathlib import Path

ENDPOINT = "https://ffd.findesk.cn/api/query"
EXPERIMENT_SCOPE = "qfq-shsz-ffd-experimental-v1"
_NETWORK_LOCK = threading.Lock()


def parse_history(payload, code, start, cutoff, index=False):
    if not isinstance(payload, dict) or payload.get("code") != 200:
        raise ValueError("FFD did not return a successful history response")
    coverage = payload.get("coverage") or {}
    if coverage.get("complete") is not True or any(coverage.get(k) for k in
            ("partial", "missing_codes", "missing_cells", "missing_cell_count", "shard_errors")):
        raise ValueError("FFD history coverage is incomplete or unknown")
    if coverage.get("returned_codes") != [code] or coverage.get("code_identity_checked") is not True:
        raise ValueError("FFD history identity is not verified")
    adjustment = payload.get("adjustment_execution") or {}
    expected = "none" if index else "qfq"
    if adjustment.get("requested") != expected or adjustment.get("effective") != expected:
        raise ValueError("FFD adjustment does not match requested price basis")
    data = payload.get("data") or {}
    columns = [data.get(k) for k in ("time", "code", "close", "volume")]
    if any(not isinstance(c, list) for c in columns) or not columns[0] or len({len(c) for c in columns}) != 1:
        raise ValueError("FFD missing or malformed history columns")
    rows = []
    for date, identity, close, volume in zip(*columns):
        if identity != code or not isinstance(date, str) or dt.date.fromisoformat(date).isoformat() != date or not start <= date <= cutoff:
            raise ValueError("FFD wrong identity or out-of-range daily date")
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in (close, volume)):
            raise ValueError("FFD null, nonnumeric or nonfinite daily value")
        if close <= 0 or volume < 0:
            raise ValueError("FFD invalid daily value")
        rows.append(dict(date=date, close=float(close), volume=float(volume)))
    dates = [r["date"] for r in rows]
    if dates != sorted(set(dates)) or dates[-1] != cutoff:
        raise ValueError("FFD duplicate, unordered or stale history")
    return rows


class HistoryClient:
    def __init__(self, max_points, *, api_key=None, post=None, receipt_dir=None):
        if isinstance(max_points, bool) or not isinstance(max_points, int) or max_points <= 0:
            raise ValueError("FFD requires an explicit positive per-run budget")
        self._key = api_key if api_key is not None else os.environ.get("FFD_API_KEY", "")
        if not self._key:
            raise ValueError("FFD_API_KEY must be supplied in the environment")
        self.limit = max_points
        self.reserved = 0
        self.halted = False
        self._lock = _NETWORK_LOCK
        self._post = post
        self.receipt_dir = Path(receipt_dir) if receipt_dir is not None else Path(__file__).resolve().parent/'output'/'ffd-request-receipts'

    def history(self, code, start, cutoff, index=False):
        if not re.fullmatch(r"[0-9]{6}\.(SH|SZ)", code):
            raise ValueError("FFD needs an explicit Shanghai/Shenzhen code")
        first, last = dt.date.fromisoformat(start), dt.date.fromisoformat(cutoff)
        if first > last:
            raise ValueError("FFD reversed date range")
        reserve = ((last-first).days+1)*2  # close + volume; identity/time are free
        with self._lock:
            if self.halted:
                raise ValueError("FFD run halted; reconcile original request before retrying")
            if self.reserved+reserve > self.limit:
                raise ValueError("FFD per-run point budget exhausted")
            body = dict(function="history", codes=code, indicators="close,volume",
                        start_date=start, end_date=cutoff, options="CPS:1" if index else "CPS:2",
                        coverage_policy="strict")
            fingerprint = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            self.receipt_dir.mkdir(parents=True, exist_ok=True)
            path = self.receipt_dir/(fingerprint+".json")
            request_id = uuid.uuid4().hex
            receipt = dict(schema="ffd-request-receipt-v1", state="pending", request=body,
                           clientRequestId=request_id, requestFingerprint=fingerprint,
                           createdAt=dt.datetime.now(dt.timezone.utc).isoformat(), reservedPoints=reserve,
                           httpStatus=None, exceptionType=None, serviceRequestId=None)
            # Exclusive creation is the cross-process gate. A crash leaves pending,
            # which is deliberately blocked just like unknown until reconciled.
            try:
                with path.open("x") as f:
                    json.dump(receipt, f, ensure_ascii=False, sort_keys=True)
                    f.flush(); os.fsync(f.fileno())
            except FileExistsError:
                raise ValueError("FFD existing attempt is blocked; inspect persistent receipt before retrying") from None
            self.reserved += reserve

            def persist(state, **fields):
                receipt.update(state=state, updatedAt=dt.datetime.now(dt.timezone.utc).isoformat(), **fields)
                temp = path.with_suffix("."+request_id+".tmp")
                with temp.open("w") as f:
                    json.dump(receipt, f, ensure_ascii=False, sort_keys=True)
                    f.flush(); os.fsync(f.fileno())
                os.replace(temp, path)

            response = None
            try:
                if self._post is None:
                    import requests
                    post = requests.post
                else:
                    post = self._post
                response = post(ENDPOINT, headers={"Authorization": "Bearer "+self._key,
                                "X-Request-ID": request_id, "X-FFD-Client-Request-ID": request_id},
                                json=body, timeout=(10, 180))
                status = response.status_code
                receipt["httpStatus"] = status if isinstance(status, int) else None
                response.raise_for_status()
                payload = response.json()
            except Exception as exc:
                self.halted = True
                # Only the exception class is safe; never message, request or headers.
                kind = type(exc).__name__
                persist("unknown", exceptionType=kind)
                raise ValueError("FFD outcome unknown; no retry; client request "+request_id+"; type "+kind) from None
            if isinstance(payload, dict):
                service_id = payload.get("request_id")
                if isinstance(service_id, str) and re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}",service_id) and service_id != self._key:
                    receipt["serviceRequestId"] = service_id
                used = payload.get("quota_used")
                if isinstance(used, (int,float)) and not isinstance(used,bool) and math.isfinite(used):
                    receipt["reportedQuotaUsed"] = used
            if not isinstance(payload, dict) or payload.get("code") != 200:
                self.halted = True
                persist("rejected")
                raise ValueError("FFD service rejected request; inspect persistent receipt "+request_id)
            try:
                rows = parse_history(payload, code, start, cutoff, index)
            except Exception:
                persist("validation_failed")
                raise ValueError("FFD data validation failed; inspect persistent receipt "+request_id) from None
            persist("completed")
            return rows, payload
