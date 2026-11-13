"""Menanam Cahaya (Planting Light).

A giant moon over flooded terraced rice paddies. The terraces mirror the
sky (Bhuana Agung / Bhuana Alit), and a line of tiny farmers plants
glowing golden seedlings -- starlight -- into the earth (gotong royong).

Flat ukiyo-e woodblock style. Pure Python stdlib. Deterministic.
Writes entry.png into $MAKEFUN_OUTPUT_DIR.
"""

import math
import os
import random
import struct
import zlib

W = H = 1024

# ---- palette: deep indigo, cream, gold, one red accent -------------------
INK = (8, 11, 24)
RIM = (10, 15, 34)
SKY_BANDS = [(13, 20, 44), (19, 29, 64), (25, 38, 82), (33, 49, 100)]
RIDGE = (15, 24, 54)
WATERS = [(41, 60, 110), (47, 67, 120), (54, 76, 130), (62, 86, 142)]
WATERS_LIGHT = [(58, 78, 128), (64, 85, 138), (71, 94, 148), (79, 104, 158)]
SKY_MIDS = [(16, 24, 54), (22, 33, 73), (29, 43, 91)]
CRATER = (226, 208, 168)
WATER_DARK = (30, 44, 86)
CREAM = (242, 227, 187)
CREAM_SOFT = (247, 236, 205)
CREAM_DIM = (206, 188, 146)
GOLD = (232, 178, 74)
GOLD_DEEP = (196, 146, 62)
GOLD_BRIGHT = (250, 208, 110)
PALE = (252, 244, 216)
RED = (190, 58, 44)

buf = bytearray(W * H * 3)
rng = random.Random(20261113)


# ---- primitives -----------------------------------------------------------
def hspan(y, x0, x1, c):
    if y < 0 or y >= H:
        return
    if x0 < 0:
        x0 = 0
    if x1 > W - 1:
        x1 = W - 1
    if x1 < x0:
        return
    i = (y * W + x0) * 3
    buf[i:i + (x1 - x0 + 1) * 3] = bytes(c) * (x1 - x0 + 1)


def rect(x0, y0, x1, y1, c):
    for y in range(max(0, y0), min(H - 1, y1) + 1):
        hspan(y, x0, x1, c)


def disc(cx, cy, r, c):
    r = int(r)
    for dy in range(-r, r + 1):
        hw = int(math.sqrt(max(0, r * r - dy * dy)))
        hspan(cy + dy, cx - hw, cx + hw, c)


def ellipse(cx, cy, rx, ry, c):
    for dy in range(-ry, ry + 1):
        t = 1.0 - (dy / ry) ** 2
        if t < 0:
            continue
        hw = int(rx * math.sqrt(t))
        hspan(cy + dy, cx - hw, cx + hw, c)


def fill_poly(pts, c):
    ys = [p[1] for p in pts]
    y0 = max(0, int(min(ys)))
    y1 = min(H - 1, int(max(ys)))
    n = len(pts)
    for y in range(y0, y1 + 1):
        nodes = []
        for i in range(n):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % n]
            if (ay <= y < by) or (by <= y < ay):
                nodes.append(ax + (y - ay) * (bx - ax) / (by - ay))
        nodes.sort()
        for k in range(0, len(nodes) - 1, 2):
            hspan(y, int(nodes[k]), int(nodes[k + 1]), c)


def thick_line(x0, y0, x1, y1, r, c):
    steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(steps + 1):
        t = i / steps
        disc(int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t), r, c)


def glow_diamond(cx, cy, r, core=PALE):
    """Flat layered diamond glow: dim halo -> gold -> bright -> hot core."""
    layers = [(r, GOLD_DEEP), (max(2, int(r * 0.66)), GOLD),
              (max(1, int(r * 0.4)), GOLD_BRIGHT), (max(1, int(r * 0.2)), core)]
    for rr, c in layers:
        if rr <= 0:
            continue
        for dy in range(-rr, rr + 1):
            hw = rr - abs(dy)
            hspan(cy + dy, cx - hw, cx + hw, c)


def blend_pixel(x, y, target, f):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        for k in range(3):
            buf[i + k] = int(buf[i + k] * (1 - f) + target[k] * f)


# ---- scene ----------------------------------------------------------------
def sky():
    edges = [0, 150, 300, 450, 612]
    for i, c in enumerate(SKY_BANDS):
        rect(0, edges[i], W - 1, edges[i + 1] - 1, c)
    for i, c in enumerate(SKY_MIDS):  # bokashi-style softened band edges
        rect(0, edges[i + 1] - 6, W - 1, edges[i + 1] + 5, c)


def stars():
    for _ in range(250):
        x = rng.randrange(6, W - 6)
        y = rng.randrange(6, 585)
        dx, dy = x - 512, y - 318
        if dx * dx + dy * dy < 252 * 252:
            continue
        c = (CREAM, CREAM_DIM, GOLD_BRIGHT)[rng.randrange(3)]
        s = rng.randrange(1, 4)
        rect(x, y, x + s - 1, y + s - 1, c)
    for _ in range(16):  # sparkle stars: small plus signs
        x = rng.randrange(20, W - 20)
        y = rng.randrange(16, 560)
        dx, dy = x - 512, y - 318
        if dx * dx + dy * dy < 258 * 258:
            continue
        r = rng.choice((4, 5, 6))
        hspan(y, x - r, x + r, CREAM_SOFT)
        for d in range(-r, r + 1):
            blend_pixel(x, y + d, CREAM_SOFT, 0.9)


def moon():
    disc(512, 318, 240, INK)          # keyblock outline
    disc(512, 318, 236, GOLD_DEEP)    # gold rim
    disc(512, 318, 229, CREAM)        # face
    disc(498, 304, 196, CREAM_SOFT)   # soft inner light, flat offset
    craters = [(430, 250, 34, 20), (585, 268, 26, 16), (470, 392, 30, 17),
               (600, 372, 20, 12), (520, 210, 18, 11), (415, 330, 16, 10)]
    for cx, cy, rx, ry in craters:
        ellipse(cx, cy, rx, ry, CRATER)


def ridge():
    pts = []
    for x in range(0, W + 1, 32):
        y = 566 + int(16 * math.sin(x / W * math.pi * 1.7 + 0.6)) \
            + int(7 * math.sin(x / W * math.pi * 5.1))
        pts.append((x, y))
    pts += [(W, 640), (0, 640)]
    fill_poly(pts, RIDGE)


# terrace geometry
BAND_TOPS = [596, 678, 772, 884]
BAND_SAGS = [14, 20, 26, 32]
BAND_RIMS = [7, 8, 10, 12]


def top_y(b, x):
    return BAND_TOPS[b] + int(BAND_SAGS[b] * (1 - (2 * x / W - 1) ** 2))


def band_bottom(b, x):
    if b < 3:
        return top_y(b + 1, x)
    return H + 24


def terrace(b):
    top = [(x, top_y(b, x)) for x in range(0, W + 1, 16)]
    bot = [(x, band_bottom(b, x)) for x in range(W, -1, -16)]
    fill_poly(top + bot, WATERS[b])
    rim = [(x, top_y(b, x)) for x in range(0, W + 1, 16)]
    rim += [(x, top_y(b, x) + BAND_RIMS[b]) for x in range(W, -1, -16)]
    fill_poly(rim, RIM)
    off = BAND_RIMS[b] + 15  # inner contour line: gives the band structure
    con = [(x, top_y(b, x) + off) for x in range(0, W + 1, 16)]
    con += [(x, top_y(b, x) + off + 3) for x in range(W, -1, -16)]
    fill_poly(con, WATERS_LIGHT[b])
    # moon reflection: broken horizontal dashes in a column under the moon
    half = (130, 165, 205, 250)[b]
    y = top_y(b, 512) + BAND_RIMS[b] + 12
    yend = band_bottom(b, 512) - 10
    row = 0
    while y < yend:
        wob = rng.randrange(-14, 15)
        w = int(half * (0.45 + 0.5 * abs(math.sin(row * 1.7 + b))))
        c = (CREAM_DIM, GOLD_DEEP, CREAM_DIM, GOLD)[row % 4]
        hspan(y, 512 + wob - w // 2, 512 + wob + w // 2, c)
        hspan(y + 1, 512 + wob - w // 3, 512 + wob + w // 3, c)
        y += rng.choice((10, 12, 13))
        row += 1
    # sparse star sparkles on the water
    for _ in range(14):
        x = rng.randrange(10, W - 10)
        yy = top_y(b, x) + BAND_RIMS[b] + rng.randrange(8, 60)
        if yy < band_bottom(b, x) - 6:
            rect(x, yy, x + 2, yy, CREAM_DIM)


def draw_farmer(x, feet_y, s, sash, flip=1):
    """Chunky bent planting silhouette; local origin at feet, height ~64*s."""
    def P(points):
        return [(x + flip * int(px * s), feet_y + int(py * s)) for px, py in points]

    fill_poly(P([(-7, -24), (-1, -24), (-2, 0), (-9, 0)]), INK)          # back leg
    fill_poly(P([(0, -24), (7, -24), (14, -9), (11, 0), (5, 0), (6, -12)]), INK)
    fill_poly(P([(-9, -46), (6, -49), (14, -28), (4, -22), (-7, -27)]), INK)  # torso
    fill_poly(P([(-6, -39), (10, -41), (12, -34), (-4, -32)]), sash)     # sash
    disc(x + flip * int(4 * s), feet_y + int(-52 * s), max(3, int(5.5 * s)), INK)
    fill_poly(P([(-16, -53), (18, -55), (3, -69)]), INK)                 # caping hat
    fill_poly(P([(-12, -56), (14, -57), (11, -60), (-9, -59)]), GOLD)   # hat band
    thick_line(x + flip * int(11 * s), feet_y + int(-42 * s),
               x + flip * int(23 * s), feet_y + int(-15 * s), max(2, int(3 * s)), INK)
    thick_line(x - flip * int(8 * s), feet_y + int(-40 * s),
               x - flip * int(16 * s), feet_y + int(-26 * s), max(2, int(3 * s)), INK)
    # seedling bundle in the back hand: tiny gold diamonds
    bx, by = x - flip * int(19 * s), feet_y + int(-22 * s)
    glow_diamond(bx, by, max(3, int(4 * s)))
    glow_diamond(bx + flip * int(5 * s), by + int(4 * s), max(2, int(3 * s)))
    # the seedling being planted, glowing at the reaching hand
    glow_diamond(x + flip * int(25 * s), feet_y + int(-11 * s), max(4, int(6 * s)))


def farmers_and_seedlings():
    b = 2  # farmers work the third terrace
    # distant neighbours on the upper terraces: gotong royong at every level
    for bx, bs, bf in [(250, 0.52, 1), (764, 0.48, -1)]:
        draw_farmer(bx, top_y(1, bx) + BAND_RIMS[1] - 1, bs, GOLD, bf)
    xs = [168, 302, 436, 566, 700, 838]
    scales = [1.14, 1.05, 1.2, 1.08, 1.16, 1.03]
    flips = [1, 1, -1, 1, -1, 1]
    for x, s, f in zip(xs, scales, flips):
        feet = top_y(b, x) + BAND_RIMS[b] - 1
        ellipse(x, top_y(b, x) + 34, 17, 6, WATER_DARK)  # reflection smudge
        draw_farmer(x, feet, s, RED if x == 436 else GOLD, f)
    # row of freshly planted glowing seedlings in the water below the rim
    for gx in range(120, 940, 41):
        gy = top_y(b, gx) + 52 + int(6 * math.sin(gx / 90.0))
        glow_diamond(gx, gy, 5)
        hspan(gy + 9, gx - 6, gx + 6, GOLD_DEEP)       # reflection dash
        hspan(gy + 13, gx - 3, gx + 3, GOLD_DEEP)
    # a few older 'star-flowers' already grown in the front terrace
    for gx, gy, r in [(240, 946, 9), (512, 972, 11), (768, 950, 9), (640, 922, 7)]:
        glow_diamond(gx, gy, r)
        hspan(gy + r + 5, gx - r, gx + r, GOLD_DEEP)
        thick_line(gx, gy + r, gx, gy + r + 10, 2, GOLD_DEEP)


def grain():
    for _ in range(5200):
        x = rng.randrange(W)
        y = rng.randrange(H)
        if rng.random() < 0.5:
            blend_pixel(x, y, CREAM, 0.13)
        else:
            blend_pixel(x, y, INK, 0.13)
        if rng.random() < 0.22:
            blend_pixel(x + 1 if x < W - 1 else x, y, CREAM, 0.07)


def write_png(path):
    raw = bytearray()
    rowlen = W * 3
    for y in range(H):
        raw.append(0)
        raw += buf[y * rowlen:(y + 1) * rowlen]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        return (struct.pack(">I", len(data)) + typ + data
                + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)


def main():
    sky()
    stars()
    moon()
    ridge()
    for b in range(4):
        terrace(b)
    farmers_and_seedlings()
    grain()
    # The output directory is not guaranteed to exist (the grader points
    # MAKEFUN_OUTPUT_DIR at a fresh path), so create it before writing.
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    path = os.path.join(outdir, "entry.png")
    os.makedirs(outdir, exist_ok=True)
    write_png(path)
    print("entry.png written:", os.path.getsize(path), "bytes")


if __name__ == "__main__":
    main()
