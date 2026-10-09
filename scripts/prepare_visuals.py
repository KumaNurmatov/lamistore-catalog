#!/usr/bin/env python3
"""Готовит вторые фотографии товара — интерьеры, которые показываются на ховере.

Берём из textures/_candidates те кадры, что не пошли на карточку: это и есть
интерьерные снимки с сайтов магазинов. Выбор фиксируется в data/visual_picks.json,
потому что автоматически интерьер от выкладки планок не отличить.
"""
import json, pathlib, subprocess
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAND = ROOT / "textures" / "_candidates"
OUT  = ROOT / "handoff" / "visuals"
WIDTH, QUALITY = 1200, 86

def load(p):
    """AVIF Pillow не читает — конвертируем через sips."""
    if p.suffix.lower() == ".avif":
        tmp = p.with_suffix(".png")
        if not tmp.exists():
            subprocess.run(["sips", "-s", "format", "png", str(p), "--out", str(tmp)],
                           capture_output=True, check=True)
        p = tmp
    return Image.open(p).convert("RGB")

def main():
    picks = json.loads((ROOT / "data" / "visual_picks.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)

    done = []
    for article, info in picks.items():
        if not info.get("pick"):
            print(f"  {article:<14} интерьера нет — {info.get('note', '')}")
            continue
        src = CAND / info["pick"]
        if not src.exists():
            print(f"  {article:<14} НЕТ ФАЙЛА {info['pick']}")
            continue
        im = load(src)
        if im.width > WIDTH:
            im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS)
        dst = OUT / f"{article}-visual.jpg"
        im.save(dst, "JPEG", quality=QUALITY, optimize=True, progressive=True)
        print(f"  {article:<14} {im.width}x{im.height}  {dst.stat().st_size/1024:5.0f} КБ  <- {info['pick']}")
        done.append(article)

    print(f"\nВизуализаций: {len(done)} из {len(picks)}")

if __name__ == "__main__":
    main()
