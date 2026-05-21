#!/usr/bin/env python3
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scene_runtime.contracts import build_error_result
from scene_runtime.server import handle_scene_analysis


class SceneRuntimeHandler(BaseHTTPRequestHandler):
    def _set_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, status_code: int, payload) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(data)

    def _send_empty(self, status_code: int) -> None:
        self.send_response(status_code)
        self.send_header("Content-Length", "0")
        self._set_cors_headers()
        self.end_headers()

    def do_OPTIONS(self) -> None:
        if self.path != "/api/scene-analysis/run":
            self._send_empty(404)
            return
        self._send_empty(204)

    def do_POST(self) -> None:
        if self.path != "/api/scene-analysis/run":
            self._send_empty(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(body or "{}")
        except json.JSONDecodeError:
            self._send_json(
                400,
                build_error_result(
                    request_id="",
                    scene="",
                    message="malformed json",
                ),
            )
            return
        result = handle_scene_analysis(payload)
        self._send_json(200, result)


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8766), SceneRuntimeHandler)
    print("scene runtime listening on http://127.0.0.1:8766")
    server.serve_forever()


if __name__ == "__main__":
    main()
