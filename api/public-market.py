"""Bounded public-data refresh; no keys or per-stock history fan-out."""
import json
import sys
import time
from http.server import BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from refresh_public_breadth import preview

_cache=None
_saved_at=0

def payload():
    global _cache,_saved_at
    if _cache is not None and time.time()-_saved_at<1800:
        return _cache
    _cache=preview()
    _saved_at=time.time()
    return _cache

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            body=json.dumps(payload(),ensure_ascii=False).encode()
            status=200
        except Exception as exc:
            body=json.dumps(dict(error=str(exc)[:200]),ensure_ascii=False).encode()
            status=503
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','public, max-age=60, s-maxage=300' if status==200 else 'no-store')
        self.end_headers()
        self.wfile.write(body)
