"""Opt-in FFD history experiment; no credentials, retries or automatic publication.

Each request reserves the maximum calendar-day cells, not an optimistic trading
calendar. Reservations are not refunded on errors. One client per run serializes
all network requests and stops after an uncertain outcome.
"""
from __future__ import annotations
import datetime as dt
import json
from json import dumps as encode_json
import math
import os
import re
import threading
import hashlib
import uuid
import urllib.request
import urllib.error
from pathlib import Path

ENDPOINT = "https://ffd.findesk.cn/api/query"
EXPERIMENT_SCOPE = "qfq-shsz-ffd-experimental-v1"
_NETWORK_LOCK = threading.Lock()


def parse_history(payload, code, start, cutoff, index=False, expected_dates=None):
    if not isinstance(payload, dict) or payload.get("code") != 200:
        raise ValueError("FFD did not return a successful history response")
    coverage = payload.get("coverage")
    if coverage is None:
        coverage = {}
    if not isinstance(coverage, dict):
        raise ValueError("FFD malformed coverage contract")
    if ("complete" in coverage and coverage["complete"] is not True) or any(coverage.get(k) for k in
            ("partial", "missing_codes", "missing_cells", "missing_cell_count", "shard_errors")):
        raise ValueError("FFD history coverage is incomplete or unknown")
    if coverage.get("complete") is not True and expected_dates is None:
        raise ValueError("FFD missing source coverage requires independent calendar proof")
    # returned_codes/code_identity_checked are annotations added by FFD MCP,
    # not mandatory REST evidence. Verify every native row ourselves below.
    for field in ("requested_codes", "accepted_codes", "returned_codes"):
        if field in coverage and coverage[field] != [code]:
            raise ValueError("FFD coverage identity conflicts with requested code")
    if coverage.get("status", "complete") != "complete":
        raise ValueError("FFD coverage status is not complete")
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
    if expected_dates is not None:
        expected = list(expected_dates)
        if not expected or expected != sorted(set(expected)) or any(not start <= day <= cutoff for day in expected):
            raise ValueError("Invalid independently supplied trading calendar window")
        if dates != expected:
            raise ValueError("FFD calendar coverage gap or unexpected non-trading date")
    return rows


class _JSONResponse:
    def __init__(self, status, headers, raw):
        self.status_code, self.headers, self._raw = status, headers, raw
    def raise_for_status(self):
        pass  # urllib raises HTTPError before creating this object.
    def json(self):
        return json.loads(self._raw.decode("utf-8"))


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None  # Never transmit the credential to a redirected destination.


def _urllib_post(url, *, headers, json, timeout):
    # Same stdlib transport as the official MCP. Default verified TLS/proxy
    # handling is retained. No retry or new CA store; redirects fail closed.
    body = encode_json(json, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.build_opener(_NoRedirect()).open(request, timeout=max(timeout)) as response:
        return _JSONResponse(response.status, response.headers, response.read())


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

    def history(self, code, start, cutoff, index=False, expected_dates=None):
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
                        start_date=start, end_date=cutoff, options="" if index else "CPS:2",
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

            def persist_response(payload):
                # Persist already-parsed JSON before validating charged data.
                # Transport headers are never copied; scrub any reflected key.
                sensitive = {"authorization", "headers", "api_key", "apikey", "access_token"}
                def scrub(value):
                    if isinstance(value, str):
                        return value.replace(self._key, "[REDACTED]")
                    if isinstance(value, list):
                        return [scrub(item) for item in value]
                    if isinstance(value, dict):
                        return {scrub(str(k)): scrub(v) for k,v in value.items() if str(k).lower() not in sensitive}
                    return value
                safe = scrub(payload)
                encoded = json.dumps(safe, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                result_path = self.receipt_dir/(fingerprint+".response.json")
                temp = result_path.with_suffix("."+request_id+".tmp")
                with temp.open("w") as f:
                    f.write(encoded); f.flush(); os.fsync(f.fileno())
                os.replace(temp, result_path)
                receipt.update(responseFile=result_path.name,
                               sanitizedResponseSha256=hashlib.sha256(encoded.encode()).hexdigest(),
                               responseSanitized=True)

            response = None
            try:
                post = self._post or _urllib_post
                response = post(ENDPOINT, headers={"Authorization": "Bearer "+self._key,
                                "Content-Type": "application/json", "User-Agent": "blackhorse-ffd-probe/1.0",
                                "X-Request-ID": request_id, "X-FFD-Client-Request-ID": request_id},
                                json=body, timeout=(10, 180))
                status = response.status_code
                receipt["httpStatus"] = status if isinstance(status, int) else None
                response.raise_for_status()
                payload = response.json()
            except urllib.error.HTTPError as exc:
                self.halted = True
                receipt["httpStatus"] = exc.code
                # A received HTTP error is not an absent response. Retain only
                # published machine fields, never raw text/body or credentials.
                try:
                    error_body = json.loads(exc.read().decode("utf-8"))
                except Exception:
                    error_body = {}
                persist_response(error_body)
                if not isinstance(error_body, dict):
                    error_body = {}
                detail = error_body.get("detail")
                detail = detail if isinstance(detail, dict) else error_body
                safe_fields = {"errorCode": detail.get("error_code") or detail.get("code"),
                               "serviceRequestId": error_body.get("request_id") or detail.get("request_id") or (exc.headers.get("X-Request-ID") if exc.headers else None),
                               "dataChargeStatus": detail.get("data_charge_status")}
                for field, value in safe_fields.items():
                    if isinstance(value, int) and not isinstance(value,bool):
                        receipt[field] = value
                    elif isinstance(value,str) and re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}",value) and self._key not in value:
                        receipt[field] = value
                persist("http_error", exceptionType="HTTPError")
                raise ValueError("FFD HTTP "+str(exc.code)+"; no retry; client request "+request_id) from None
            except Exception as exc:
                self.halted = True
                # Only the exception class is safe; never message, request or headers.
                kind = type(exc).__name__
                persist("unknown", exceptionType=kind)
                raise ValueError("FFD outcome unknown; no retry; client request "+request_id+"; type "+kind) from None
            persist_response(payload)
            persist("response_received")
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
                rows = parse_history(payload, code, start, cutoff, index, expected_dates=expected_dates)
            except Exception:
                persist("validation_failed")
                raise ValueError("FFD data validation failed; inspect persistent receipt "+request_id) from None
            persist("completed")
            return rows, payload
