#!/usr/bin/env python3
"""Переносит выбранные кандидаты в textures/ под именем артикула.

AVIF Pillow не читает, поэтому конвертируем через системный sips.
"""
import json, pathlib, re, subprocess
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAND = ROOT / "textures" / "_candidates"
TEX  = ROOT / "textures"

def main():
    picks = json.loads((ROOT / "data" / "texture_picks.json").read_text(encoding="utf-8"))
    found = json.loads((ROOT / "data" / "eparket_found.json").read_text(encoding="utf-8"))

    for article, info in picks.items():
        src = CAND / info["pick"]
        if not src.exists():
            print(f"  {article:14} НЕТ ФАЙЛА {info['pick']}"); continue
        dst = TEX / f"{re.sub(r'[^A-Za-z0-9._-]', '_', article)}.jpg"
        if src.suffix.lower() == ".avif":
            subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "95",
                            str(src), "--out", str(dst)], capture_output=True, check=True)
        else:
            Image.open(src).convert("RGB").save(dst, "JPEG", quality=95)
        w, h = Image.open(dst).size
        print(f"  {article:14} {w}x{h}  {dst.stat().st_size/1024:5.0f} КБ   "
              f"{found.get(article, {}).get('url', '')[:60]}")

if __name__ == "__main__":
    main()
