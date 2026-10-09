#!/usr/bin/env python3
"""Паспортные характеристики товара с карточки eparket.com — для шторки
«Подробная информация».

Таблица характеристик отдаётся как чередование строк «название / значение»,
между ними встречается одиночный «?» — подсказка-тултип, её выкидываем.
"""
import html, json, pathlib, re, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")
STOP = {"Описание", "Доставка", "Оплата", "Характеристики", "Отзывы", "Похожие товары"}
# Ниже «Упаковки» идёт блок доставки — там чередование пар ломается,
# и парные строки превращаются в мусор вроде «610 мм / Ширина».
END = ("Упаковка", "Документы", "Варианты доставки", "О [[", "[[+tree")

def get(url):
    r = subprocess.run(["curl", "-sS", "-m", "90", "-L", "-A", UA, url], capture_output=True)
    return r.stdout.decode("utf-8", "replace")

def lines_of(page):
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", page, flags=re.S | re.I)
    t = html.unescape(re.sub(r"<[^>]+>", "\n", t))
    return [re.sub(r"\s+", " ", x).strip() for x in t.split("\n")]

def specs(page):
    ls = [l for l in lines_of(page) if l and len(l) < 100 and l != "?"]
    try:
        i = ls.index("Характеристики") + 1
    except ValueError:
        return {}
    out, seen = {}, set()
    while i + 1 < len(ls):
        k, v = ls[i], ls[i + 1]
        if k in STOP or k in seen or any(k.startswith(e) for e in END):
            break
        # Значение не должно само выглядеть как заголовок секции.
        if v in STOP:
            break
        seen.add(k)
        out[k] = v
        i += 2
    return out

def main():
    found = json.loads((ROOT / "data" / "eparket_found.json").read_text(encoding="utf-8"))
    targets = sys.argv[1:] or list(found)
    result = {}
    for art in targets:
        if art not in found:
            print(f"  {art}: нет в eparket_found.json"); continue
        sp = specs(get(found[art]["url"]))
        result[art] = {"url": found[art]["url"], "specs": sp}
        print(f"\n=== {art}  ({len(sp)} характеристик)")
        for k, v in sp.items():
            print(f"   {k:<34}{v}")
        time.sleep(.4)
    # Дополняем, а не перезаписываем: иначе прогон по части артикулов
    # стирает всё, что собрали раньше.
    out = ROOT / "data" / "eparket_specs.json"
    prev = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
    prev.update(result)
    out.write_text(json.dumps(prev, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n-> {out}")

if __name__ == "__main__":
    main()
