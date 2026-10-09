#!/usr/bin/env python3
"""products.json + textures/ -> PNG-карточки для каталога Тильды."""
import json, pathlib, re, subprocess, sys, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import card_template as T

ROOT   = pathlib.Path(__file__).resolve().parent.parent
TEX    = ROOT / "textures"
CARDS  = ROOT / "cards"; CARDS.mkdir(exist_ok=True)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

def find_texture(p):
    """Текстуру ищем по артикулу — так она привязана к позиции матрицы."""
    if not p["article"]:
        return None
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", p["article"])
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        f = TEX / f"{safe}{ext}"
        if f.exists():
            return f
    return None

def labels_for(p):
    """Состав лейблов повторяет макет: бренд, декор, затем класс и толщина в строку."""
    lines = [f"Ламинат {p['brand']}"]
    if p["decor"]:
        lines.append(p["decor"])
    elif p["article"]:
        lines.append(p["article"])
    row = []
    if p["wear_class"]:
        row.append(f"{p['wear_class']} класс")
    if p["thickness_mm"]:
        row.append(f"Толщина: {p['thickness_mm']:g} мм")
    return lines, ([row] if row else [])

def render(html, out):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html); src = f.name
    try:
        r = subprocess.run([
            CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
            "--force-device-scale-factor=1",
            # Фон непрозрачный: прозрачность в PNG оборачивается чёрными углами.
            "--default-background-color=ffffffff",
            f"--window-size={T.W},{T.H}",
            f"--screenshot={out}", f"file://{src}",
        ], capture_output=True, timeout=120)
        if not out.exists():
            raise RuntimeError(r.stderr.decode()[:300])
    finally:
        pathlib.Path(src).unlink(missing_ok=True)

def main():
    products = json.loads((ROOT / "data" / "products.json").read_text(encoding="utf-8"))
    only = sys.argv[1:] or None

    done = skipped = 0
    for p in products:
        if only and p["article"] not in only and p["sku"] not in only:
            continue
        tex = find_texture(p)
        if not tex:
            skipped += 1
            continue
        lines, rows = labels_for(p)
        html = T.build(tex.resolve().as_uri(), lines, rows,
                       diagonal=T.is_diagonal(p["collection"]))
        out = CARDS / f"{p['sku']}.png"
        render(html, out)
        p["texture"] = tex.name
        p["card"] = out.name
        done += 1
        print(f"  {p['article'] or p['sku']:10} -> {out.name}  ({out.stat().st_size/1024:.0f} КБ)")

    (ROOT / "data" / "products.json").write_text(
        json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nОтрисовано: {done}   без текстуры: {skipped}")

if __name__ == "__main__":
    main()
