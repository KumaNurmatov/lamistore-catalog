#!/usr/bin/env python3
"""Автоматически выбирает из кадров товара выкладку планок.

Правило выведено и проверено на 20 кадрах, разобранных вручную: у выкладки
нет ни светлых пятен (стены, окна), ни тёмных провалов, ни оттенков вне
тёплого «деревянного» сектора. У всех интерьеров хотя бы одна метрика ненулевая.

Товары, где лучший кандидат не идеально чистый или таких несколько,
попадают в «спорные» и размечаются глазами.
"""
import colorsys, json, pathlib, subprocess, sys
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAND = ROOT / "textures" / "_candidates"
CLEAN = 0.004          # порог «чистоты»: заметно выше нуля, но ниже худшего из выкладок

def load(p):
    if p.suffix.lower() in (".avif", ".webp"):
        tmp = p.with_suffix(".conv.png")
        if not tmp.exists():
            subprocess.run(["sips", "-s", "format", "png", str(p), "--out", str(tmp)],
                           capture_output=True, check=True)
        p = tmp
    return Image.open(p).convert("RGB")

def score(p):
    im = load(p).resize((64, 64), Image.LANCZOS)
    px = list(im.getdata())
    light = dark = nonwood = 0
    for r, g, b in px:
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        if l > 0.80: light += 1
        if l < 0.12: dark += 1
        if s > 0.12 and not (0.02 <= h <= 0.14): nonwood += 1
    n = len(px)
    return (light + dark + nonwood) / n

def main():
    found = json.loads((ROOT / "data" / "eparket_found.json").read_text(encoding="utf-8"))
    picks_path = ROOT / "data" / "texture_picks.json"
    picks = json.loads(picks_path.read_text(encoding="utf-8"))

    auto, doubtful = 0, []
    for art, info in found.items():
        if art in picks:
            continue
        cands = [CAND / c for c in info.get("candidates", []) if (CAND / c).exists()]
        if not cands:
            doubtful.append((art, "нет кадров")); continue
        ranked = sorted(((score(p), p.name) for p in cands))
        best, second = ranked[0], (ranked[1] if len(ranked) > 1 else (9, None))
        if best[0] > CLEAN:
            doubtful.append((art, f"лучший кадр не чистый ({best[0]:.3f})")); continue
        if second[0] <= CLEAN:
            doubtful.append((art, f"чистых кадров несколько: {best[1]}, {second[1]}")); continue
        picks[art] = {"pick": best[1], "note": f"выбрано автоматически, чистота {best[0]:.4f}"}
        auto += 1

    picks_path.write_text(json.dumps(picks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Выбрано автоматически: {auto}")
    print(f"Требуют глаз: {len(doubtful)}")
    for art, why in doubtful:
        print(f"   {art:<14}{why}")

if __name__ == "__main__":
    main()
