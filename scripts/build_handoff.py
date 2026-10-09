#!/usr/bin/env python3
"""Страница для ручного заведения товаров в Тильде.

По одной позиции на блок: готовая карточка и все поля с кнопкой «копировать»,
чтобы не перенабирать характеристики руками.
"""
import json, pathlib, shutil, sys
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT  = ROOT / "handoff"
IMGS = OUT / "cards"

def money(v):
    return f"{v:,.0f}".replace(",", " ") if v else None

def fields(p):
    """Пары «поле Тильды -> значение». Пустые не показываем, чтобы не мешали."""
    f = [("Название", p["title"]),
         ("Артикул", p["article"] or ""),
         ("Цена (сом/упак)", f"{p['price_pack']:.0f}" if p["price_pack"] else ""),
         ("Категория", f"Ламинат / {p['brand']}")]
    specs = [("Бренд", p["brand"]), ("Коллекция", p["collection"]), ("Декор", p["decor"]),
             ("Класс износостойкости", p["wear_class"]),
             ("Размер планки", f"{p['size_mm']} мм" if p["size_mm"] else None),
             ("Толщина", f"{p['thickness_mm']:g} мм" if p["thickness_mm"] else None),
             ("Фаска", p["bevel"]),
             ("Планок в упаковке", f"{p['planks_per_pack']:g}" if p["planks_per_pack"] else None),
             ("м² в упаковке", f"{p['m2_per_pack']:g}" if p["m2_per_pack"] else None),
             ("Цена за м²", f"{p['price_m2']:.0f} сом" if p["price_m2"] else None)]
    specs = [(k, v) for k, v in specs if v]
    f.append(("Описание", "\n".join(f"{k} — {v}" for k, v in specs)))
    return [(k, v) for k, v in f if v], specs

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#F2F2F2;--card:#FFF;--ink:#1A1A1A;--muted:#8A8A8A;--line:#E3E3E3;--accent:#9F9067}
:root:not([data-theme="light"]){@media (prefers-color-scheme:dark){
  --bg:#141414;--card:#1E1E1E;--ink:#F2F2F2;--muted:#8A8A8A;--line:#2E2E2E}}
:root[data-theme="dark"]{--bg:#141414;--card:#1E1E1E;--ink:#F2F2F2;--muted:#8A8A8A;--line:#2E2E2E}
body{background:var(--bg);color:var(--ink);min-height:100vh;
  font-family:'Inter','Helvetica Neue',Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased}
.wrap{max-width:1100px;margin:0 auto;padding:48px 16px 96px}
h1{font-size:28px;letter-spacing:-.02em}
.lead{color:var(--muted);font-size:15px;margin-top:10px;line-height:1.6}
.row{display:flex;gap:28px;background:var(--card);border:1px solid var(--line);
  border-radius:16px;padding:24px;margin-top:24px}
.row img{width:210px;height:263px;object-fit:cover;border-radius:10px;flex:none;border:1px solid var(--line)}
.meta{flex:1;min-width:0}
.n{color:var(--muted);font-size:12px;letter-spacing:.08em;text-transform:uppercase}
h2{font-size:19px;margin:6px 0 16px}
table{width:100%;border-collapse:collapse}
td{padding:7px 0;vertical-align:top;border-bottom:1px solid var(--line);font-size:14px}
td:first-child{color:var(--muted);width:180px;padding-right:16px}
td pre{font:inherit;white-space:pre-wrap}
button{border:1px solid var(--line);background:transparent;color:var(--muted);border-radius:6px;
  padding:3px 10px;font-size:12px;cursor:pointer;margin-left:8px}
button:hover{border-color:var(--accent);color:var(--ink)}
.src{margin-top:14px;font-size:12px;color:var(--muted);word-break:break-all}
.src a{color:var(--muted)}
.warn{background:rgba(159,144,103,.12);border:1px solid var(--accent);border-radius:10px;
  padding:14px 18px;margin-top:24px;font-size:14px;line-height:1.6}
@media(max-width:720px){.row{flex-direction:column}.row img{width:100%;height:auto;aspect-ratio:4/5}
  td:first-child{width:130px}}
"""

JS = """
document.addEventListener('click', async e => {
  const b = e.target.closest('button[data-copy]'); if(!b) return;
  try { await navigator.clipboard.writeText(b.dataset.copy);
        const t=b.textContent; b.textContent='скопировано'; setTimeout(()=>b.textContent=t,1200); }
  catch { b.textContent='не вышло'; }
});
"""

def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))

def main():
    products = json.loads((ROOT / "data" / "products.json").read_text(encoding="utf-8"))
    # Откуда взято фото — показываем в карточке, чтобы источник был проверяем.
    sources = {}
    f = ROOT / "data" / "eparket_found.json"
    if f.exists():
        for art, info in json.loads(f.read_text(encoding="utf-8")).items():
            sources[art] = info["url"]
    f = ROOT / "data" / "textures_locfloor.json"
    if f.exists():
        for rec in json.loads(f.read_text(encoding="utf-8")):
            sources[rec["article"]] = rec["page"]

    items = [p for p in products if p["card"]]
    only = sys.argv[1:]
    if only:
        order = {a: i for i, a in enumerate(only)}
        items = sorted((p for p in items if p["article"] in order),
                       key=lambda p: order[p["article"]])
    if not items:
        print("нет отрисованных карточек"); return

    if IMGS.exists():
        shutil.rmtree(IMGS)
    IMGS.mkdir(parents=True)

    blocks = []
    for i, p in enumerate(items, 1):
        im = Image.open(ROOT / "cards" / p["card"]).convert("RGB")
        im.thumbnail((900, 1200), Image.LANCZOS)
        name = pathlib.Path(p["card"]).stem + ".jpg"
        im.save(IMGS / name, "JPEG", quality=88, optimize=True)

        flds, _ = fields(p)
        rows = "".join(
            f"<tr><td>{esc(k)}</td><td><pre>{esc(v)}</pre>"
            f'<button data-copy="{esc(v)}">копировать</button></td></tr>'
            for k, v in flds)
        src = sources.get(p["article"], "")
        src_html = f'<div class="src">Источник фото: <a href="{esc(src)}">{esc(src)}</a></div>' if src else ""
        blocks.append(
            f'<div class="row"><img src="cards/{name}" alt="{esc(p["title"])}">'
            f'<div class="meta"><div class="n">Позиция {i} из {len(items)}</div>'
            f"<h2>{esc(p['title'])}</h2><table>{rows}</table>{src_html}</div></div>")

    no_price = [p for p in items if not p["price_pack"]]
    warn = ""
    if no_price:
        warn = ('<div class="warn"><b>Без цены в матрице:</b> '
                + ", ".join(f"{p['article']} — {p['title']}" for p in no_price)
                + ". Цену нужно взять у заказчика до публикации.</div>")

    html = f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lamistore — позиции для заливки</title><style>{CSS}</style></head>
<body><div class="wrap">
<h1>Lamistore — {len(items)} позиций для ручной заливки</h1>
<div class="lead">Данные из товарной матрицы, фото собраны из открытых источников.
Картинки лежат рядом в папке <code>handoff/cards/</code> — их можно грузить в Тильду как есть.</div>
{warn}
{''.join(blocks)}
</div><script>{JS}</script></body></html>"""

    (OUT / "index.html").write_text(html, encoding="utf-8")
    print(f"Позиций на странице: {len(items)}")
    print(f"-> {OUT/'index.html'}")

if __name__ == "__main__":
    main()
