#!/usr/bin/env python3
import base64
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "snapextract_local_config.json"
OCR_HELPER = ROOT / "tools" / "local_ocr_extract.py"

DEFAULT_CONFIG = {
    "local_qwen_base": "http://127.0.0.1:8910/v1",
    "local_qwen_path": "/chat/completions",
    "model": "qwen2.5vl3b",
    "fallback_models": ["qwen2.5vl3b"],
    "host": "127.0.0.1",
    "port": 8765,
    "ocr_enabled": True,
    "ocr_python": "C:\\Users\\1\\Documents\\Codex\\2026-05-13\\ocr-qwen-ai\\.conda-ocr\\python.exe",
    "ocr_backend": "auto",
    "ocr_lang": "zh",
    "ocr_max_pages": 4,
    "tesseract_cmd": "",
    "tessdata_prefix": "C:\\Users\\1\\Documents\\Codex\\2026-05-13\\ocr-qwen-ai\\tessdata",
}


def load_config():
    config = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        loaded = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            config.update({k: v for k, v in loaded.items() if v not in (None, "")})

    env_map = {
        "LOCAL_QWEN_BASE": "local_qwen_base",
        "LOCAL_QWEN_PATH": "local_qwen_path",
        "LOCAL_QWEN_MODEL": "model",
        "OCR_PYTHON": "ocr_python",
        "OCR_BACKEND": "ocr_backend",
        "OCR_LANG": "ocr_lang",
        "TESSERACT_CMD": "tesseract_cmd",
        "TESSDATA_PREFIX": "tessdata_prefix",
    }
    for env_name, key in env_map.items():
        value = os.environ.get(env_name)
        if value:
            config[key] = value

    if os.environ.get("HOST"):
        config["host"] = os.environ["HOST"]
    if os.environ.get("PORT"):
        config["port"] = int(os.environ["PORT"])

    config["local_qwen_base"] = str(config["local_qwen_base"]).rstrip("/")
    path = str(config["local_qwen_path"]).strip()
    config["local_qwen_path"] = path if path.startswith("/") else f"/{path}"
    config["fallback_models"] = [
        m for m in config.get("fallback_models", []) if isinstance(m, str) and m.strip()
    ] or [config["model"]]
    config["ocr_enabled"] = bool(config.get("ocr_enabled", True))
    config["ocr_max_pages"] = int(config.get("ocr_max_pages") or 4)
    config["port"] = int(config["port"])
    return config


CONFIG = load_config()


def sse(obj):
    return ("data: " + json.dumps(obj, ensure_ascii=False) + "\n\n").encode("utf-8")


def json_response(handler, code, body):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(data)


def decode_uploaded_file(body):
    file_name = str(body.get("file_name") or "").strip()
    file_type = str(body.get("file_type") or "").strip()
    file_bytes_b64 = body.get("file_bytes_b64")
    if not file_name or not isinstance(file_bytes_b64, str) or not file_bytes_b64:
        raise ValueError("missing file payload")
    raw = base64.b64decode(file_bytes_b64)
    return file_name, file_type, raw


def run_local_ocr(file_name, file_type, raw):
    if not CONFIG["ocr_enabled"]:
        return {"ok": False, "error": "ocr_disabled", "text": "", "kind": "ocr"}

    py = Path(str(CONFIG["ocr_python"]))
    if not py.exists():
        return {"ok": False, "error": f"ocr_python_not_found: {py}", "text": "", "kind": "ocr"}
    if not OCR_HELPER.exists():
        return {"ok": False, "error": f"ocr_helper_not_found: {OCR_HELPER}", "text": "", "kind": "ocr"}

    suffix = Path(file_name).suffix or ".bin"
    with tempfile.TemporaryDirectory(prefix="snapextract_ocr_") as tmpdir:
        file_path = Path(tmpdir) / f"upload{suffix}"
        file_path.write_bytes(raw)
        cmd = [
            str(py),
            str(OCR_HELPER),
            "--input",
            str(file_path),
            "--backend",
            str(CONFIG["ocr_backend"]),
            "--lang",
            str(CONFIG["ocr_lang"]),
            "--max-pages",
            str(CONFIG["ocr_max_pages"]),
        ]
        env = os.environ.copy()
        if CONFIG.get("tesseract_cmd"):
            env["SNAP_TESSERACT_CMD"] = str(CONFIG["tesseract_cmd"])
        if CONFIG.get("tessdata_prefix"):
            env["TESSDATA_PREFIX"] = str(CONFIG["tessdata_prefix"])
        try:
            proc = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="ignore",
                env=env,
                timeout=180,
            )
            result = json.loads(proc.stdout or "{}")
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            stdout = (exc.stdout or "").strip()
            detail = stderr or stdout or str(exc)
            return {
                "ok": False,
                "error": f"ocr_failed: {detail[:1200]}",
                "text": "",
                "kind": "ocr",
                "backend": CONFIG["ocr_backend"],
            }
        except Exception as exc:
            return {
                "ok": False,
                "error": f"ocr_failed: {exc}",
                "text": "",
                "kind": "ocr",
                "backend": CONFIG["ocr_backend"],
            }

    if not isinstance(result, dict):
        return {"ok": False, "error": "ocr_invalid_output", "text": "", "kind": "ocr"}
    result.setdefault("text", "")
    result.setdefault("kind", "ocr")
    result.setdefault("backend", CONFIG["ocr_backend"])
    result["text"] = str(result.get("text") or "")[:20000]
    return result


def build_openai_payload(body):
    model = body.get("model") or CONFIG["model"]
    messages = body.get("messages")
    if isinstance(messages, list) and messages:
        payload_messages = messages
    else:
        system = str(body.get("system") or "").strip()
        prompt = str(body.get("prompt") or "").strip()
        payload_messages = []
        if system:
            payload_messages.append({"role": "system", "content": system})
        payload_messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "stream": True,
        "messages": payload_messages,
    }
    for key in ("temperature", "max_tokens", "top_p", "presence_penalty", "frequency_penalty"):
        val = body.get(key)
        if isinstance(val, (int, float)):
            payload[key] = val
    stop = body.get("stop")
    if isinstance(stop, (list, str)):
        payload["stop"] = stop
    return payload


def build_request(payload):
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    return urllib.request.Request(
        f"{CONFIG['local_qwen_base']}{CONFIG['local_qwen_path']}",
        # GenieAPIService is more reliable when non-ASCII text is JSON-escaped.
        # Raw UTF-8 Chinese can be mis-decoded by the service before tokenization.
        data=json.dumps(payload, ensure_ascii=True).encode("ascii"),
        headers=headers,
        method="POST",
    )


def extract_delta(obj):
    choices = obj.get("choices") or []
    if not choices:
        return ""
    choice = choices[0] or {}
    delta = choice.get("delta") or {}
    if isinstance(delta, dict) and isinstance(delta.get("content"), str):
        return delta["content"]
    message = choice.get("message") or {}
    if isinstance(message, dict) and isinstance(message.get("content"), str):
        return message["content"]
    return ""


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path != "/health":
            self.send_response(404)
            self.end_headers()
            return
        json_response(
            self,
            200,
            {
                "ok": True,
                "provider": "local-qwen-runtime",
                "local_qwen_base": CONFIG["local_qwen_base"],
                "local_qwen_path": CONFIG["local_qwen_path"],
                "model": CONFIG["model"],
                "ocr_enabled": CONFIG["ocr_enabled"],
                "ocr_backend": CONFIG["ocr_backend"],
                "port": CONFIG["port"],
            },
        )

    def do_POST(self):
        if self.path == "/ocr":
            self.handle_ocr()
            return
        if self.path == "/chat":
            self.handle_chat()
            return
        self.send_response(404)
        self.end_headers()

    def handle_ocr(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            file_name, file_type, raw = decode_uploaded_file(body)
        except Exception as exc:
            json_response(self, 400, {"ok": False, "error": str(exc)})
            return

        result = run_local_ocr(file_name, file_type, raw)
        result["file_name"] = file_name
        result["file_type"] = file_type
        result["ok"] = bool(result.get("text")) and not result.get("error")
        json_response(self, 200, result)

    def handle_chat(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            self.send_response(400)
            self.end_headers()
            return

        payload = build_openai_payload(body)
        candidates = [payload["model"]] + [
            m for m in CONFIG["fallback_models"] if m != payload["model"]
        ]

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")
        self._cors()
        self.end_headers()

        last_error = None
        for model_name in candidates:
            payload["model"] = model_name
            req = build_request(payload)
            try:
                with urllib.request.urlopen(req, timeout=180) as resp:
                    for raw in resp:
                        line = raw.decode("utf-8", errors="ignore").strip()
                        if not line or not line.startswith("data:"):
                            continue
                        data = line[5:].strip()
                        if data == "[DONE]":
                            self.wfile.write(b"data: [DONE]\n\n")
                            self.wfile.flush()
                            return
                        try:
                            obj = json.loads(data)
                        except Exception:
                            continue
                        delta = extract_delta(obj)
                        if delta:
                            self.wfile.write(sse({"t": delta}))
                            self.wfile.flush()
                return
            except urllib.error.HTTPError as exc:
                msg = exc.read().decode("utf-8", errors="ignore")[:400]
                last_error = f"upstream {exc.code}: {msg}"
            except Exception as exc:
                last_error = str(exc)

        self.wfile.write(sse({"err": last_error or "upstream request failed"}))
        self.wfile.flush()

    def log_message(self, fmt, *args):
        sys.stderr.write("[proxy] " + (fmt % args) + "\n")


if __name__ == "__main__":
    print(f"[proxy] listening on http://{CONFIG['host']}:{CONFIG['port']}", file=sys.stderr)
    print(f"[proxy] local llm = {CONFIG['local_qwen_base']}{CONFIG['local_qwen_path']}", file=sys.stderr)
    print(f"[proxy] model     = {CONFIG['model']}", file=sys.stderr)
    print(f"[proxy] ocr       = {CONFIG['ocr_enabled']} ({CONFIG['ocr_backend']})", file=sys.stderr)
    ThreadingHTTPServer((CONFIG["host"], CONFIG["port"]), Handler).serve_forever()
