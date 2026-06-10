#!/usr/bin/env python3
"""Upscale README assets with Real-ESRGAN (4x) then cap width for GitHub."""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image
from realesrgan_ncnn_py import Realesrgan

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets"
MAX_WIDTH = 2048


def enhance(src: Path, dst: Path) -> None:
    realesrgan = Realesrgan(gpuid=-1)
    im = Image.open(src).convert("RGB")
    up = realesrgan.process_pil(im)
    if up.width > MAX_WIDTH:
        h = int(up.height * MAX_WIDTH / up.width)
        up = up.resize((MAX_WIDTH, h), Image.Resampling.LANCZOS)
    up.save(dst, "PNG", optimize=True, compress_level=9)
    print(f"{src.name} {im.size} -> {dst.name} {up.size} ({dst.stat().st_size // 1024} KB)")


def main() -> None:
    pairs = [
        (ASSETS / "demo-screenshot.png", ASSETS / "demo-screenshot.png"),
        (ASSETS / "award-ceremony.png", ASSETS / "award-ceremony.png"),
    ]
    # If originals are low-res, pass source paths as CLI args
    if len(sys.argv) >= 3:
        enhance(Path(sys.argv[1]), Path(sys.argv[2]))
        return
    for src, dst in pairs:
        if src.exists():
            enhance(src, dst)


if __name__ == "__main__":
    main()
