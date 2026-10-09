#!/usr/bin/env python3
"""Готовит папку docs/ для GitHub Pages: картинки каталога под публичными адресами.

Тильда тянет фото по URL, поэтому карточки и визуализации должны лежать
в открытом доступе. Имена файлов — sku-слаг позиции: только ASCII, без плюсов
и пробелов, так что адрес не требует экранирования и однозначно сопоставим
с товаром.
"""
import json, pathlib, re, shutil
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
CARD_W, CARD_Q = 900, 86
VIS_W,  VIS_Q  = 900, 84

def safe(a):
    return re.sub(r"[^A-Za-z0-9._-]", "_", a or "")

def save(src, dst, width, quality):
    im = Image.open(src).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(dst, "JPEG", quality=quality, optimize=True, progressive=True)
    return dst.stat().st_size

def main():
    products = json.loads((ROOT / "data" / "products.json").read_text(encoding="utf-8"))
    for sub in ("cards", "visuals"):
        d = DOCS / sub
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)

    vis_dirs = [ROOT / "handoff" / "visuals", ROOT / "textures" / "_official_visuals"]
    total_c = total_v = 0
    index = {}
    for p in products:
        if not p["card"]:
            continue
        sku = p["sku"]
        total_c += save(ROOT / "cards" / p["card"], DOCS / "cards" / f"{sku}.jpg", CARD_W, CARD_Q)
        rec = {"card": f"cards/{sku}.jpg"}
        for d in vis_dirs:
            for ext in (".jpg", ".jpeg", ".png", ".webp"):
                for name in (p["article"], safe(p["article"])):
                    f = d / f"{name}-visual{ext}"
                    if f.exists():
                        total_v += save(f, DOCS / "visuals" / f"{sku}.jpg", VIS_W, VIS_Q)
                        rec["visual"] = f"visuals/{sku}.jpg"
                        break
                if "visual" in rec: break
            if "visual" in rec: break
        index[p["article"]] = rec

    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    (ROOT / "data" / "publish_index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    cards = len(list((DOCS / "cards").glob("*.jpg")))
    vis = len(list((DOCS / "visuals").glob("*.jpg")))
    print(f"карточек:      {cards:>4}   {total_c/1e6:6.1f} МБ")
    print(f"визуализаций:  {vis:>4}   {total_v/1e6:6.1f} МБ")
    print(f"всего:              {(total_c+total_v)/1e6:6.1f} МБ  -> {DOCS}")

if __name__ == "__main__":
    main()
