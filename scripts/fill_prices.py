#!/usr/bin/env python3
"""Подставляет ориентировочные цены там, где в матрице их нет.

Матрица не трогается: результат пишется в отдельные поля
price_pack_filled / price_m2_filled / price_source, так что всегда видно,
где настоящая цена заказчика, а где наша прикидка.

Логика: берём медианную цену за м² у ближайшей группы товаров
(коллекция -> тот же размер планки -> бренд -> весь каталог)
и умножаем на м² в упаковке. Цена округляется до 10 сом.
"""
import json, pathlib, re, statistics

ROOT = pathlib.Path(__file__).resolve().parent.parent

# В матрице один производитель записан двумя способами.
BRAND_ALIASES = {"alsafloor": "alsaflooring"}

def norm_brand(b):
    key = re.sub(r"[^a-z]", "", (b or "").lower())
    return BRAND_ALIASES.get(key, key)

def norm_collection(c):
    """'Élégant Bâton rompu (Herringbone/Espiga)' и 'Elégant Herringbone' — одна коллекция."""
    c = (c or "").lower()
    c = re.sub(r"\(.*?\)", " ", c)
    return re.sub(r"[^a-zа-я]", "", c)

def median(vals):
    return statistics.median(vals) if vals else None

def groups(products, p):
    """Группы-доноры от самой близкой к самой дальней."""
    nb, nc = norm_brand(p["brand"]), norm_collection(p["collection"])
    yield ("коллекции", [q for q in products
                         if norm_brand(q["brand"]) == nb and norm_collection(q["collection"]) == nc])
    yield ("того же размера планки", [q for q in products
                                      if norm_brand(q["brand"]) == nb and q["size_mm"]
                                      and q["size_mm"] == p["size_mm"]])
    yield ("бренда", [q for q in products if norm_brand(q["brand"]) == nb])
    yield ("всего каталога", products)

def main():
    path = ROOT / "data" / "products.json"
    products = json.loads(path.read_text(encoding="utf-8"))

    filled = []
    for p in products:
        p["price_source"] = None
        if p["price_pack"]:
            p["price_pack_filled"] = p["price_pack"]
            p["price_m2_filled"] = p["price_m2"]
            p["price_source"] = "матрица"
            continue
        # Цена за м² в матрице есть, а за упаковку нет — это не пробел,
        # а арифметика, а не прикидка.
        if p["price_m2"] and p["m2_per_pack"]:
            p["price_m2_filled"] = round(p["price_m2"])
            p["price_pack_filled"] = round(p["price_m2"] * p["m2_per_pack"] / 10) * 10
            p["price_source"] = "расчёт из цены за м² в матрице"
            continue

        for label, grp in groups(products, p):
            grp = [q for q in grp if q is not p]
            m2_prices = [q["price_m2"] for q in grp if q["price_m2"]]
            if not m2_prices:
                continue
            price_m2 = median(m2_prices)
            pack = p["m2_per_pack"] or median([q["m2_per_pack"] for q in grp if q["m2_per_pack"]])
            if not pack:
                continue
            p["price_m2_filled"] = round(price_m2)
            p["price_pack_filled"] = round(price_m2 * pack / 10) * 10
            p["price_source"] = f"по {label} ({len(m2_prices)} поз.)"
            filled.append(p)
            break
        else:
            p["price_pack_filled"] = None
            p["price_m2_filled"] = None
            p["price_source"] = "нет данных"

    path.write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")

    from_matrix = sum(1 for p in products if p["price_source"] == "матрица")
    none_ = [p for p in products if p["price_source"] == "нет данных"]
    print(f"Цена из матрицы: {from_matrix}   подставлено: {len(filled)}   без данных: {len(none_)}\n")
    print(f"{'артикул':<14}{'товар':<42}{'цена/упак':>10}  основание")
    for p in filled:
        print(f"{(p['article'] or p['sku'])[:13]:<14}"
              f"{(p['decor'] or p['collection'])[:40]:<42}"
              f"{p['price_pack_filled']:>10.0f}  {p['price_source']}")
    for p in none_:
        print(f"{(p['article'] or p['sku'])[:13]:<14}{(p['decor'] or p['collection'])[:40]:<42}"
              f"{'—':>10}  нет данных")

if __name__ == "__main__":
    main()
