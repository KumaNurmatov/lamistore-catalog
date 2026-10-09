#!/usr/bin/env python3
"""Массовый сбор кадров с eparket по списку data/todo_sources.json.

Адреса товаров уже сопоставлены с артикулами матрицы, поэтому карту сайта
заново не читаем. Все кадры складываются в textures/_candidates — какой из них
выкладка планок, решаем потом по контактному листу.
"""
import json, pathlib, re, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAND = ROOT / "textures" / "_candidates"; CAND.mkdir(parents=True, exist_ok=True)
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")
IMG = re.compile(r"https://eparket\.com/images/product/\d+/\d+/\d+-(\d+)_full\.webp")
BASE = re.compile(r"(https://eparket\.com/images/product/\d+/\d+/\d+)-\d+_full\.webp")

def get(url, referer="https://eparket.com/", retries=3):
    for i in range(retries):
        r = subprocess.run(["curl", "-sS", "-m", "90", "-L", "-A", UA, "-e", referer, url],
                           capture_output=True)
        if r.returncode == 0 and r.stdout:
            return r.stdout
        time.sleep(2 * (i + 1))
    return None

def safe(article):
    """Артикулы вроде AF6026PQ+ нельзя класть в имя файла как есть."""
    return re.sub(r"[^A-Za-z0-9._-]", "_", article)

def main():
    todo = json.loads((ROOT / "data" / "todo_sources.json").read_text(encoding="utf-8"))
    todo = [t for t in todo if t["url"] != "locfloor"]
    out_path = ROOT / "data" / "eparket_found.json"
    found = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {}

    for n, t in enumerate(todo, 1):
        art = t["article"]
        if art in found and found[art].get("candidates"):
            print(f"[{n}/{len(todo)}] {art:<14} уже есть", flush=True); continue
        page = get(t["url"])
        if not page:
            print(f"[{n}/{len(todo)}] {art:<14} СТРАНИЦА НЕ ОТКРЫЛАСЬ", flush=True); continue
        page = page.decode("utf-8", "replace")
        title = re.search(r"<title>([^<]*)</title>", page)
        base = BASE.search(page)
        shots = sorted(set(IMG.findall(page)), key=int)
        saved = []
        if base:
            for s in shots:
                data = get(f"{base.group(1)}-{s}_2000.avif", referer=t["url"])
                ext = ".avif"
                if not data or len(data) < 5000:
                    data = get(f"{base.group(1)}-{s}_full.webp", referer=t["url"]); ext = ".webp"
                if data and len(data) > 5000:
                    dst = CAND / f"{safe(art)}-{s}{ext}"
                    dst.write_bytes(data); saved.append(dst.name)
                time.sleep(.25)
        found[art] = {"url": t["url"], "title": title.group(1).strip() if title else "",
                      "candidates": saved}
        out_path.write_text(json.dumps(found, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[{n}/{len(todo)}] {art:<14} {len(saved)} кадр(ов)", flush=True)
        time.sleep(.3)
    print("ГОТОВО")

if __name__ == "__main__":
    main()
