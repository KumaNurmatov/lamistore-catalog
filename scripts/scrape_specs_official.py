#!/usr/bin/env python3
"""Характеристики с официальных сайтов — там, где eparket товар не держит.

aqua-floor.com и locfloor.ru отдают таблицу как чередование строк
«название / значение», как и eparket, но с разными якорями и мусором вокруг.
"""
import html, json, pathlib, re, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")

def get(url, referer):
    r = subprocess.run(["curl", "-sS", "-m", "90", "-L", "-A", UA, "-e", referer, url],
                       capture_output=True)
    return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else ""

# Разметка у обоих сайтов структурная, поэтому пары берём из неё,
# а не из «плоского» текста: строки с пустым значением ломают чередование.
DL = re.compile(r"<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>", re.S | re.I)
PROP = re.compile(
    r'js-prop-title"[^>]*>(.*?)</div>.*?js-prop-value"[^>]*>(.*?)</div>', re.S | re.I)

def clean(x):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", x))).strip()

# Поля калькулятора стоимости: значения приходят неподставленными шаблонами.
JUNK_KEYS = {"В упаковке:", "Вес:", "Упаковок:", "Площадь помещения"}

def from_markup(page, pattern):
    out = {}
    for k, v in pattern.findall(page):
        k, v = clean(k), clean(v)
        if not k or not v or k in out or k in JUNK_KEYS:
            continue
        if "{{" in v or len(k) > 80 or len(v) > 160:
            continue
        out[k] = v
    return out

def lines(page):
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", page, flags=re.S | re.I)
    t = html.unescape(re.sub(r"<[^>]+>", "\n", t))
    return [l for l in (re.sub(r"\s+", " ", x).strip() for x in t.split("\n"))
            if l and len(l) < 110]

def pairs(ls, anchor, stop, limit=60):
    try:
        i = ls.index(anchor) + 1
    except ValueError:
        return {}
    # Сразу за якорем могут идти подписи вкладок — пропускаем их, а не обрываемся.
    while i < len(ls) and ls[i] in stop:
        i += 1
    out = {}
    while i + 1 < len(ls) and len(out) < limit:
        k, v = ls[i], ls[i + 1]
        if k in stop or v in stop:
            break
        if k != v and not k.endswith(("₽", "руб.")):
            out[k] = v
        i += 2
    return out

STOP = {"Характеристики", "Описание", "Доставка", "Оплата", "Отзывы",
        "Похожие товары", "Сопутствующие товары", "Корзина", "Аксессуары",
        "Упаковочные детали", "Документы", "Где купить"}

def aquafloor(article):
    url = ("https://aqua-floor.com/catalog/napolnye_pokrytiya/"
           f"kvarts_vinilovyy_parket/{article.lower().rstrip('+')}/")
    return url, from_markup(get(url, "https://aqua-floor.com/"), DL)

def locfloor(page_url):
    return page_url, from_markup(get(page_url, "https://locfloor.ru/"), PROP)

def main():
    out_path = ROOT / "data" / "official_specs.json"
    res = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {}

    aqua = ["AF6027PQ+", "AF6029PQ+", "AF6028PQ+", "AF6030PQ+", "AF7501SOU",
            "AF7502SOU", "AF7503SOU", "AF7504SOU", "AF7505SOU", "AF7506SOU"]
    for a in aqua:
        url, sp = aquafloor(a)
        res[a] = {"url": url, "specs": sp}
        print(f"  {a:<12}{len(sp):>3} характеристик")
        time.sleep(.4)

    loc = json.loads((ROOT / "data" / "textures_locfloor.json").read_text(encoding="utf-8"))
    for rec in loc:
        a = rec["article"]
        if a in res:
            continue
        url, sp = locfloor(rec["page"])
        res[a] = {"url": url, "specs": sp}
        print(f"  {a:<12}{len(sp):>3} характеристик")
        time.sleep(.4)

    out_path.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n-> {out_path}")

if __name__ == "__main__":
    main()
