from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent
UPSTREAM = "http://127.0.0.1:8910/v1/chat/completions"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_OPTIONS(self):
        if self.path == "/v1/chat/completions":
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            return
        super().do_OPTIONS()

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            self.send_error(404, "Not Found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        req = urllib.request.Request(
            UPSTREAM,
            data=body,
            headers={"Content-Type": self.headers.get("Content-Type", "application/json")},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                payload = resp.read()
                status = resp.status
                content_type = resp.headers.get("Content-Type", "application/json; charset=utf-8")
        except urllib.error.HTTPError as err:
            payload = err.read()
            status = err.code
            content_type = err.headers.get("Content-Type", "application/json; charset=utf-8")
        except Exception as err:
            payload = json.dumps({"error": str(err)}).encode("utf-8")
            status = 502
            content_type = "application/json; charset=utf-8"

        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()

    os.chdir(ROOT)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Serving {ROOT} at http://127.0.0.1:{args.port}")
    print(f"Proxying /v1/chat/completions -> {UPSTREAM}")
    server.serve_forever()


if __name__ == "__main__":
    main()
