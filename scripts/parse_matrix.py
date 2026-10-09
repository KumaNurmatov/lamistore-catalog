#!/usr/bin/env python3
"""Товарная матрица Lamistore (.xlsx) -> нормализованный products.json."""
import json, re, unicodedata, pathlib, openpyxl

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC  = ROOT / "data" / "matrix.xlsx"
OUT  = ROOT / "data" / "products.json"

COLS = ["brand", "collection", "decor", "article", "wear_class", "size_mm",
        "thickness_mm", "bevel", "planks_per_pack", "m2_per_pack",
        "price_pack", "price_m2", "flag"]

TRANSLIT = {
    'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i',
    'й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t',
    'у':'u','ф':'f','х':'h','ц':'c','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'',
    'э':'e','ю':'yu','я':'ya',
}

def blank(v):
    """В матрице пустое значение пишут и как None, и как дефис."""
    return v is None or str(v).strip() in ("", "-", "—")

def clean(v):
    if blank(v):
        return None
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v).strip()

def num(v):
    if blank(v):
        return None
    try:
        return round(float(v), 4)
    except (TypeError, ValueError):
        return None

def slug(*parts):
    s = " ".join(str(p) for p in parts if p)
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = "".join(TRANSLIT.get(c, c) for c in s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")

def parse_size(v):
    """'1380x156' -> (1380, 156); в матрице встречается и 'x', и '×'."""
    if blank(v):
        return None, None
    m = re.match(r"\s*(\d+)\s*[x×х]\s*(\d+)\s*", str(v))
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)

def main():
    ws = openpyxl.load_workbook(SRC, data_only=True).active
    products, seen = [], {}

    for row_no, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        # Строка считается позицией, только если заполнено что-то из бренд/коллекция/декор/артикул.
        if all(blank(v) for v in row[:4]):
            continue
        r = dict(zip(COLS, row))

        brand      = clean(r["brand"])
        collection = clean(r["collection"])
        decor      = clean(r["decor"])
        article    = clean(r["article"])
        length, width = parse_size(r["size_mm"])

        # Артикул уникален только внутри бренда+коллекции: у ALSA 521 и 903
        # встречаются в двух коллекциях сразу.
        sku = slug(brand, collection, article or decor or f"row{row_no}")
        if sku in seen:
            sku = f"{sku}-{row_no}"
        seen[sku] = row_no

        # Название для карточки: у AQUAFLOOR декоров нет, падаем на артикул.
        title_tail = decor or article or ""
        title = " ".join(x for x in ("Ламинат", brand, title_tail) if x)

        products.append({
            "sku": sku,
            "row": row_no,
            "brand": brand,
            "collection": collection,
            "decor": decor,
            "article": article,
            "title": title,
            "wear_class": clean(r["wear_class"]),
            "size_mm": clean(r["size_mm"]),
            "length_mm": length,
            "width_mm": width,
            "thickness_mm": num(r["thickness_mm"]),
            "bevel": clean(r["bevel"]),
            "planks_per_pack": num(r["planks_per_pack"]),
            "m2_per_pack": num(r["m2_per_pack"]),
            "price_pack": num(r["price_pack"]),
            "price_m2": num(r["price_m2"]),
            "flag": bool(r["flag"]),
            # Заполняется на следующих шагах пайплайна.
            "texture": None,
            "card": None,
            "description": None,
        })

    OUT.write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")

    # Сводка: что готово к загрузке, а что требует ручного добора.
    n = len(products)
    no_price  = [p for p in products if p["price_pack"] is None and p["price_m2"] is None]
    no_decor  = [p for p in products if not p["decor"]]
    no_size   = [p for p in products if not p["size_mm"]]
    no_pack   = [p for p in products if p["m2_per_pack"] is None]
    print(f"Позиций: {n}  ->  {OUT.relative_to(ROOT)}")
    print(f"  без цены:            {len(no_price):3}")
    print(f"  без названия декора: {len(no_decor):3}")
    print(f"  без размера:         {len(no_size):3}")
    print(f"  без м²/упаковка:     {len(no_pack):3}")
    print(f"  flag=True:           {sum(p['flag'] for p in products):3}")
    print("\nПо брендам:")
    for b in dict.fromkeys(p["brand"] for p in products):
        rows = [p for p in products if p["brand"] == b]
        cols = len({p["collection"] for p in rows})
        print(f"  {b:16} {len(rows):3} поз. / {cols} колл.")

if __name__ == "__main__":
    main()
