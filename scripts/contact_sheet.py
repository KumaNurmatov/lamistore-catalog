#!/usr/bin/env python3
"""Контактный лист кандидатов — чтобы глазами выбрать выкладку планок."""
import pathlib, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAND = ROOT / "textures" / "_candidates"

def load(p):
    """AVIF Pillow не читает — конвертируем через sips."""
    if p.suffix.lower() == ".avif":
        tmp = p.with_suffix(".png")
        if not tmp.exists():
            subprocess.run(["sips", "-s", "format", "png", str(p), "--out", str(tmp)],
                           capture_output=True)
        p = tmp
    return Image.open(p).convert("RGB")

def font(sz):
    try:
        return ImageFont.truetype("/System/Library/Fonts/Supplemental/Helvetica.ttc", sz)
    except Exception:
        return ImageFont.load_default(sz)

def main():
    files = sorted(f for f in CAND.iterdir() if f.suffix.lower() in (".avif", ".webp", ".jpg", ".png")
                   and not f.name.endswith(".png"))
    if not files:
        print("нет кандидатов"); return
    CW, CH, GAP, PAD, CAP = 260, 260, 20, 40, 28
    cols = 6
    rows = (len(files) + cols - 1) // cols
    W = PAD*2 + cols*CW + (cols-1)*GAP
    H = PAD*2 + rows*(CH+CAP) + (rows-1)*GAP + 40
    sheet = Image.new("RGB", (W, H), "#EDEDED")
    d = ImageDraw.Draw(sheet)
    d.text((PAD, PAD-18), "Кандидаты текстур — выбрать выкладку планок", font=font(22), fill="#1A1A1A")

    for i, f in enumerate(files):
        r, c = divmod(i, cols)
        x = PAD + c*(CW+GAP); y = PAD + 40 + r*(CH+CAP+GAP)
        try:
            im = load(f)
            im.thumbnail((CW, CH), Image.LANCZOS)
            sheet.paste(im, (x + (CW-im.width)//2, y + (CH-im.height)//2))
        except Exception as e:
            d.text((x+8, y+CH//2), f"ошибка: {e}", font=font(11), fill="#B00")
        d.text((x, y+CH+6), f.stem, font=font(14), fill="#1A1A1A")

    out = CAND / "_sheet.png"
    sheet.save(out)
    print(f"{len(files)} кандидатов -> {out}")

if __name__ == "__main__":
    main()
