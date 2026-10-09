"""HTML-шаблон карточки товара Lamistore.

Геометрия вынесена в константы: когда придут точные размеры из Figma,
правим только их, перерисовка всего каталога — один прогон render_cards.py.
"""
import math, re

# --- Холст ----------------------------------------------------------------
W, H      = 1200, 1500          # 4:5, как в макете
# Углы строго прямые: скругление оставляет прозрачные уголки,
# которые на тёмном фоне показываются чёрными.
RADIUS    = 0
BG        = "#FFFFFF"
PAD       = 64

# --- Лейблы ---------------------------------------------------------------
LABEL_BORDER = "#9F9067"        # оливковый из иконок макета (Frame 67-71)
LABEL_TEXT   = "#1A1A1A"
LABEL_FS     = 34
LABEL_PAD    = "18px 28px"
LABEL_RADIUS = 8
LABEL_GAP    = 16

# --- Ромб с текстурой -----------------------------------------------------
# Верхняя вершина ромба в долях от размеров карточки (снято с макета).
APEX_X, APEX_Y = 0.68, 0.266

# Коллекции с диагональной укладкой: у них рисунок сам по себе под углом,
# и поворот текстуры на 45° превращает ёлочку в обычные прямые планки.
# Для них ромб остаётся, а текстура внутри не поворачивается.
DIAGONAL_PATTERN = re.compile(r"herringbone|chevron|parquet|ёлоч|елоч|ёлка|elka", re.I)

def is_diagonal(collection):
    return bool(collection and DIAGONAL_PATTERN.search(collection))

def diamond(w=W, h=H, apex_x=APEX_X, apex_y=APEX_Y):
    """Половина диагонали ромба и его вершина — такие, чтобы накрыть низ карточки.

    Ромб в метрике L1: точка (x, y) внутри, если |x-cx| + |y-cy| <= d.
    Берём d, при котором накрыты оба нижних угла карточки.
    """
    ax, ay = apex_x * w, apex_y * h
    d = max((ax + h - ay) / 2, ((w - ax) + h - ay) / 2)
    return d * 1.02, ax, ay       # запас на скругление углов

D, AX, AY = diamond()
SIDE = D * 2 / math.sqrt(2)       # сторона квадрата, вписанного в ромб
# Вершины ромба: верх, лево, низ, право. Выход за рамку карточки режет overflow.
POLY = (f"{AX}px {AY}px, {AX - D}px {AY + D}px, "
        f"{AX}px {AY + 2 * D}px, {AX + D}px {AY + D}px")

HTML = """<!doctype html>
<html><head><meta charset="utf-8"><style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html, body {{ width:{W}px; height:{H}px; background:transparent; }}
  .card {{
    position:relative; width:{W}px; height:{H}px;
    background:{BG}; border-radius:{RADIUS}px; overflow:hidden;
    font-family:'Inter','Helvetica Neue',Helvetica,Arial,sans-serif;
    -webkit-font-smoothing:antialiased;
  }}
  /* Силуэт ромба один и тот же; поворачивается только текстура внутри. */
  .clip {{ position:absolute; inset:0; clip-path:polygon({POLY}); }}
  .tex {{
    position:absolute; {TEX_BOX}
    background-image:url('{TEXTURE}');
    background-size:cover; background-position:center;
  }}
  .labels {{
    position:absolute; left:{PAD}px; top:{PAD}px; z-index:2;
    display:flex; flex-direction:column; align-items:flex-start; gap:{LABEL_GAP}px;
  }}
  .row {{ display:flex; gap:{LABEL_GAP}px; }}
  .lbl {{
    border:2px solid {LABEL_BORDER}; border-radius:{LABEL_RADIUS}px;
    padding:{LABEL_PAD}; font-size:{LABEL_FS}px; line-height:1.15;
    color:{LABEL_TEXT}; white-space:nowrap; background:rgba(255,255,255,.92);
  }}
</style></head><body>
  <div class="card">
    <div class="clip"><div class="tex"></div></div>
    <div class="labels">{LABELS}</div>
  </div>
</body></html>"""

# Планки под 45°: квадрат со стороной SIDE, повёрнутый вокруг центра ромба.
ROTATED_BOX = (f"width:{round(SIDE)}px; height:{round(SIDE)}px; "
               f"left:{round(AX - SIDE / 2)}px; top:{round(AY + D - SIDE / 2)}px; "
               f"transform:rotate(45deg); transform-origin:center center;")
# Диагональный рисунок: текстура во всю карточку, без поворота.
UPRIGHT_BOX = "inset:0;"

def label(text):
    return f'<div class="lbl">{text}</div>'

def build(texture_url, lines, rows, diagonal=False):
    """lines — лейблы в столбик, rows — списки лейблов в одну строку.
    diagonal=True — рисунок уже диагональный (ёлочка), текстуру не вращаем."""
    blocks = [label(t) for t in lines]
    for r in rows:
        blocks.append('<div class="row">' + "".join(label(t) for t in r) + "</div>")
    return HTML.format(
        W=W, H=H, BG=BG, RADIUS=RADIUS, PAD=PAD, POLY=POLY,
        TEX_BOX=UPRIGHT_BOX if diagonal else ROTATED_BOX,
        TEXTURE=texture_url, LABELS="".join(blocks),
        LABEL_BORDER=LABEL_BORDER, LABEL_TEXT=LABEL_TEXT, LABEL_FS=LABEL_FS,
        LABEL_PAD=LABEL_PAD, LABEL_RADIUS=LABEL_RADIUS, LABEL_GAP=LABEL_GAP)
