## Local OCR Setup

### Python environment

- Environment path: `C:\Users\1\Documents\Codex\2026-05-13\ocr-qwen-ai\.conda-ocr`
- Python version: `3.10`

Activate with:

```powershell
conda activate C:\Users\1\Documents\Codex\2026-05-13\ocr-qwen-ai\.conda-ocr
```

### Installed packages

- `paddlepaddle==2.6.2`
- `paddleocr==2.7.3`
- `pytesseract`

### Tesseract

- Engine installed via `winget`
- Binary directory: `C:\Program Files\Tesseract-OCR`
- Project tessdata directory: `C:\Users\1\Documents\Codex\2026-05-13\ocr-qwen-ai\tessdata`

Available project languages:

- `chi_sim`
- `eng`
- `osd`

Use Tesseract with:

```powershell
$env:PATH += ';C:\Program Files\Tesseract-OCR'
$env:TESSDATA_PREFIX = 'C:\Users\1\Documents\Codex\2026-05-13\ocr-qwen-ai\tessdata'
tesseract input.png stdout -l chi_sim+eng
```

### Quick verification

Tesseract:

```powershell
$env:PATH += ';C:\Program Files\Tesseract-OCR'
$env:TESSDATA_PREFIX = 'C:\Users\1\Documents\Codex\2026-05-13\ocr-qwen-ai\tessdata'
tesseract 'C:\Users\1\Downloads\FireShot\FireShot Capture 002 - SoMark 文档智能 - [somark.tech].png' stdout -l chi_sim+eng
```

PaddleOCR:

```powershell
& 'C:\Users\1\Documents\Codex\2026-05-13\ocr-qwen-ai\.conda-ocr\python.exe' -c "from paddleocr import PaddleOCR; ocr=PaddleOCR(use_angle_cls=True, lang='ch', show_log=False); res=ocr.ocr(r'C:\Users\1\Downloads\FireShot\FireShot Capture 002 - SoMark 文档智能 - [somark.tech].png', cls=True); print('\n'.join([item[1][0] for page in res if page for item in page][:12]))"
```
