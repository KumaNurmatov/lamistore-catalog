#!/usr/bin/env python3
"""Готовит задания на генерацию интерьеров — по одному на декор.

Цвет в промпте не выдумывается: он считается из самой текстуры, поэтому
комната получается в тон товару. Укладка берётся из названия коллекции.
"""
import colorsys, json, pathlib, re, sys
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIAGONAL = re.compile(r"herringbone|chevron|parquet|ёлоч|елоч", re.I)

def tone(path):
    """Светлота и теплота текстуры -> словесное описание для промпта."""
    im = Image.open(path).convert("RGB").resize((48, 48), Image.LANCZOS)
    px = list(im.getdata())
    r = sum(p[0] for p in px) / len(px)
    g = sum(p[1] for p in px) / len(px)
    b = sum(p[2] for p in px) / len(px)
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    light = "very pale" if l > 0.72 else "light" if l > 0.58 else \
            "mid-tone" if l > 0.40 else "deep dark"
    warm = "cool grey" if s < 0.10 else "greyish" if s < 0.18 else \
           "warm" if h < 0.09 else "golden"
    return f"{light} {warm}"

def main():
    todo = json.loads((ROOT / "data" / "visuals_todo.json").read_text(encoding="utf-8"))
    ids = json.loads((ROOT / "data" / "media_ids.json").read_text(encoding="utf-8"))
    size = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    which = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    reqs = []
    for i, t in enumerate(todo):
        tex = pathlib.Path(t["texture"])
        mid = ids.get(tex.name)
        if not mid:
            print(f"нет media_id для {tex.name}", file=sys.stderr); continue
        diag = bool(DIAGONAL.search(t["collection"] or ""))
        lay = ("laid in a classic herringbone pattern, the herringbone clearly visible"
               if diag else "laid with long straight wide planks")
        reqs.append({"index": i, "params": {
            "model": "gpt_image_2_5", "aspect_ratio": "4:5",
            "quality": "high", "resolution": "2k",
            "medias": [{"role": "image_references", "value": mid}],
            "prompt": (
                "Photorealistic interior photograph of a calm modern living room. "
                f"The floor is {lay}, in exactly the {tone(tex)} oak decor shown in the "
                "reference image — match its colour, grain and plank proportions precisely. "
                "Floor fills the lower two thirds of the frame, seen at a low wide angle. "
                "Soft natural daylight from a tall window, light linen sofa, low wooden "
                "coffee table, a soft beige rug, one large plant, muted Scandinavian styling. "
                "Sharp realistic wood grain. No people, no text, no logos, no watermark.")}})

    batches = [reqs[i:i + size] for i in range(0, len(reqs), size)]
    print(f"всего заданий: {len(reqs)}, пачек: {len(batches)}", file=sys.stderr)
    print(json.dumps(batches[which - 1], ensure_ascii=False))

if __name__ == "__main__":
    main()
