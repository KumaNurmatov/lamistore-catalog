#!/usr/bin/env python3
"""Из рендера одной планки собирает плоскую выкладку пола.

У ALSAFLOOR на официальном сайте выложены не выкладки, а рендеры одной планки
под углом. Проекция там параллельная (не перспективная), поэтому лицевую грань
можно выпрямить аффинным преобразованием точно, без искажений, а потом замостить.
"""
import pathlib, sys
import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEX = ROOT / "textures"

def face_corners(im):
    """Четыре угла лицевой грани. Фон белый, торец почти чёрный — отсекаем оба."""
    a = np.asarray(im.convert("RGB")).astype(int)
    bright = a.sum(axis=2)
    mask = (bright < 720) & (bright > 120)       # не фон и не чёрный торец
    ys, xs = np.nonzero(mask)
    if len(xs) < 1000:
        raise ValueError("грань не найдена")
    s, d = xs + ys, xs - ys
    # Параллелограмм: крайние точки по суммам и разностям координат.
    tl = (xs[np.argmin(s)], ys[np.argmin(s)])
    br = (xs[np.argmax(s)], ys[np.argmax(s)])
    tr = (xs[np.argmax(d)], ys[np.argmax(d)])
    bl = (xs[np.argmin(d)], ys[np.argmin(d)])
    return tl, tr, br, bl

def flatten(im, out_w=1400, out_h=320):
    """Выпрямляет грань в прямоугольник."""
    tl, tr, br, bl = face_corners(im)
    # PIL ждёт коэффициенты обратного преобразования: выход -> вход.
    src = [tl, tr, br, bl]
    dst = [(0, 0), (out_w, 0), (out_w, out_h), (0, out_h)]
    A, B = [], []
    for (sx, sy), (dx, dy) in zip(src, dst):
        A.append([dx, dy, 1, 0, 0, 0, -dx * sx, -dy * sx]); B.append(sx)
        A.append([0, 0, 0, dx, dy, 1, -dx * sy, -dy * sy]); B.append(sy)
    coeffs = np.linalg.lstsq(np.array(A, float), np.array(B, float), rcond=None)[0]
    return im.convert("RGB").transform((out_w, out_h), Image.PERSPECTIVE,
                                       tuple(coeffs), Image.BICUBIC)

def herringbone(plank, size=1600, pw=150, ph=600):
    """Выкладка ёлочкой: планки под +45 и -45, уложенные в шахматном ритме."""
    base = plank.resize((ph, pw), Image.LANCZOS)      # горизонтальная планка
    a = base.rotate(45, expand=True, resample=Image.BICUBIC)
    b = base.rotate(-45, expand=True, resample=Image.BICUBIC)
    canvas = Image.new("RGB", (size * 2, size * 2), (235, 230, 222))
    step = int((pw + ph) / 2 ** 0.5)
    for row in range(-1, size * 2 // step + 2):
        for col in range(-1, size * 2 // step + 2):
            x = col * step
            y = row * step + (step // 2 if col % 2 else 0)
            canvas.paste(a, (x - a.width // 2, y - a.height // 2))
            canvas.paste(b, (x - b.width // 2 + step // 2, y - b.height // 2))
    return canvas.crop((size // 2, size // 2, size // 2 + size, size // 2 + size))

def main():
    for art in sys.argv[1:]:
        src = None
        for ext in (".png", ".jpg", ".webp"):
            f = TEX / f"{art}{ext}"
            if f.exists(): src = f; break
        if not src:
            print(f"  {art}: нет файла"); continue
        im = Image.open(src)
        flat = flatten(im)
        out = TEX / "_flat" / f"{art}-flat.jpg"
        out.parent.mkdir(exist_ok=True)
        flat.save(out, "JPEG", quality=94)
        lay = herringbone(flat)
        lo = TEX / "_layout" / f"{art}-layout.jpg"
        lo.parent.mkdir(exist_ok=True)
        lay.save(lo, "JPEG", quality=92)
        print(f"  {art:<6} грань {flat.size} -> выкладка {lay.size}")

if __name__ == "__main__":
    main()
