"""Minimal HTTP server (PRD v0.3, Tier 1).

Python standard library only: http.server ThreadingHTTPServer.
Run:  python server.py
Then open http://localhost:8000 in a browser.

JSON endpoints (Tier 1 only, so no 429 / fail-open here - that is Tier 2):
  POST /api/request  {"client": "192.0.2.10"}
      -> {"allowed": true/false, "remaining_tokens": 9, ...}  (always HTTP 200)
  POST /api/burst    {"client": "...", "count": 15}
      -> {"allowed": 10, "denied": 5, "results": [...]}
  POST /api/config   {"capacity": 10, "refill_rate": 2}
      -> HTTP 400 + {"error": "..."} if invalid, config unchanged
  POST /api/reset    {}
  GET  /api/config   -> current config
  GET  /api/status?client=...  -> remaining tokens for that client
  GET  /api/stats    -> allowed / denied totals
"""
import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from limiter.config import PRESET_CLIENTS, validate_client_key
from limiter.store import BucketStore

HOST = "127.0.0.1"
PORT = 8000
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

store = BucketStore()
recent = []  # last 20 decisions, newest first; in memory only


def _send_json(handler, status, payload):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _read_json(handler):
    length = int(handler.headers.get("Content-Length") or 0)
    if not length:
        return {}
    return json.loads(handler.rfile.read(length).decode("utf-8") or "{}")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def log_message(self, *args):  # keep the terminal clean for the demo
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.path = "/index.html"
            return super().do_GET()
        if parsed.path == "/api/config":
            return _send_json(self, 200, {
                "capacity": store.capacity,
                "refill_rate": store.refill_rate,
                "cost": store.cost,
                "preset_clients": PRESET_CLIENTS,
            })
        if parsed.path == "/api/stats":
            stats = store.stats()
            stats["recent"] = recent[:20]
            return _send_json(self, 200, stats)
        if parsed.path == "/api/status":
            client = parse_qs(parsed.query).get("client", [""])[0]
            try:
                validate_client_key(client)
            except ValueError as exc:
                return _send_json(self, 400, {"error": str(exc)})
            return _send_json(self, 200, store.status(client))
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            data = _read_json(self)
        except (json.JSONDecodeError, ValueError):
            return _send_json(self, 400, {"error": "Request body must be JSON."})

        if parsed.path == "/api/request":
            client = data.get("client") or data.get("client_ip") or ""
            try:
                result = store.allow(client)
            except ValueError as exc:
                return _send_json(self, 400, {"error": str(exc)})
            recent.insert(0, result)
            del recent[20:]
            return _send_json(self, 200, result)

        if parsed.path == "/api/burst":
            client = data.get("client") or data.get("client_ip") or ""
            try:
                count = int(data.get("count", 15))
            except (TypeError, ValueError):
                return _send_json(self, 400, {"error": "count must be a whole number."})
            if not 1 <= count <= 100:
                return _send_json(self, 400, {"error": "count must be from 1 to 100."})
            try:
                results = [store.allow(client) for _ in range(count)]
            except ValueError as exc:
                return _send_json(self, 400, {"error": str(exc)})
            for result in results:
                recent.insert(0, result)
            del recent[20:]
            allowed = sum(1 for r in results if r["allowed"])
            return _send_json(self, 200, {
                "client": client, "allowed": allowed,
                "denied": len(results) - allowed, "results": results,
            })

        if parsed.path == "/api/config":
            try:
                store.set_config(data.get("capacity"), data.get("refill_rate"))
            except ValueError as exc:
                return _send_json(self, 400, {"error": str(exc)})
            recent.clear()
            return _send_json(self, 200, {
                "capacity": store.capacity, "refill_rate": store.refill_rate,
            })

        if parsed.path == "/api/reset":
            store.reset()
            recent.clear()
            return _send_json(self, 200, {"ok": True})

        return _send_json(self, 404, {"error": "Unknown endpoint."})


if __name__ == "__main__":
    print(f"Rate limiter demo running at http://{HOST}:{PORT}")
    print("Defaults: capacity 10, refill 2 tokens/second. Press Ctrl+C to stop.")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
