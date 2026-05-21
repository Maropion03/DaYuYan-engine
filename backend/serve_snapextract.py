import argparse
import http.client
import os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit


DEFAULT_FRONTEND_DIR = Path(
    r"C:\Users\1\Documents\Codex\2026-05-13\files-mentioned-by-the-user-codex\snap--extract-frontend"
)
DEFAULT_BACKEND = "http://127.0.0.1:8910"
DEFAULT_SCENE_RUNTIME = "http://127.0.0.1:8766"


class SnapExtractHandler(SimpleHTTPRequestHandler):
    frontend_dir = DEFAULT_FRONTEND_DIR
    backend = urlsplit(DEFAULT_BACKEND)
    scene_runtime = urlsplit(DEFAULT_SCENE_RUNTIME)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(self.frontend_dir), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_OPTIONS(self):
        if self.path.startswith("/v1/") or self.path == "/api/scene-analysis/run":
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.end_headers()
            return
        super().do_OPTIONS()

    def do_GET(self):
        if self.path == "/":
            self.path = "/snapextract_v3.html"
        if self.path.startswith("/v1/"):
            self._proxy_request("GET", self.backend)
            return
        if self.path == "/api/scene-analysis/run":
            self._proxy_request("GET", self.scene_runtime)
            return
        super().do_GET()

    def do_POST(self):
        if self.path.startswith("/v1/"):
            self._proxy_request("POST", self.backend)
            return
        if self.path == "/api/scene-analysis/run":
            self._proxy_request("POST", self.scene_runtime)
            return
        self.send_error(405, "Unsupported method")

    def _proxy_request(self, method: str, target):
        body = None
        if method in {"POST", "PUT", "PATCH"}:
            length = int(self.headers.get("Content-Length", "0") or "0")
            body = self.rfile.read(length) if length else None

        conn = http.client.HTTPConnection(
            target.hostname,
            target.port or 80,
            timeout=600,
        )
        try:
            headers = {
                key: value
                for key, value in self.headers.items()
                if key.lower() not in {"host", "content-length", "connection"}
            }
            conn.request(method, self.path, body=body, headers=headers)
            resp = conn.getresponse()
            data = resp.read()

            self.send_response(resp.status, resp.reason)
            for key, value in resp.getheaders():
                lower = key.lower()
                if lower in {"content-length", "connection", "transfer-encoding"}:
                    continue
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            if data:
                self.wfile.write(data)
        except Exception as exc:
            self.send_error(502, f"Proxy error: {exc}")
        finally:
            conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--frontend-dir", default=str(DEFAULT_FRONTEND_DIR))
    parser.add_argument("--backend", default=DEFAULT_BACKEND)
    parser.add_argument("--scene-runtime", default=DEFAULT_SCENE_RUNTIME)
    args = parser.parse_args()

    SnapExtractHandler.frontend_dir = Path(args.frontend_dir)
    SnapExtractHandler.backend = urlsplit(args.backend)
    SnapExtractHandler.scene_runtime = urlsplit(args.scene_runtime)

    os.chdir(SnapExtractHandler.frontend_dir)
    server = ThreadingHTTPServer((args.host, args.port), SnapExtractHandler)
    print(f"Serving frontend: http://{args.host}:{args.port}/snapextract_v3.html")
    print(f"Proxying /v1/* -> {args.backend}")
    print(f"Proxying /api/scene-analysis/run -> {args.scene_runtime}")
    server.serve_forever()


if __name__ == "__main__":
    main()
