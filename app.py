import math as m
import random as r
import json
import streamlit as st
import streamlit.components.v1 as components

# Configuración de Streamlit para pantalla completa en celulares
st.set_page_config(page_title="Love Heart", layout="centered", initial_sidebar_state="collapsed")

# Ocultar menús molestos de Streamlit para que parezca una app limpia
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {padding-top: 1rem; padding-bottom: 0rem; padding-left: 0rem; padding-right: 0rem;}
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DE CÁLCULO ---
SC = 17
OY = 20
DURATION = 10
ANIM = 42
GAP = 7
SIZES = (10, 11, 12, 13)
FONT = "Arial"
BG = "#060208"

rng = r.Random(11)

PHRASES = [
    "I love you", "Seni seviyorum", "Te amo", "Je t'aime",
    "Ich liebe dich", "Ti amo", "Eu te amo", "Я тебя люблю",
    "사랑해", "愛してる", "我爱你", "मैं तुमसे प्यार करता हूँ",
    "Σ' αγαπώ", "Ik hou van jou", "Jag älskar dig", "Kocham cię",
    "ฉันรักเธอ", "Anh yêu em", "Aku cinta kamu", "Я тебе кохаю",
]

def heart(a):
    x = 16 * (m.sin(a) ** 3)
    y = (13 * m.cos(a) - 5 * m.cos(2 * a) - 2 * m.cos(3 * a) - m.cos(4 * a))
    return x * SC, y * SC + OY

def mix(a, b, k):
    return tuple(p + (q - p) * k for p, q in zip(a, b))

POLY = [heart(2 * m.pi * i / 720) for i in range(720)]
EDGES = list(zip(POLY, POLY[1:] + POLY[:1]))
YMAX = max(p[1] for p in POLY)
YMIN = min(p[1] for p in POLY)
CY = (YMAX + YMIN) / 2

def spans(y):
    xs = []
    for (x1, y1), (x2, y2) in EDGES:
        if (y1 <= y < y2) or (y2 <= y < y1):
            xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
    xs.sort()
    return list(zip(xs[0::2], xs[1::2]))

def intersect(A, B):
    out = []
    for a in A:
        for b in B:
            lo, hi = max(a[0], b[0]), min(a[1], b[1])
            if hi - lo > 14:
                out.append((lo, hi))
    return out

def phrase_cycle():
    while True:
        order = PHRASES[:]
        rng.shuffle(order)
        yield from order

def math_dist(x, y):
    return m.hypot(x / (16 * SC), (y - CY) / (14.5 * SC))

def estimate_width(text, size):
    return len(text) * size * 0.62

def build():
    cycle = phrase_cycle()
    row_h = max(z * 1.2 for z in SIZES) + 4
    half = row_h / 2
    placed = []

    y = YMAX - half
    while y > YMIN + half:
        row = intersect(spans(y + half), spans(y - half))
        for lo, hi in row:
            lo += 4
            hi -= 4
            cur = lo + rng.uniform(0, 8)
            line = []
            while True:
                fit = None
                for _ in range(10):
                    text = next(cycle)
                    size = rng.choice(SIZES)
                    w = estimate_width(text, size)
                    if cur + w <= hi:
                        fit = (text, size, w)
                        break
                if not fit:
                    break
                text, size, w = fit
                line.append([cur + w / 2, text, size, w])
                cur += w + GAP

            if not line:
                continue

            if len(line) > 1:
                left = hi - (line[-1][0] + line[-1][3] / 2)
                for i, it in enumerate(line):
                    it[0] += left * i / (len(line) - 1)
            else:
                line[0][0] = (lo + hi) / 2

            for i, (x, text, size, w) in enumerate(line):
                edge = i == 0 or i == len(line) - 1
                placed.append(dict(x=x, y=y, text=text, size=size, edge=edge))
        y -= row_h

    wine = (0.58, 0.0, 0.09)
    crimson = (0.90, 0.05, 0.14)
    blood = (0.98, 0.10, 0.16)
    for p in placed:
        rad = min(1.0, math_dist(p["x"], p["y"]))
        base = mix(wine, crimson, 0.25 + 0.75 * rad)
        base = mix(base, blood, rng.uniform(0, 0.35) + (0.3 if p["edge"] else 0))
        
        # Corrección de color en RGB
        r_val = int(min(1.0, base[0]) * 255)
        g_val = int(min(1.0, base[1]) * 255)
        b_val = int(min(1.0, base[2]) * 255)
        p["color"] = f"rgb({r_val}, {g_val}, {b_val})"
        p["rad"] = rad

    edges = [p for p in placed if p["edge"]]
    inner = [p for p in placed if not p["edge"]]
    edges.sort(key=lambda p: m.atan2(p["x"], p["y"] - CY) % (2 * m.pi))
    inner.sort(key=lambda p: -p["rad"] + rng.uniform(0, 0.08))
    return edges + inner

ORDER = build()
json_data = json.dumps(ORDER)

# --- HTML5 / CANVAS JAVASCRIPT ---
html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ 
            margin: 0; 
            background-color: {BG}; 
            overflow: hidden; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
            font-family: '{FONT}', sans-serif; 
        }}
        canvas {{ 
            display: block; 
            width: 100%; 
            max-width: 600px; 
            height: auto; 
        }}
    </style>
</head>
<body>
    <canvas id="loveCanvas" width="800" height="800"></canvas>
    <script>
        const canvas = document.getElementById('loveCanvas');
        const ctx = canvas.getContext('2d');
        const data = {json_data};
        
        let active = [];
        let index = 0;
        const totalItems = data.length;
        const duration = {DURATION} * 1000; 
        const tickRate = 16;
        const rate = totalItems / (duration / tickRate);
        let acc = 0;
        let mainIds = [];

        function clamp(v) {{ return Math.max(0.0, Math.min(1.0, v)); }}
        
        function parseRGB(rgbStr) {{
            const match = rgbStr.match(/\\d+/g);
            return [parseInt(match[0]), parseInt(match[1]), parseInt(match[2])];
        }}

        function mixColors(c1, c2, k) {{
            return [
                Math.round(c1[0] + (c2[0] - c1[0]) * k),
                Math.round(c1[1] + (c2[1] - c1[1]) * k),
                Math.round(c1[2] + (c2[2] - c1[2]) * k)
            ];
        }}

        function step() {{
            ctx.fillStyle = '{BG}';
            ctx.fillRect(0, 0, 800, 800);

            if (index < totalItems) {{
                acc += rate;
                while (acc >= 1 && index < totalItems) {{
                    acc -= 1;
                    let item = data[index++];
                    item.f = 0;
                    item.dx = (Math.random() * 20) - 10;
                    item.done = false;
                    active.push(item);
                    mainIds.push(item);
                }}
            }}

            for (let i = 0; i < active.length; i++) {{
                let p = active[i];
                if (!p.done) p.f += 1;
                
                let u = clamp(p.f / {ANIM});
                let e = 1 - Math.pow(1 - u, 3);
                
                let cx = 400 + p.x;
                let cy = 400 - p.y;
                
                let hover = (1 - e) * 34;
                let px = cx + p.dx * (1 - e);
                let py = cy - hover;

                ctx.font = "bold " + p.size + "px {FONT}";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";

                let baseColor = parseRGB(p.color);
                let bgRGB = [6, 2, 8]; // Corregido: arreglo RGB de #060208

                if (!p.done) {{
                    ctx.fillStyle = `rgb(${{mixColors(bgRGB, mixColors(baseColor, [0,0,0], 0.3), e).join(',')}})`;
                    ctx.fillText(p.text, px + 2, py + 3);

                    let flash = 0.75 * Math.sin(Math.PI * clamp((u - 0.55) / 0.45));
                    let col = mixColors(mixColors(bgRGB, baseColor, Math.pow(e, 1.5)), [255, 199, 199], flash);
                    ctx.fillStyle = `rgb(${{col.join(',')}})`;
                    ctx.fillText(p.text, px, py);

                    if (u >= 1) p.done = true;
                }} else {{
                    ctx.fillStyle = `rgb(${{mixColors(bgRGB, mixColors(baseColor, [0,0,0], 0.3), 1).join(',')}})`;
                    ctx.fillText(p.text, cx + 2, cy + 3);
                    ctx.fillStyle = p.color;
                    ctx.fillText(p.text, cx, cy);
                }}
            }}

            if (index >= totalItems) {{
                if (Math.random() < 0.15) {{
                    let target = mainIds[Math.floor(Math.random() * mainIds.length)];
                    let origColor = target.color;
                    target.color = "rgb(255, 200, 200)";
                    setTimeout(() => {{ target.color = origColor; }}, 260);
                }}
            }}

            requestAnimationFrame(step);
        }}

        setTimeout(step, 200);
    </script>
</body>
</html>
"""

components.html(html_code, height=720, scrolling=False)
