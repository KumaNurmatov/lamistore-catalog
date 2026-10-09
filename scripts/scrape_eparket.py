#!/usr/bin/env python3
"""Текстуры декоров с eparket.com по артикулам из матрицы.

Магазин держит PERGO, AQUAFLOOR и ALSAFLOOR — три бренда, которых нет
на доступных официальных сайтах. Товар ищется по карте сайта, потому что
поиск на самом сайте отдаётся через JS.

Порядок картинок на карточке плавает (интерьер / ракурс / выкладка),
поэтому скрипт скачивает все и складывает в textures/_candidates —
нужную выбираем глазами и фиксируем в data/texture_picks.json.
"""
import json, pathlib, re, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAND = ROOT / "textures" / "_candidates"; CAND.mkdir(parents=True, exist_ok=True)
SITEMAP_CACHE = ROOT / "data" / "eparket_urls.txt"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")

def get(url, referer="https://eparket.com/", retries=3, timeout="120"):
    for i in range(retries):
        r = subprocess.run(["curl", "-sS", "-m", timeout, "-L", "-A", UA, "-e", referer, url],
                           capture_output=True)
        if r.returncode == 0 and r.stdout:
            return r.stdout
        if i == retries - 1:
            raise RuntimeError(f"не скачалось: {url}")
        time.sleep(2 * (i + 1))

def sitemap_urls():
    """Карта сайта большая (~485k ссылок), поэтому кэшируем её на диск."""
    if SITEMAP_CACHE.exists():
        return SITEMAP_CACHE.read_text(encoding="utf-8").splitlines()
    index = get("https://eparket.com/sitemap.xml").decode("utf-8", "replace")
    urls = []
    for feed in re.findall(r"<loc>(https://eparket\.com/feed/SiteMap\d*\.xml)</loc>", index):
        urls += re.findall(r"<loc>([^<]+)</loc>",
                           get(feed, timeout="180").decode("utf-8", "replace"))
    SITEMAP_CACHE.write_text("\n".join(urls), encoding="utf-8")
    return urls

# Картинки лежат как /images/product/<bucket>/<id>/<id>-<n>_<size>.<ext>;
# _2000 — самый крупный доступный вариант.
IMG = re.compile(r"https://eparket\.com/images/product/\d+/\d+/\d+-(\d+)_full\.webp")

def find_url(urls, article, hint=None):
    """Артикул ищем как отдельный сегмент slug, иначе короткий номер вроде '511'
    поймает посторонний товар. hint — подстрока, обязанная быть в адресе
    (обычно бренд): задаётся как АРТИКУЛ@подсказка."""
    pat = re.compile(rf"(?:^|[-/]){re.escape(article.lower())}(?:[-/]|$)")
    hits = [u for u in urls
            if "/product/" in u and pat.search(u.lower())
            and (hint is None or hint.lower() in u.lower())]
    return hits[0] if hits else None

def main():
    articles = sys.argv[1:]
    if not articles:
        print("укажите артикулы: scrape_eparket.py L1258-04431 AF4516PQL ...")
        return
    urls = sitemap_urls()
    print(f"ссылок в карте сайта: {len(urls)}\n")

    found = {}
    for spec in articles:
        art, _, hint = spec.partition("@")
        page_url = find_url(urls, art, hint or None)
        if not page_url:
            print(f"  {art:14} НЕ НАЙДЕН")
            continue
        page = get(page_url).decode("utf-8", "replace")
        title = re.search(r"<title>([^<]*)</title>", page)
        title = title.group(1).strip() if title else ""
        shots = sorted(set(IMG.findall(page)), key=int)

        saved = []
        for n in shots:
            base = re.search(r"(https://eparket\.com/images/product/\d+/\d+/\d+)-\d+_full\.webp", page).group(1)
            for variant in ("_2000.avif", "_full.webp"):
                data = get(f"{base}-{n}{variant}", referer=page_url)
                if len(data) > 5000:
                    dst = CAND / f"{art}-{n}{pathlib.Path(variant).suffix}"
                    dst.write_bytes(data); saved.append(dst.name); break
            time.sleep(.3)
        found[art] = {"url": page_url, "title": title, "candidates": saved}
        print(f"  {art:14} {len(saved)} карт.  {title[:70]}")

    out = ROOT / "data" / "eparket_found.json"
    prev = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
    prev.update(found)
    out.write_text(json.dumps(prev, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n-> {out}")

if __name__ == "__main__":
    main()
