#!/usr/bin/env python3
"""Статическая витрина каталога: демо для согласования + хостинг картинок для Тильды.

Карточки из cards/*.png пережимаются в JPEG — 131 PNG весит ~220 МБ,
что тяжело и для репозитория, и для загрузки Тильдой по URL.
"""
import json, pathlib, shutil
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
OUT  = SITE / "cards"
WEB_WIDTH, JPEG_QUALITY = 900, 86

def optimize(src, dst):
    im = Image.open(src).convert("RGB")
    if im.width > WEB_WIDTH:
        im = im.resize((WEB_WIDTH, round(im.height * WEB_WIDTH / im.width)), Image.LANCZOS)
    im.save(dst, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    return dst.stat().st_size

def money(v):
    return f"{v:,.0f}".replace(",", " ") if v else None

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#F2F2F2; --card:#FFF; --ink:#1A1A1A; --muted:#8A8A8A;
  --line:#E3E3E3; --accent:#9F9067;
}
:root:not([data-theme="light"]){
  @media (prefers-color-scheme: dark){
    --bg:#141414; --card:#1E1E1E; --ink:#F2F2F2; --muted:#8A8A8A; --line:#2E2E2E;
  }
}
:root[data-theme="dark"]{--bg:#141414;--card:#1E1E1E;--ink:#F2F2F2;--muted:#8A8A8A;--line:#2E2E2E}
body{
  background:var(--bg); color:var(--ink); min-height:100vh;
  font-family:'Inter','Helvetica Neue',Helvetica,Arial,sans-serif;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:1280px; margin:0 auto; padding:56px 16px 96px}
header{margin-bottom:12px}
h1{font-size:30px; letter-spacing:-.02em}
.sub{color:var(--muted); font-size:15px; margin-top:8px; line-height:1.5}
.bar{display:flex; flex-wrap:wrap; gap:8px; margin:28px 0 32px}
.chip{
  border:1px solid var(--line); background:var(--card); color:var(--ink);
  border-radius:999px; padding:9px 18px; font-size:14px; cursor:pointer;
}
.chip[aria-pressed="true"]{border-color:var(--accent); box-shadow:inset 0 0 0 1px var(--accent)}
.grid{display:grid; grid-template-columns:repeat(auto-fill,minmax(230px,1fr)); gap:28px}
.item img{
  width:100%; aspect-ratio:4/5; object-fit:cover; display:block;
  border-radius:14px; background:var(--card); border:1px solid var(--line);
}
.art{color:var(--muted); font-size:12px; margin-top:14px}
.name{font-size:15px; font-weight:600; margin-top:4px; line-height:1.35}
.price{font-size:14px; color:var(--muted); margin-top:6px}
.price b{color:var(--ink); font-weight:600}
.empty{color:var(--muted); font-size:14px}
footer{margin-top:64px; padding-top:24px; border-top:1px solid var(--line);
       color:var(--muted); font-size:13px; line-height:1.7}
@media(max-width:600px){ .wrap{padding:32px 16px 64px} h1{font-size:23px} }
"""

JS = """
const chips=[...document.querySelectorAll('.chip')];
chips.forEach(c=>c.addEventListener('click',()=>{
  chips.forEach(x=>x.setAttribute('aria-pressed', x===c));
  const b=c.dataset.brand;
  document.querySelectorAll('.item').forEach(el=>{
    el.hidden = b!=='*' && el.dataset.brand!==b;
  });
}));
"""

def main():
    products = json.loads((ROOT / "data" / "products.json").read_text(encoding="utf-8"))
    items = [p for p in products if p["card"]]
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    total = 0
    for p in items:
        jpg = OUT / (pathlib.Path(p["card"]).stem + ".jpg")
        total += optimize(ROOT / "cards" / p["card"], jpg)
        p["web_card"] = jpg.name

    brands = list(dict.fromkeys(p["brand"] for p in items))
    chips = ['<button class="chip" data-brand="*" aria-pressed="true">Все</button>'] + [
        f'<button class="chip" data-brand="{b}" aria-pressed="false">{b}</button>' for b in brands]

    cells = []
    for p in items:
        price = money(p["price_pack"])
        price_html = (f'<b>{price} сом</b> / упак' if price else
                      '<span style="opacity:.7">цена уточняется</span>')
        cells.append(
            f'<div class="item" data-brand="{p["brand"]}">'
            f'<img src="cards/{p["web_card"]}" alt="{p["title"]}" loading="lazy">'
            f'<div class="art">Арт. {p["article"] or "—"}</div>'
            f'<div class="name">{p["title"]}</div>'
            f'<div class="price">{price_html}</div></div>')

    done, left = len(items), len(products) - len(items)
    html = f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lamistore — каталог</title>
<style>{CSS}</style></head>
<body><div class="wrap">
<header>
  <h1>Lamistore — каталог, образец</h1>
  <div class="sub">
    {done} из {len(products)} позиций товарной матрицы.<br>
    Карточки собраны автоматически: матрица → текстуры декоров → вёрстка → PNG.
    Так же будут собраны остальные {left}, как только появятся текстуры.
  </div>
</header>
<div class="bar">{''.join(chips)}</div>
<div class="grid">{''.join(cells)}</div>
<footer>
  Демо для согласования шаблона карточки. Геометрия и типографика снимались с макета —
  уточняются по Figma.<br>
  Эти же файлы служат источником картинок при импорте в Магазин Тильды.
</footer>
</div><script>{JS}</script></body></html>"""

    (SITE / "index.html").write_text(html, encoding="utf-8")
    (ROOT / "data" / "products.json").write_text(
        json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Карточек на витрине: {done}")
    print(f"JPEG: {total/1e6:.1f} МБ  (в среднем {total/done/1024:.0f} КБ)")
    print(f"Прогноз на 131 позицию: ~{total/done*131/1e6:.0f} МБ")
    print(f"-> {SITE/'index.html'}")

if __name__ == "__main__":
    main()
