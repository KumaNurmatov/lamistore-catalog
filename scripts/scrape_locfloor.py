#!/usr/bin/env python3
"""Текстуры декоров LOC FLOOR Tempo с locfloor.ru, разложенные по артикулам LFT6xx."""
import json, pathlib, re, subprocess, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEX  = ROOT / "textures"; TEX.mkdir(exist_ok=True)
BASE = "https://locfloor.ru"
SECTION = f"{BASE}/product/laminat-locfloor/tempo/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")

# Галерея отдаётся через resize_cache; оригинал лежит на том же пути без сегмента кэша.
RESIZE = re.compile(
    r'/upload/resize_cache/(iblock/[0-9a-f]{3}/)\d+_\d+_[0-9a-f]+/([0-9a-z]+\.(?:jpg|jpeg|png|webp))',
    re.I)

def get(url, referer=BASE, retries=3):
    """Через curl: у системного python нет набора корневых сертификатов."""
    for i in range(retries):
        r = subprocess.run(["curl", "-sS", "-m", "120", "-L", "-A", UA, "-e", referer, url],
                           capture_output=True)
        if r.returncode == 0 and r.stdout:
            return r.stdout
        if i == retries - 1:
            raise RuntimeError(f"не скачалось: {url} ({r.stderr.decode()[:200]})")
        time.sleep(2 * (i + 1))

def size_of(url, referer):
    """Размер без скачивания — чтобы из галереи выбрать оригинал, а не превью."""
    r = subprocess.run(["curl", "-sSI", "-m", "60", "-L", "-A", UA, "-e", referer, url],
                       capture_output=True, text=True)
    m = re.findall(r"(?im)^content-length:\s*(\d+)", r.stdout)
    return int(m[-1]) if m else 0

def main():
    html = get(SECTION).decode("utf-8", "replace")
    pages = sorted(set(re.findall(r'href="(/product/laminat-locfloor/tempo/[a-z0-9-]+/)"', html)))
    print(f"Страниц декоров: {len(pages)}\n")

    out, skipped = [], []
    for path in pages:
        url = BASE + path
        page = get(url, referer=SECTION).decode("utf-8", "replace")

        art = re.search(r"\bLFT(\d{3})\b", page)
        article = f"LFT{art.group(1)}" if art else None
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S)
        name = re.sub(r"<[^>]+>", "", h1.group(1)).strip() if h1 else path.strip("/").split("/")[-1]

        imgs = list(dict.fromkeys(RESIZE.findall(page)))
        if not article or not imgs:
            skipped.append((path, article, len(imgs)))
            continue

        # В галерее лежит одна и та же выкладка в разных разрешениях — берём самое крупное.
        cands = [f"{BASE}/upload/{folder}{fname}" for folder, fname in imgs]
        best = max(cands, key=lambda u: size_of(u, url))

        dest = TEX / f"{article}{pathlib.Path(best).suffix.lower()}"
        if not dest.exists():
            dest.write_bytes(get(best, referer=url))
            time.sleep(1)
        mb = dest.stat().st_size / 1024 / 1024
        print(f"  {article:8} {name:28} {mb:6.1f} MB  ({len(cands)} вар.)")
        out.append({"article": article, "name": name, "page": url,
                    "source": best, "file": dest.name, "bytes": dest.stat().st_size})

    (ROOT / "data" / "textures_locfloor.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nСкачано текстур: {len(out)}")
    for path, article, n in skipped:
        print(f"  ПРОПУСК {path}: артикул={article}, картинок={n}")

if __name__ == "__main__":
    main()
