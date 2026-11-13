#!/usr/bin/env python3
"""
"Leviathan Bloom" - a colossal luminous jellyfish rising over a night ocean.

Pure procedural art: every pixel is drawn by this program at run time
(Python 3.13 standard library only, no network, fully deterministic).
The image is rendered into an RGB buffer with a small software rasterizer
(scanline polygon fills, soft ellipses, additive glow accumulated in a
half-resolution buffer), then written as a PNG with a zlib/struct encoder.

Output: $MAKEFUN_OUTPUT_DIR/entry.png  (1024x1024, < 1 MiB)
"""

import math
import os
import random
import struct
import zlib
from array import array

W = 1024
H = 1024
HORIZON = 648          # sea line
CX = 512               # jellyfish centre x
BELL_TOP = 148
BELL_RX = 268
BELL_RY = 218
BELL_EQ = BELL_TOP + BELL_RY   # bell equator y (~366)

rng = random.Random(20261112)

# ---------------------------------------------------------------- buffers
img = bytearray(W * H * 3)                 # final RGB image
GW, GH = W // 2, H // 2                    # glow buffer resolution
glow = array("f", bytes(4 * GW * GH * 3))  # additive light, float rgb


def clamp(v):
    return 0 if v < 0 else (255 if v > 255 else int(v))


def lerp(a, b, t):
    return a + (b - a) * t


def lerp3(c1, c2, t):
    return (lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t))


# ---------------------------------------------------------------- painting
def blend_px(x, y, col, alpha):
    """Alpha-blend one pixel of the main image."""
    if 0 <= x < W and 0 <= y < H and alpha > 0.0:
        i = (y * W + x) * 3
        ia = 1.0 - alpha
        img[i] = clamp(img[i] * ia + col[0] * alpha)
        img[i + 1] = clamp(img[i + 1] * ia + col[1] * alpha)
        img[i + 2] = clamp(img[i + 2] * ia + col[2] * alpha)


def fill_rows(y0, y1, c_top, c_bot):
    """Vertical gradient band, whole width (fast slice writes)."""
    for y in range(y0, y1):
        t = (y - y0) / max(1, (y1 - y0 - 1))
        c = lerp3(c_top, c_bot, t)
        row = bytes((clamp(c[0]), clamp(c[1]), clamp(c[2]))) * W
        img[y * W * 3:(y + 1) * W * 3] = row


def add_glow(cx, cy, radius, col, peak):
    """Add a soft radial light into the half-res glow buffer."""
    gx, gy, gr = cx * 0.5, cy * 0.5, radius * 0.5
    r2 = gr * gr
    x0 = max(0, int(gx - gr)); x1 = min(GW - 1, int(gx + gr))
    y0 = max(0, int(gy - gr)); y1 = min(GH - 1, int(gy + gr))
    cr, cg, cb = col
    for y in range(y0, y1 + 1):
        dy = y - gy
        dy2 = dy * dy
        base = y * GW * 3
        for x in range(x0, x1 + 1):
            dx = x - gx
            d2 = dx * dx + dy2
            if d2 < r2:
                f = 1.0 - d2 / r2
                f = f * f * peak
                i = base + x * 3
                glow[i] += cr * f
                glow[i + 1] += cg * f
                glow[i + 2] += cb * f


def fill_poly(points, color_fn, alpha_fn=None):
    """Scanline polygon fill. color_fn(y)->(r,g,b); alpha_fn(y)->0..1."""
    ys = [p[1] for p in points]
    y_lo = max(0, int(min(ys)))
    y_hi = min(H - 1, int(max(ys)))
    n = len(points)
    edges = []
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        if y1 != y2:
            edges.append((y1, y2, x1, (x2 - x1) / (y2 - y1)))
    for y in range(y_lo, y_hi + 1):
        yc = y + 0.5
        xs = []
        for (y1, y2, x1, slope) in edges:
            if (y1 <= yc < y2) or (y2 <= yc < y1):
                xs.append(x1 + (yc - y1) * slope)
        if len(xs) < 2:
            continue
        xs.sort()
        col = color_fn(y)
        alpha = 0.9 if alpha_fn is None else alpha_fn(y)
        if alpha <= 0.0:
            continue
        ia = 1.0 - alpha
        r, g, b = col
        rowbase = y * W * 3
        for k in range(0, len(xs) - 1, 2):
            xa = max(0, int(math.ceil(xs[k] - 0.5)))
            xb = min(W - 1, int(math.floor(xs[k + 1] - 0.5)))
            for x in range(xa, xb + 1):
                i = rowbase + x * 3
                img[i] = clamp(img[i] * ia + r * alpha)
                img[i + 1] = clamp(img[i + 1] * ia + g * alpha)
                img[i + 2] = clamp(img[i + 2] * ia + b * alpha)


def soft_ellipse(cx, cy, rx, ry, col, alpha):
    """Filled ellipse with a soft (feathered) edge, alpha blended."""
    x0 = max(0, int(cx - rx)); x1 = min(W - 1, int(cx + rx))
    y0 = max(0, int(cy - ry)); y1 = min(H - 1, int(cy + ry))
    for y in range(y0, y1 + 1):
        dy = (y - cy) / ry
        rowbase = y * W * 3
        for x in range(x0, x1 + 1):
            dx = (x - cx) / rx
            q = dx * dx + dy * dy
            if q < 1.0:
                a = alpha * (1.0 - q) ** 1.5
                if a > 0.003:
                    ia = 1.0 - a
                    i = rowbase + x * 3
                    img[i] = clamp(img[i] * ia + col[0] * a)
                    img[i + 1] = clamp(img[i + 1] * ia + col[1] * a)
                    img[i + 2] = clamp(img[i + 2] * ia + col[2] * a)


def stamp(cx, cy, r, col, alpha):
    """Small soft disc."""
    x0 = max(0, int(cx - r - 1)); x1 = min(W - 1, int(cx + r + 1))
    y0 = max(0, int(cy - r - 1)); y1 = min(H - 1, int(cy + r + 1))
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            d = math.hypot(x - cx, y - cy)
            if d < r + 1.0:
                a = alpha * max(0.0, min(1.0, (r + 1.0 - d) / 2.0 + 0.5 * (d < r)))
                a = alpha * max(0.0, (r + 1.0 - d) / (r + 1.0)) ** 0.7 if d > r - 1 else alpha
                blend_px(x, y, col, a)


def stroke_path(pts, width, col, alpha):
    """Thick polyline: stamps along the path."""
    r = width * 0.5
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        steps = max(1, int(math.hypot(x2 - x1, y2 - y1) / 1.5))
        for s in range(steps + 1):
            t = s / steps
            stamp(lerp(x1, x2, t), lerp(y1, y2, t), r, col, alpha)


def ribbon(points, width_fn, color_fn, alpha_fn):
    """Filled ribbon along a path; width/color/alpha are functions of t."""
    left, right = [], []
    n = len(points)
    for i in range(n):
        x, y = points[i]
        if i == 0:
            dx, dy = points[1][0] - x, points[1][1] - y
        elif i == n - 1:
            dx, dy = x - points[i - 1][0], y - points[i - 1][1]
        else:
            dx, dy = points[i + 1][0] - points[i - 1][0], points[i + 1][1] - points[i - 1][1]
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        hw = width_fn(i / (n - 1)) * 0.5
        left.append((x + nx * hw, y + ny * hw))
        right.append((x - nx * hw, y - ny * hw))
    poly = left + right[::-1]

    # colour/alpha vary along the path, approximated per scanline via y
    y_top = points[0][1]
    y_bot = points[-1][1]
    span = max(1.0, y_bot - y_top)

    def cfn(y):
        return color_fn(min(1.0, max(0.0, (y - y_top) / span)))

    def afn(y):
        return alpha_fn(min(1.0, max(0.0, (y - y_top) / span)))

    fill_poly(poly, cfn, afn)


# ---------------------------------------------------------------- scene
def paint_background():
    # sky: deep indigo -> teal at the horizon
    fill_rows(0, HORIZON, (4, 6, 20), (10, 48, 74))
    # sea: dark teal -> near black at the bottom
    fill_rows(HORIZON, H, (8, 40, 58), (2, 6, 14))
    # nebula washes
    add_glow(210, 150, 430, (0.16, 0.05, 0.30), 0.50)
    add_glow(850, 110, 380, (0.02, 0.20, 0.26), 0.45)
    add_glow(560, 560, 520, (0.0, 0.22, 0.26), 0.35)   # horizon bloom


def paint_stars():
    for _ in range(300):
        x = rng.uniform(0, W)
        y = rng.uniform(0, HORIZON - 30) * rng.uniform(0.25, 1.0)
        a = rng.uniform(0.15, 0.8)
        col = (210, 235, 255) if rng.random() < 0.7 else (170, 220, 255)
        blend_px(int(x), int(y), col, a)
        if rng.random() < 0.14:
            blend_px(int(x) + 1, int(y), col, a * 0.5)
    for _ in range(26):  # brighter stars with a cross sparkle
        x = rng.uniform(20, W - 20)
        y = rng.uniform(10, HORIZON - 120)
        col = (235, 250, 255)
        stamp(x, y, 1.6, col, 0.9)
        for d in (2, 3, 4):
            a = 0.34 - d * 0.07
            blend_px(int(x) + d, int(y), col, a)
            blend_px(int(x) - d, int(y), col, a)
            blend_px(int(x), int(y) + d, col, a)
            blend_px(int(x), int(y) - d, col, a)
    # one shooting star, upper left
    sx, sy = 120.0, 118.0
    for i in range(46):
        t = i / 46
        stamp(sx + i * 3.4, sy + i * 1.35, 2.2 * (1 - t) + 0.4,
              (220, 245, 255), 0.55 * (1 - t) ** 1.5)


def tentacle_path(x0, length, sway, phase, y0=372.0, step=9.0):
    pts = []
    n = int(length / step)
    for i in range(n + 1):
        t = i / n
        y = y0 + length * t
        x = x0 + math.sin(t * 3.1 + phase) * sway * t \
            + math.sin(t * 7.3 + phase * 2.0) * sway * 0.22 * t
        pts.append((x, y))
    return pts


def paint_tentacles():
    # fine thread tentacles first (behind)
    for k in range(26):
        x0 = CX + (k - 12.5) * 15.5 + rng.uniform(-5, 5)
        length = rng.uniform(430, 600)
        pts = tentacle_path(x0, length, rng.uniform(16, 34), rng.uniform(0, 6.28))
        stroke_path(pts[::2], 1.4, (150, 225, 255), 0.30)
    # main ribbons
    mains = []
    for k in range(10):
        frac = (k - 4.5) / 4.5
        x0 = CX + frac * 205
        length = 560 - abs(frac) * 190 + rng.uniform(-25, 25)
        sway = rng.uniform(22, 46) * (1 if frac >= 0 else -1) * 0.4 + rng.uniform(-8, 8)
        phase = rng.uniform(0, 6.28)
        pts = tentacle_path(x0, length, abs(sway) + 14, phase)
        mains.append(pts)
        if k % 2 == 0:
            c_top, c_bot = (70, 224, 255), (176, 107, 255)
        else:
            c_top, c_bot = (120, 240, 255), (255, 79, 216)
        w0 = 13 - abs(frac) * 4
        ribbon(pts, lambda t, w0=w0: w0 * (1 - t) ** 0.8 + 1.2,
               lambda t, a=c_top, b=c_bot: lerp3(a, b, t),
               lambda t: 0.22)
        ribbon(pts, lambda t, w0=w0: w0 * 0.62 * (1 - t) ** 0.8 + 0.8,
               lambda t, a=c_top, b=c_bot: lerp3(a, b, t),
               lambda t: 0.38)
        ribbon(pts, lambda t, w0=w0: w0 * 0.30 * (1 - t) ** 0.8 + 0.4,
               lambda t, a=c_top, b=c_bot: lerp3((235, 253, 255), b, t),
               lambda t: 0.75)


def paint_bell():
    # halo + core light (into glow buffer)
    add_glow(CX, 330, 470, (0.10, 0.55, 0.70), 0.85)
    add_glow(CX, 300, 185, (0.55, 0.95, 1.0), 0.27)
    add_glow(CX, 470, 320, (0.55, 0.12, 0.55), 0.40)

    # dome outline: top arc + scalloped lower margin
    pts = []
    steps = 72
    for i in range(steps + 1):
        a = math.pi * i / steps            # 0..pi, right -> top -> left
        pts.append((CX + BELL_RX * math.cos(a), BELL_EQ - BELL_RY * math.sin(a)))
    scallops = 7
    for s in range(scallops):
        for j in range(1, 9):
            t = j / 8
            x = lerp(pts[-1][0], CX + BELL_RX, (s + t) / scallops) if False else \
                CX - BELL_RX + 2 * BELL_RX * (s + t) / scallops
            y = BELL_EQ + 20 * math.sin(t * math.pi) + 6
            pts.append((x, y))

    def bell_col(y):
        t = (y - BELL_TOP) / (BELL_EQ - BELL_TOP + 26)
        if t < 0.5:
            return lerp3((168, 238, 255), (36, 172, 236), t * 2)
        return lerp3((36, 172, 236), (110, 66, 220), (t - 0.5) * 2)

    fill_poly(pts, bell_col, lambda y: 0.94)

    # inner dome (magenta-violet heart)
    ipts = []
    for i in range(steps + 1):
        a = math.pi * i / steps
        ipts.append((CX + BELL_RX * 0.70 * math.cos(a),
                     BELL_EQ - 6 - BELL_RY * 0.70 * math.sin(a)))
    for s in range(5):
        for j in range(1, 7):
            t = j / 6
            x = CX - BELL_RX * 0.70 + 2 * BELL_RX * 0.70 * (s + t) / 5
            ipts.append((x, BELL_EQ - 6 + 12 * math.sin(t * math.pi)))
    fill_poly(ipts, lambda y: lerp3((238, 84, 204), (118, 58, 224),
                                    (y - BELL_TOP) / 260), lambda y: 0.52)

    # canopy highlight, upper left (kept faint so the colour shows through)
    soft_ellipse(CX - 108, 216, 96, 52, (240, 255, 255), 0.15)

    # amber gonad ring (the classic four-lobed organ), drawn on top so it reads;
    # deep saturated orange so the warm hue survives the cyan glow in composite
    for (gx, gy, grx, gry) in ((CX - 74, 252, 56, 40), (CX + 74, 252, 56, 40),
                               (CX - 138, 292, 44, 32), (CX + 138, 292, 44, 32)):
        soft_ellipse(gx, gy, grx, gry, (250, 106, 22), 0.92)
        soft_ellipse(gx, gy, grx * 0.55, gry * 0.55, (255, 152, 48), 0.85)
        add_glow(gx, gy, 90, (0.65, 0.30, 0.04), 0.30)

    # rim light along the dome edge
    rim = [(CX + (BELL_RX + 2) * math.cos(math.pi * i / steps),
            BELL_EQ - (BELL_RY + 2) * math.sin(math.pi * i / steps))
           for i in range(steps + 1)]
    stroke_path(rim, 13, (64, 200, 245), 0.16)
    stroke_path(rim, 5, (214, 250, 255), 0.85)
    # glowing margin line under the bell
    marg = [(CX - BELL_RX + 2 * BELL_RX * i / 60,
             BELL_EQ + 20 * abs(math.sin(i / 60 * math.pi * scallops)) * 0.9 + 6)
            for i in range(61)]
    stroke_path(marg, 4, (255, 120, 225), 0.5)


def paint_oral_arms():
    for k in range(5):
        x0 = CX + (k - 2) * 34
        pts = []
        for i in range(41):
            t = i / 40
            y = 384 + 250 * t
            x = x0 + math.sin(t * 5.2 + k * 1.7) * (10 + 26 * t)
            pts.append((x, y))
        ribbon(pts, lambda t: 24 * (1 - t) + 5,
               lambda t: lerp3((255, 128, 168), (232, 84, 178), t),
               lambda t: 0.20)
        ribbon(pts, lambda t: 10 * (1 - t) + 2,
               lambda t: lerp3((255, 186, 128), (255, 138, 200), t),
               lambda t: 0.30)


def paint_sea_life():
    # reflection: a soft pool of light under the bell (no hard shapes)
    soft_ellipse(CX, HORIZON + 26, 310, 64, (30, 160, 190), 0.30)
    soft_ellipse(CX, HORIZON + 90, 200, 90, (24, 120, 160), 0.16)
    add_glow(CX, HORIZON + 60, 330, (0.05, 0.35, 0.42), 0.5)
    # shimmering light streaks on the water, hugging the glow column
    for _ in range(300):
        y = rng.uniform(HORIZON + 4, H - 8)
        depth = (y - HORIZON) / (H - HORIZON)
        spread = 250 * (0.30 + depth)
        x = CX + rng.uniform(-spread, spread)
        ln = rng.uniform(6, 16 + 52 * (1 - depth))
        a = rng.uniform(0.04, 0.20) * (1 - depth * 0.75)
        col = (120, 220, 245) if rng.random() < 0.8 else (230, 150, 235)
        xi, yi = int(x), int(y)
        for xx in range(xi, min(W - 1, xi + int(ln))):
            blend_px(xx, yi, col, a)
    # bioluminescent plankton
    for _ in range(210):
        x = rng.uniform(0, W)
        y = rng.uniform(HORIZON + 6, H - 4)
        blend_px(int(x), int(y), (110, 235, 220), rng.uniform(0.15, 0.6))
    # dark rock silhouettes in the lower corners
    fill_poly([(0, H), (0, 948), (70, 922), (150, 938), (205, 972), (230, H)],
              lambda y: (2, 5, 10), lambda y: 0.9)
    fill_poly([(W, H), (W, 958), (940, 930), (862, 944), (818, 978), (796, H)],
              lambda y: (2, 5, 10), lambda y: 0.9)
    # mist band softening the horizon
    soft_ellipse(CX, HORIZON, 520, 30, (120, 200, 220), 0.10)
    soft_ellipse(CX, HORIZON, 330, 16, (170, 230, 245), 0.12)
    # horizon light line
    for x in range(70, W - 70):
        a = 0.22 * (1 - abs(x - CX) / 480)
        if a > 0:
            blend_px(x, HORIZON - 1, (150, 230, 250), a)
            blend_px(x, HORIZON, (150, 230, 250), a * 0.7)


def composite():
    """Add the glow buffer and apply a vignette, one final pass."""
    for y in range(H):
        gy = y >> 1
        dy = (y - 512) / 512.0
        dy2 = dy * dy
        rowbase = y * W * 3
        gbase = gy * GW * 3
        for x in range(W):
            gx = x >> 1
            dx = (x - 512) / 512.0
            v = 1.0 - 0.34 * (dx * dx + dy2)
            gi = gbase + gx * 3
            i = rowbase + x * 3
            img[i] = clamp((img[i] + glow[gi] * 255) * v)
            img[i + 1] = clamp((img[i + 1] + glow[gi + 1] * 255) * v)
            img[i + 2] = clamp((img[i + 2] + glow[gi + 2] * 255) * v)


# ---------------------------------------------------------------- PNG out
def write_png(path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        raw += img[y * W * 3:(y + 1) * W * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n" +
           chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)) +
           chunk(b"IDAT", comp) +
           chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    paint_background()
    paint_stars()
    paint_tentacles()
    paint_oral_arms()
    paint_bell()
    paint_sea_life()
    composite()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    size = write_png(os.path.join(out_dir, "entry.png"))
    print("entry.png written:", size, "bytes")


if __name__ == "__main__":
    main()
