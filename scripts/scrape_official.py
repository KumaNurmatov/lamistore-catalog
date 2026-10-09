#!/usr/bin/env python3
"""Текстуры и интерьеры с официальных сайтов производителей.

aqua-floor.com — настоящий сайт AQUAFLOOR (не aquafloor.ru, тот недоступен).
  Имена файлов говорят сами за себя: <артикул>.jpg — выкладка,
  <АРТИКУЛ>_int.jpg — интерьер, то есть визуализацию можно не генерировать.

alsaflooring.com — сайт ALSAFLOOR (не alsafloor.com).
  В именах файлов зашит номер декора: 901-chene-berlin-web.png.
  Файлы с -amb- — интерьерные кадры.
"""
import json, pathlib, re, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEX  = ROOT / "textures"
VIS  = ROOT / "textures" / "_official_visuals"; VIS.mkdir(parents=True, exist_ok=True)
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")

def get(url, referer, retries=3):
    for i in range(retries):
        r = subprocess.run(["curl", "-sS", "-m", "90", "-L", "-A", UA, "-e", referer, url],
                           capture_output=True)
        if r.returncode == 0 and len(r.stdout) > 1000:
            return r.stdout
        time.sleep(2 * (i + 1))
    return None

def safe(a):
    return re.sub(r"[^A-Za-z0-9._-]", "_", a)

def aquafloor(articles, log):
    base = "https://aqua-floor.com/catalog/napolnye_pokrytiya/kvarts_vinilovyy_parket"
    for art in articles:
        page_url = f"{base}/{art.lower()}/"
        page = get(page_url, "https://aqua-floor.com/")
        if not page:
            log.append((art, "страница не открылась")); continue
        page = page.decode("utf-8", "replace")
        paths = set(re.findall(r"/upload/iblock/[^\"'\s]+\.(?:jpg|jpeg|png|webp)", page))
        tex = [p for p in paths if p.lower().endswith(f"/{art.lower()}.jpg")]
        vis = [p for p in paths if art.lower() + "_int" in p.lower()]
        if tex:
            d = TEX / f"{safe(art)}.jpg"
            data = get("https://aqua-floor.com" + tex[0], page_url)
            if data: d.write_bytes(data)
        if vis:
            d = VIS / f"{safe(art)}-visual.jpg"
            data = get("https://aqua-floor.com" + vis[0], page_url)
            if data: d.write_bytes(data)
        log.append((art, f"текстура {'да' if tex else 'НЕТ'}, интерьер {'да' if vis else 'нет'}"))
        time.sleep(.3)

def alsafloor(articles, log):
    pool = (ROOT / "data" / "alsaflooring_images.txt").read_text(encoding="utf-8").split()
    # Из набора размеров берём исходник — без суффикса -WxH.
    full = sorted({re.sub(r"-\d+x\d+(\.\w+)$", r"\1", u) for u in pool})
    for art in articles:
        name = f"/{art}-"
        tex = [u for u in full if name in u and "-amb-" not in u and "-perspectiv-" not in u]
        vis = [u for u in full if name in u and ("-amb-" in u or "-perspectiv-" in u)]
        if not tex:
            log.append((art, "файла с этим номером нет")); continue
        data = get(tex[0], "https://www.alsaflooring.com/")
        if data:
            (TEX / f"{safe(art)}{pathlib.Path(tex[0]).suffix}").write_bytes(data)
        if vis:
            d = get(vis[0], "https://www.alsaflooring.com/")
            if d: (VIS / f"{safe(art)}-visual{pathlib.Path(vis[0]).suffix}").write_bytes(d)
        log.append((art, f"текстура да, интерьер {'да' if vis else 'нет'}"))
        time.sleep(.3)

def main():
    log = []
    aqua = ["AF6027PQ", "AF6029PQ", "AF6028PQ", "AF6030PQ",
            "AF7501SOU", "AF7502SOU", "AF7503SOU", "AF7504SOU", "AF7505SOU", "AF7506SOU"]
    alsa = ["508", "525", "560", "901", "902", "903", "904", "906", "907",
            "451", "452", "464", "465", "466"]
    aquafloor(aqua, log)
    alsafloor(alsa, log)
    for art, why in log:
        print(f"  {art:<12}{why}")
    ok = sum(1 for _, w in log if w.startswith("текстура да"))
    print(f"\nтекстур получено: {ok} из {len(log)}")

if __name__ == "__main__":
    main()
