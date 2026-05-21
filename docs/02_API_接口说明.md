# 答于言 · API 接口说明

> 本文件介绍提交包中三个本地后端服务（8000 / 8765 / 8766）暴露的接口。Qwen 推理服务（8910）走 OpenAI 兼容协议，不在此处展开。

---

## 一、前端静态服务 · port 8000

由 `serve_snapextract.py` 提供，仅静态文件服务，无业务接口。

| 路径 | 用途 |
|------|------|
| `/snapextract_v3.html` | 主应用入口 |
| `/snapextract_parse_assets.js` | 辅助资源 |
| `/vendor/pdfjs/*` | PDF.js 离线资源 |
| `/demo_sample_files_public/samples/*` | 4 场景演示样例文件 |

---

## 二、多模态代理 · port 8765

由 `proxy.py` 提供，三类接口。

### 2.1 POST `/chat`

转发 OpenAI 风格请求到 Qwen NPU 服务（:8910）。

**请求体：**
```json
{
  "model": "qwen2.5vl3b",
  "messages": [
    {"role": "user", "content": [
      {"type": "text", "text": "..."},
      {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
    ]}
  ],
  "temperature": 0.05,
  "max_tokens": 620,
  "presence_penalty": 1.2,
  "frequency_penalty": 0.8,
  "stop": ["\n```", "\n\n\n\n\n\n"]
}
```

**响应：** SSE 流式，每帧为标准 OpenAI delta 格式。

**注意：**
- Qwen2.5-VL-3B 上下文上限 2048 token，prompt + 图像 + 输出之和必须满足
- 超限时 Qwen 返回 `{"error": "Model query unavailable"}`

### 2.2 POST `/ocr`

调用本地 Tesseract OCR。

**请求体：**
```json
{
  "image_base64": "...",
  "lang": "chi_sim+eng"
}
```

**响应：**
```json
{
  "text": "...",
  "backend": "tesseract",
  "lang": "chi_sim+eng",
  "duration_ms": 1234
}
```

### 2.3 POST `/pdf`

使用 PyMuPDF 抽取 PDF 文本层（不走 OCR，速度极快，但要求 PDF 有嵌入文字）。

**请求体：**
```json
{
  "pdf_base64": "...",
  "max_pages": 5
}
```

**响应：**
```json
{
  "text": "...",
  "pages": 4,
  "backend": "pdf-text",
  "kind": "pdf_ocr"
}
```

---

## 三、场景分析后端 · port 8766

由 `scene_runtime/app.py`（FastAPI）提供。

### 3.1 POST `/api/scene-analysis/run`

执行单一场景的深度分析。

**请求体：**
```json
{
  "request_id": "task_xxx",
  "scene": "paper | resume | contract | statement",
  "main_file": {
    "name": "xxx.pdf",
    "mime": "application/pdf",
    "size": 12345,
    "data_url": "data:application/pdf;base64,..."
  },
  "supplement": {
    "mode": "file | form",
    "file": { /* 同 main_file，可选 */ },
    "form": { /* 自由 KV，如 JD 文本、研究方向等 */ }
  },
  "runtime": {},
  "output_options": {}
}
```

**响应：** 因场景而异，统一外壳：

```json
{
  "status": "ok | failed",
  "decision": "...",
  "confidence": "high | medium | low",
  "summary": "...",
  "facts": { /* 场景专属字段 */ }
}
```

详细 facts 结构详见 `scene_runtime/contracts.py`。

### 3.2 OPTIONS `/api/scene-analysis/run`

CORS 预检。

---

## 四、Qwen 推理服务 · port 8910（外部依赖）

由 Snapdragon SDK 的 `GenieAPIService.exe` 提供，OpenAI 协议兼容子集。

| 路径 | 用途 |
|------|------|
| GET `/v1/models` | 列出已加载模型 |
| POST `/v1/chat/completions` | Chat completion（SSE） |

本项目仅用 `qwen2.5vl3b` 一个模型，由 8765 端口的 proxy.py 统一转发。

---

