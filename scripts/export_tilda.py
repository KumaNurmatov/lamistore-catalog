#!/usr/bin/env python3
"""products.json -> CSV для импорта товаров в Магазин Тильды.

Формат колонок снят с реальной выгрузки магазина Lami Store
(store-36109803), а не из документации: порядок, набор полей и стиль
оформления описания повторяют то, что Тильда отдаёт сама.

Фото Тильда тянет по URL, поэтому картинки должны быть уже загружены;
соответствие «файл карточки -> адрес на tildacdn» лежит
в data/tilda_photo_urls.json.
"""
import argparse, csv, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Порядок колонок как в выгрузке Тильды — менять нельзя.
COLS = ["Tilda UID", "Brand", "SKU", "Mark", "Category", "Title", "Description",
        "Text", "Photo", "Price", "Quantity", "Price Old", "Editions",
        "Modifications", "External ID", "Parent UID", "Weight", "Length",
        "Width", "Height"]
# Шторки на карточке товара. Тильда хранит их как info|#|Заголовок|#|Текст,
# по колонке на шторку. Url в выгрузке только для чтения — на импорт не отдаём.
TAB_FORMAT = "{kind}|#|{title}|#|{body}"
MAX_TABS = 2

def num(v, dash=False):
    """Числа в описании — с запятой, как принято в русских карточках."""
    if v is None:
        return None
    s = f"{v:g}"
    return s.replace(".", ",") if dash else s

def description(p):
    bits = []
    if p["collection"]:
        bits.append(f"Коллекция {p['collection']}")
    if p["wear_class"]:
        bits.append(f"{p['wear_class']} класс износостойкости")
    if p["thickness_mm"]:
        bits.append(f"толщина {p['thickness_mm']:g} мм")
    if not bits:
        return ""
    s = ", ".join(bits)
    return s[0].upper() + s[1:]

def text(p, show_price=False):
    """Блок характеристик в том же виде, в каком карточки заполняли вручную:
    строки через <br />, тире — короткое, размеры через ×."""
    size = p["size_mm"].replace("x", "×") if p["size_mm"] else None
    if size and p["thickness_mm"]:
        size = f"{size}×{p['thickness_mm']:g}"
    pack = None
    if p["m2_per_pack"]:
        pack = f"{num(p['m2_per_pack'], dash=True)} м²"
        if p["planks_per_pack"]:
            pack += f" ({num(p['planks_per_pack'])} планок)"

    rows = [("Бренд", p["brand"]),
            ("Коллекция", p["collection"]),
            ("Декор", p["decor"]),
            ("Толщина планки", f"{p['thickness_mm']:g} мм" if p["thickness_mm"] else None),
            ("Размер планки", f"{size} мм" if size else None),
            ("Наличие фаски", p["bevel"]),
            ("Класс", p["wear_class"]),
            ("Кол-во в пачке", pack),
            # Цену за м² печатаем только когда проставляем и саму цену,
            # иначе в карточке с ценой 0 всплывёт цена из описания.
            ("Цена за м²", f"{p.get('price_m2_filled') or 0:.0f} сом"
             if (show_price and p.get("price_m2_filled")) else None)]
    lines = [f"{k} – {v}" for k, v in rows if v]
    head = (p["description"] + "<br /><br />") if p.get("description") else ""
    return head + "<br />".join(lines)

def quote_like_tilda(value):
    """Тильда оборачивает в кавычки всё, где есть пробел или разделитель."""
    s = "" if value is None else str(value)
    if any(c in s for c in ' ;"\n\r'):
        return '"' + s.replace('"', '""') + '"'
    return s

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category-mode", choices=("brand", "flat", "nested"), default="brand",
                    help="brand — раздел на бренд; flat — один общий; "
                         "nested — Ламинат/БРЕНД (проверить, что Тильда так умеет)")
    ap.add_argument("--flat-category", default="Ламинат",
                    help="название общего раздела для режимов flat и nested")
    ap.add_argument("--prices", choices=("filled", "matrix", "zero"), default="filled",
                    help="filled — матрица плюс подставленные; "
                         "matrix — только из матрицы; zero — везде 0")
    ap.add_argument("--keep-uid", action="store_true",
                    help="оставить колонку Tilda UID; по умолчанию она выкидывается — "
                         "при импорте новых товаров Тильда берёт её за уникальный ключ "
                         "и отвергает строки с пустым значением (Empty Uniq column: uid)")
    ap.add_argument("-o", "--out", default=str(ROOT / "data" / "tilda_import.csv"))
    ap.add_argument("articles", nargs="*", help="артикулы; без них — весь каталог")
    args = ap.parse_args()

    products = json.loads((ROOT / "data" / "products.json").read_text(encoding="utf-8"))
    photos = {}
    f = ROOT / "data" / "tilda_photo_urls.json"
    if f.exists():
        photos = json.loads(f.read_text(encoding="utf-8"))
    # Вторая фотография — интерьер, показывается на ховере в каталоге.
    visuals = {}
    f = ROOT / "data" / "tilda_visual_urls.json"
    if f.exists():
        visuals = json.loads(f.read_text(encoding="utf-8"))
    brand_tabs = {}
    f = ROOT / "data" / "brand_tabs.json"
    if f.exists():
        brand_tabs = {k: v for k, v in json.loads(f.read_text(encoding="utf-8")).items()
                      if not k.startswith("_")}
    # «Подробная информация» — своя у каждого товара: характеристики декоров различаются.
    product_tabs = {}
    f = ROOT / "data" / "product_tabs.json"
    if f.exists():
        product_tabs = json.loads(f.read_text(encoding="utf-8"))

    if args.articles:
        order = {a: i for i, a in enumerate(args.articles)}
        products = sorted((p for p in products if p["article"] in order),
                          key=lambda p: order[p["article"]])

    def category(p):
        if args.category_mode == "flat":
            return args.flat_category
        if args.category_mode == "nested":
            return f"{args.flat_category}/{p['brand']}"
        return p["brand"]

    def price(p):
        if args.prices == "zero":
            return 0
        if args.prices == "matrix":
            return p["price_pack"] or 0
        return p.get("price_pack_filled") or p["price_pack"] or 0

    rows, no_photo, no_visual, derived = [], [], [], []
    for p in products:
        key = p["card"] and pathlib.Path(p["card"]).with_suffix(".jpg").name
        photo = photos.get(key, "")
        if not photo:
            no_photo.append(p["article"] or p["sku"])
        # Несколько фото Тильда разделяет пробелом; порядок задаёт, какая на ховере.
        visual = visuals.get(p["article"] or "", "")
        if not visual:
            no_visual.append(p["article"] or p["sku"])
        photo_field = " ".join(u for u in (photo, visual) if u)

        tabs = []
        own = product_tabs.get(p["article"] or "")
        if own:
            tabs.append(own)
        tabs += brand_tabs.get(p["brand"]) or []
        if args.prices == "filled" and not p["price_pack"] and p.get("price_pack_filled"):
            derived.append((p["article"] or p["sku"], p["price_pack_filled"], p["price_source"]))
        rows.append({
            # Пустой Tilda UID — товар создаётся новым, а не обновляет существующий.
            "Tilda UID": "", "Brand": p["brand"], "SKU": p["article"] or p["sku"],
            "Mark": "", "Category": category(p), "Title": p["title"],
            "Description": description(p), "Text": text(p, args.prices != "zero"),
            "Photo": photo_field,
            "Price": f"{price(p):.0f}",
            "Quantity": "", "Price Old": "", "Editions": "", "Modifications": "",
            "External ID": p["sku"], "Parent UID": "",
            "Weight": "0", "Length": "0", "Width": "0", "Height": "0",
            **{f"Tabs:{i}": (TAB_FORMAT.format(**tabs[i - 1]) if i <= len(tabs) else "")
               for i in range(1, MAX_TABS + 1)},
        })

    cols = COLS if args.keep_uid else [c for c in COLS if c != "Tilda UID"]
    cols += [f"Tabs:{i}" for i in range(1, MAX_TABS + 1)]

    out = pathlib.Path(args.out)
    # Без BOM и с ручным квотированием — ровно как в выгрузке Тильды.
    with out.open("w", encoding="utf-8", newline="") as fh:
        fh.write(";".join(quote_like_tilda(c) for c in cols) + "\n")
        for r in rows:
            fh.write(";".join(quote_like_tilda(r[c]) for c in cols) + "\n")

    print(f"Строк: {len(rows)}  ->  {out}")
    print(f"  колонок:  {len(cols)}"
          f"{'' if args.keep_uid else '  (Tilda UID выкинут — ключом будет External ID)'}")
    print(f"  разделы:  {args.category_mode}  ->  "
          f"{', '.join(sorted({r['Category'] for r in rows}))}")
    print(f"  цены:     {args.prices}")
    if derived:
        print(f"  ЦЕНА ПОДСТАВЛЕНА (не из матрицы), {len(derived)} поз.:")
        for art, val, src in derived:
            print(f"      {art:<14}{val:>8.0f}  {src}")
    n1 = sum(1 for r in rows if r.get("Tabs:1"))
    n2 = sum(1 for r in rows if r.get("Tabs:2"))
    print(f"  шторки:   подробная информация у {n1}, сертификаты у {n2} из {len(rows)}")
    if no_photo:
        print(f"  БЕЗ ФОТО:        {', '.join(no_photo)}")
    if no_visual:
        print(f"  БЕЗ ВИЗУАЛИЗАЦИИ: {', '.join(no_visual)}")

if __name__ == "__main__":
    main()
