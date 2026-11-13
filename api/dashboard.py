from __future__ import annotations

import json
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard_delivery import build_delivery


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        force = params.get("force", ["0"])[0] == "1"
        try:
            payload = build_delivery(force=force)
            status = 200
        except Exception:
            # Do not expose local paths, source bodies, or stack traces.
            payload = {'status': 'unavailable', 'error': 'dashboard_observation_unavailable',
                       'message': '观察快照或宽度数据暂不可用；未生成新的市场结论。'}
            status = 503
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Allow", "GET, OPTIONS")
        self.end_headers()
