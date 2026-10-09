#!/usr/bin/env python3
"""Интерьерные кадры AQUAFLOOR с сайта производителя.

На aqua-floor.com имя файла говорит, что внутри: <АРТИКУЛ>_int.jpg — интерьер.
Это избавляет от генерации: берём подлинные снимки производителя.
"""
import json, pathlib, re, subprocess, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "textures" / "_official_visuals"; OUT.mkdir(parents=True, exist_ok=True)
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")

def get(url, referer):
    r = subprocess.run(["curl", "-sS", "-m", "90", "-L", "-A", UA, "-e", referer, url],
                       capture_output=True)
    return r.stdout if r.returncode == 0 else b""

def safe(a):
    return re.sub(r"[^A-Za-z0-9._-]", "_", a)

def main():
    pages = json.loads((ROOT / "data" / "aquafloor_pages.json").read_text(encoding="utf-8"))
    have = skipped = 0
    for art, page_url in pages.items():
        dst = OUT / f"{safe(art)}-visual.jpg"
        if dst.exists():
            have += 1; continue
        page = get(page_url, "https://aqua-floor.com/").decode("utf-8", "replace")
        base = art.lower().rstrip("+")
        paths = set(re.findall(r"/upload/iblock/[^\"'\s]+\.(?:jpg|jpeg|png|webp)", page))
        # Берём оригинал, а не вариант из resize_cache.
        vis = [p for p in paths if f"{base}_int" in p.lower() and "resize_cache" not in p]
        if not vis:
            skipped += 1
            print(f"  {art:<12} интерьера нет", flush=True); continue
        data = get("https://aqua-floor.com" + vis[0], page_url)
        if len(data) > 5000:
            dst.write_bytes(data); have += 1
            print(f"  {art:<12} {len(data)/1024:6.0f} КБ", flush=True)
        else:
            skipped += 1
            print(f"  {art:<12} не скачался", flush=True)
        time.sleep(.3)
    print(f"\nинтерьеров: {have}, без интерьера: {skipped}")

if __name__ == "__main__":
    main()
