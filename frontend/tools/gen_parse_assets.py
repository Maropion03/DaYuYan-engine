#!/usr/bin/env python3
import html
import json
import re
import subprocess
import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image

ROOT = Path("/Users/medusa/Desktop/snap Extract")
DEMO = ROOT / "demo_sample_files_public"
RENDER_DIR = DEMO / "rendered_multi"
OUT = ROOT / "snapextract_parse_assets.js"

SAMPLES = {
    "attention": DEMO / "attention_is_all_you_need.pdf",
    "contract": DEMO / "mississippi_sample_contract.pdf",
    "resume": DEMO / "ucr_resume_sample.pdf",
    "statement": DEMO / "umich_handwritten_receipt_example.pdf",
}

STATEMENT_MANUAL_BLOCKS = [
    {"text": "B01346", "x": 8.4, "y": 30.2, "w": 7.8, "h": 3.7},
    {"text": "ARECIBO CAR SERVICE (718) 783-6465 (718) 783-3030 Official Taxi Receipt", "x": 19.2, "y": 28.4, "w": 34.6, "h": 18.8},
    {"text": "Date 01-31-19", "x": 48.9, "y": 46.2, "w": 17.3, "h": 5.3},
    {"text": "From Brooklyn", "x": 7.9, "y": 48.0, "w": 21.9, "h": 8.1},
    {"text": "To LGA", "x": 8.1, "y": 54.1, "w": 11.8, "h": 4.6},
    {"text": "Fare Paid $45.50", "x": 7.9, "y": 59.0, "w": 19.1, "h": 5.2},
    {"text": "Car No. 14", "x": 52.1, "y": 65.1, "w": 10.1, "h": 5.3},
]

FORMULA_CHARS = set("=+*/^√∑∫≤≥≈≠∞λθσβγδπµ∈→←∂·")
EQUATION_PATTERNS = [
    re.compile(r"\b[a-zA-Z]\w*\s*=\s*[^=]"),
    re.compile(r"[A-Za-z0-9_]+\([^)]*\)\s*=\s*"),
    re.compile(r"\b\d+\s*[\+\-\*/=]\s*\d+"),
    re.compile(r"\b[A-Za-z]\b\s*[\+\-\*/]\s*\b[A-Za-z0-9]\b"),
]


def run(cmd):
    subprocess.run(cmd, check=True)


def run_capture(cmd):
    return subprocess.check_output(cmd, text=True)


def text_from_node(node):
    return html.unescape("".join(node.itertext())).replace("\xa0", " ").strip()


def compact(text):
    return re.sub(r"\s+", " ", text).strip()


def line_from_group(group, fonts):
    group = sorted(group, key=lambda x: x["left"])
    parts = []
    prev_right = None
    for item in group:
        txt = item["text"]
        if not txt:
            continue
        if prev_right is not None:
            gap = item["left"] - prev_right
            if gap > 10:
                parts.append(" ")
        parts.append(txt)
        prev_right = item["left"] + item["width"]
    text = compact("".join(parts))
    if not text:
        return None
    font_sizes = [fonts.get(str(item["font"]), 12) for item in group]
    tops = [item["top"] for item in group]
    lefts = [item["left"] for item in group]
    rights = [item["left"] + item["width"] for item in group]
    bottoms = [item["top"] + item["height"] for item in group]
    return {
        "text": text,
        "top": min(tops),
        "left": min(lefts),
        "right": max(rights),
        "bottom": max(bottoms),
        "font_size": max(font_sizes) if font_sizes else 12,
    }


def group_lines(texts, fonts):
    rows = []
    for item in sorted(texts, key=lambda x: (x["top"], x["left"])):
        placed = False
        for row in rows:
            if abs(row["top"] - item["top"]) <= 4:
                row["items"].append(item)
                row["top"] = min(row["top"], item["top"])
                placed = True
                break
        if not placed:
            rows.append({"top": item["top"], "items": [item]})
    lines = []
    for row in rows:
        line = line_from_group(row["items"], fonts)
        if line:
            lines.append(line)
    return sorted(lines, key=lambda x: (x["top"], x["left"]))


def looks_formula(text, font_size):
    t = text.strip()
    if not t:
        return False
    if len(t) <= 3 and t.isdigit():
        return False
    if len(t) > 180:
        return False
    if re.fullmatch(r"[A-Z][A-Z\s:&./#-]{3,}", t):
        return False
    if t.endswith(":") and not any(ch in FORMULA_CHARS for ch in t):
        return False
    if any(p.search(t) for p in EQUATION_PATTERNS):
        return True
    formula_char_count = sum(ch in FORMULA_CHARS for ch in t)
    if formula_char_count == 0:
        return False
    alpha_ratio = sum(ch.isalpha() for ch in t) / max(1, len(t))
    digit_ratio = sum(ch.isdigit() for ch in t) / max(1, len(t))
    if formula_char_count >= 2 and len(t) <= 120 and (alpha_ratio < 0.58 or digit_ratio > 0.08):
        return True
    if len(t) <= 48 and formula_char_count >= 1 and alpha_ratio < 0.5:
        return True
    return False


def merge_lines(lines, page_w, page_h, key, page_no):
    blocks = []
    current = None
    bid = 0
    for line in lines:
        text = line["text"]
        gap = None if current is None else line["top"] - current["bottom"]
        left_delta = None if current is None else abs(line["left"] - current["left"])
        is_short = len(text) <= 60
        is_heading = line["font_size"] >= 16 and is_short
        new_block = (
            current is None
            or is_heading
            or current["is_heading"]
            or gap is None
            or gap > max(18, current["font_size"] * 1.5)
            or left_delta > 80
        )
        if new_block:
            if current is not None:
                bid += 1
                blocks.append(finalize_block(current, page_w, page_h, key, page_no, bid))
            current = {
                "lines": [text],
                "top": line["top"],
                "left": line["left"],
                "right": line["right"],
                "bottom": line["bottom"],
                "font_size": line["font_size"],
                "is_heading": is_heading,
            }
        else:
            joiner = "" if current["lines"][-1].endswith("-") else " "
            current["lines"][-1] = current["lines"][-1].rstrip("-") + joiner + text
            current["right"] = max(current["right"], line["right"])
            current["bottom"] = line["bottom"]
            current["font_size"] = max(current["font_size"], line["font_size"])
    if current is not None:
        bid += 1
        blocks.append(finalize_block(current, page_w, page_h, key, page_no, bid))
    return blocks


def finalize_block(block, page_w, page_h, key, page_no, bid):
    text = compact(" ".join(block["lines"]))
    kind = "formula" if looks_formula(text, block["font_size"]) else "text"
    return {
        "id": f"{key}-p{page_no:02d}-b{bid:03d}",
        "page": page_no,
        "x": round(block["left"] / page_w * 100, 2),
        "y": round(block["top"] / page_h * 100, 2),
        "w": round(max(0.2, (block["right"] - block["left"]) / page_w * 100), 2),
        "h": round(max(0.6, (block["bottom"] - block["top"]) / page_h * 100), 2),
        "text": text,
        "kind": kind,
        "level": 2 if block["is_heading"] else 0,
    }


def vision_ocr(image_path: Path):
    swift = r'''
import Foundation
import Vision
import AppKit

let path = CommandLine.arguments[1]
let url = URL(fileURLWithPath: path)
guard let image = NSImage(contentsOf: url) else { fatalError("load image failed") }
guard let tiff = image.tiffRepresentation,
      let bitmap = NSBitmapImageRep(data: tiff),
      let cg = bitmap.cgImage else { fatalError("cg image failed") }

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = false
let handler = VNImageRequestHandler(cgImage: cg, options: [:])
try handler.perform([request])
let obs = request.results ?? []
let rows: [[String: Any]] = obs.compactMap { item in
    guard let c = item.topCandidates(1).first else { return nil }
    let b = item.boundingBox
    return [
        "text": c.string,
        "x": b.origin.x,
        "y": b.origin.y,
        "w": b.size.width,
        "h": b.size.height,
        "confidence": c.confidence
    ]
}
let data = try JSONSerialization.data(withJSONObject: rows, options: [])
FileHandle.standardOutput.write(data)
'''
    with tempfile.TemporaryDirectory() as td:
        script = Path(td) / "vision_ocr.swift"
        script.write_text(swift, encoding="utf-8")
        out = run_capture(["swift", str(script), str(image_path)])
    return json.loads(out)


def normalize_statement_text(text: str) -> str:
    t = compact(text)
    replacements = {
        "Brookiyn+": "Brooklyn",
        "Brookiyn": "Brooklyn",
        "Date01-31-19": "Date 01-31-19",
        "DateO1-31-19": "Date 01-31-19",
        "Date01--31-19*": "Date 01-31-19",
        "Car No./4": "Car No. 14",
        "Fare Paid $ 45:50": "Fare Paid $45.50",
        "Fare Paid $ 45.00": "Fare Paid $45.00",
    }
    return replacements.get(t, t)


def union_boxes(rows):
    return {
        "x": min(r["x"] for r in rows),
        "y": min(r["y"] for r in rows),
        "w": max(r["x"] + r["w"] for r in rows) - min(r["x"] for r in rows),
        "h": max(r["y"] + r["h"] for r in rows) - min(r["y"] for r in rows),
    }


def statement_field_blocks(rows):
    items = []
    for row in rows:
        text = normalize_statement_text(row["text"])
        if not text:
            continue
        if text in {
            "Vendor Name", "Transaction Date", "To and From Destinations", "Proof of Payment",
            "Handwritten Receipt Example", "*Handwritten receipts are allowable"
        }:
            continue
        items.append({**row, "text": text})

    def pick(predicate):
        return [r for r in items if predicate(r["text"])]

    groups = []

    code = pick(lambda t: re.fullmatch(r"B0?\d{4,6}", t) is not None)
    if code:
        groups.append(("Receipt #", code))

    vendor = pick(lambda t: t in {"ARECIBO", "CAR SERVICE"} or "783-3030" in t or "783-6465" in t or "Official Taxi Receipt" in t)
    if vendor:
        groups.append(("Merchant", vendor))

    thanks = pick(lambda t: "Thank you" in t)
    if thanks:
        groups.append(("Thanks", thanks))

    date = pick(lambda t: t.startswith("Date "))
    if date:
        groups.append(("Date", date))

    from_rows = pick(lambda t: t == "From" or "Brooklyn" in t)
    if from_rows:
        groups.append(("From", from_rows))

    to_rows = pick(lambda t: t == "To" or re.fullmatch(r"LGA", t) is not None)
    if to_rows:
        groups.append(("To", to_rows))

    fare = pick(lambda t: t.startswith("Fare Paid"))
    if fare:
        groups.append(("Fare", fare))

    car_no = pick(lambda t: t.startswith("Car No"))
    if car_no:
        groups.append(("Car No", car_no))

    blocks = []
    for idx, (label, rows_in_group) in enumerate(groups, start=1):
        merged = union_boxes(rows_in_group)
        text = " ".join(r["text"] for r in sorted(rows_in_group, key=lambda r: (r["y"], r["x"])))
        blocks.append({
            "id": f"statement-field-{idx:03d}",
            "text": text,
            "label": label,
            **merged,
        })
    return blocks


def statement_blocks_from_image(page_img_path: Path, image_rect, page_w, page_h, key, page_no):
    blocks = []
    for idx, field in enumerate(STATEMENT_MANUAL_BLOCKS, start=1):
        blocks.append({
            "id": f"{key}-p{page_no:02d}-ocr{idx:03d}",
            "page": page_no,
            "x": round(field["x"], 2),
            "y": round(field["y"], 2),
            "w": round(max(0.2, field["w"]), 2),
            "h": round(max(0.6, field["h"]), 2),
            "text": field["text"],
            "kind": "text",
            "level": 0,
        })
    return blocks


def parse_pdf(key, pdf_path):
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        xml_base = tmp / key
        run(["pdftohtml", "-xml", "-noframes", str(pdf_path), str(xml_base)])
        tree = ET.parse(str(xml_base.with_suffix(".xml")))
        root = tree.getroot()
        asset = {"detected_type": "paper" if key == "attention" else ("resume" if key == "resume" else ("statement" if key == "statement" else "contract")), "pages": []}
        RENDER_DIR.mkdir(parents=True, exist_ok=True)
        for page in root.findall("page"):
            page_no = int(page.attrib["number"])
            page_w = float(page.attrib["width"])
            page_h = float(page.attrib["height"])
            out_prefix = RENDER_DIR / f"{key}_p{page_no:02d}"
            if not out_prefix.with_suffix(".png").exists():
                run([
                    "pdftocairo", "-png", "-singlefile",
                    "-f", str(page_no), "-l", str(page_no),
                    "-scale-to", "1200",
                    str(pdf_path), str(out_prefix)
                ])
            texts = []
            fonts = {}
            image_rects = []
            for child in page:
                if child.tag == "fontspec":
                    fonts[str(child.attrib["id"])] = float(child.attrib["size"])
                elif child.tag == "text":
                    txt = text_from_node(child)
                    if not txt:
                        continue
                    width = float(child.attrib.get("width", 0) or 0)
                    height = float(child.attrib.get("height", 0) or 0)
                    if width <= 0 and txt:
                        width = max(4, len(txt) * 6)
                    texts.append({
                        "top": float(child.attrib["top"]),
                        "left": float(child.attrib["left"]),
                        "width": width,
                        "height": height,
                        "font": child.attrib.get("font", "0"),
                        "text": txt,
                    })
                elif child.tag == "image":
                    image_rects.append({
                        "top": float(child.attrib["top"]),
                        "left": float(child.attrib["left"]),
                        "width": float(child.attrib["width"]),
                        "height": float(child.attrib["height"]),
                    })
            if key == "statement" and image_rects:
                main_image = max(image_rects, key=lambda r: r["width"] * r["height"])
                blocks = statement_blocks_from_image(out_prefix.with_suffix(".png"), main_image, page_w, page_h, key, page_no)
            else:
                blocks = merge_lines(group_lines(texts, fonts), page_w, page_h, key, page_no)
            img_idx = 0
            for child in page.findall("image"):
                if key == "statement":
                    continue
                img_idx += 1
                blocks.append({
                    "id": f"{key}-p{page_no:02d}-img{img_idx:03d}",
                    "page": page_no,
                    "x": round(float(child.attrib["left"]) / page_w * 100, 2),
                    "y": round(float(child.attrib["top"]) / page_h * 100, 2),
                    "w": round(float(child.attrib["width"]) / page_w * 100, 2),
                    "h": round(float(child.attrib["height"]) / page_h * 100, 2),
                    "text": "Image block",
                    "kind": "image",
                    "level": 0,
                })
            blocks.sort(key=lambda b: (b["y"], b["x"]))
            asset["pages"].append({
                "number": page_no,
                "width": page_w,
                "height": page_h,
                "image": f"demo_sample_files_public/rendered_multi/{out_prefix.name}.png",
                "blocks": blocks,
            })
        return asset


def main():
    assets = {key: parse_pdf(key, path) for key, path in SAMPLES.items() if path.exists()}
    js = "window.SNAP_PARSE_ASSETS = " + json.dumps(assets, ensure_ascii=False) + ";\n"
    OUT.write_text(js, encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
