"""Library of doodle elements (sun, earth, people, props, labels, stamps...).

Each element function has the signature ``fn(p, rng, t) -> (image, (ax, ay))``
where ``p`` is the element's parameter dict from the episode JSON, ``rng`` is a
seeded RNG (changes a few times per second for the line-boil effect), ``t`` is
seconds since the element appeared, and ``(ax, ay)`` is the anchor point in the
returned image that is placed at the element's ``x, y`` on the canvas.

Elements listed in ``ANIMATED`` depend on ``t`` and are re-rendered every frame;
all others are cached per boil-variant.
"""
from __future__ import annotations

import math

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from .draw import (BLUE, GREEN, INK, ORANGE, RED, SKIN, WHITE, YELLOW, arrow, blob_pts, curve, cutout,
                   ellipse, font, hand_text, hatch, line, rect, shape, star_pts, text_size)

ELEMENTS = {}
ANIMATED = set()
NO_CUTOUT = set()


def element(name, animated=False, cut=True):
    def deco(fn):
        ELEMENTS[name] = fn
        if animated:
            ANIMATED.add(name)
        if not cut:
            NO_CUTOUT.add(name)
        return fn
    return deco


def rgba(c, default):
    if c is None:
        return default
    if isinstance(c, str):
        c = c.lstrip("#")
        return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
    return tuple(c) if len(c) == 4 else tuple(c) + (255,)


def canvas(w, h):
    im = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


# --------------------------------------------------------------------------- #
# faces
# --------------------------------------------------------------------------- #
def face(d, cx, cy, s, mood, rng, ink=INK):
    """Draw a cartoon face of scale ``s`` (≈ face radius) centred at cx, cy."""
    ex = s * 0.38
    ey = cy - s * 0.15
    w = max(3, s * 0.06)
    if mood in ("angry", "evil"):
        for sx in (-1, 1):
            ellipse(d, cx + sx * ex, ey + s * 0.05, s * 0.15, s * 0.11, rng, fill=WHITE, w=w)
            ellipse(d, cx + sx * ex, ey + s * 0.08, s * 0.06, s * 0.06, rng, fill=RED if mood == "evil" else INK, w=0)
            line(d, [(cx + sx * (ex + s * 0.25), ey - s * 0.18), (cx + sx * s * 0.08, ey - s * 0.02)], rng, w * 1.4, ink)
        # toothy grin
        mx0, mx1, my = cx - s * 0.45, cx + s * 0.45, cy + s * 0.32
        pts = [(mx0, my - s * 0.05), (mx1, my - s * 0.05), (cx + s * 0.25, my + s * 0.22), (cx - s * 0.25, my + s * 0.22)]
        shape(d, pts, rng, fill=WHITE, w=w)
        for k in range(1, 5):
            x = mx0 + (mx1 - mx0) * k / 5
            line(d, [(x, my - s * 0.05), (x, my + s * 0.15)], rng, max(2, w * 0.6), ink)
    elif mood in ("scared", "shocked"):
        for sx in (-1, 1):
            ellipse(d, cx + sx * ex, ey, s * 0.17, s * 0.2, rng, fill=WHITE, w=w)
            ellipse(d, cx + sx * ex, ey + s * 0.03, s * 0.05, s * 0.05, rng, fill=INK, w=0)
            line(d, [(cx + sx * (ex - s * 0.15), ey - s * 0.32), (cx + sx * (ex + s * 0.15), ey - s * 0.42)], rng, w, ink)
        ellipse(d, cx, cy + s * 0.42, s * 0.16, s * 0.22, rng, fill=(120, 20, 30, 255), w=w)
        # sweat drop
        sx, sy = cx + s * 0.75, cy - s * 0.35
        shape(d, [(sx, sy - s * 0.18), (sx + s * 0.1, sy + s * 0.02), (sx, sy + s * 0.1), (sx - s * 0.1, sy + s * 0.02)],
              rng, fill=(140, 200, 255, 255), w=max(2, w * 0.6))
    elif mood == "smug":
        for sx in (-1, 1):
            line(d, [(cx + sx * ex - s * 0.13, ey), (cx + sx * ex + s * 0.13, ey)], rng, w * 1.2, ink)
            line(d, [(cx + sx * ex - s * 0.15, ey - s * 0.2), (cx + sx * ex + s * 0.12, ey - s * 0.25)], rng, w, ink)
        line(d, [(cx - s * 0.3, cy + s * 0.35), (cx + s * 0.1, cy + s * 0.42), (cx + s * 0.38, cy + s * 0.25)], rng, w, ink)
    elif mood == "sleepy":
        for sx in (-1, 1):
            line(d, [(cx + sx * ex - s * 0.13, ey + s * 0.02), (cx + sx * ex, ey + s * 0.08), (cx + sx * ex + s * 0.13, ey + s * 0.02)], rng, w, ink)
        ellipse(d, cx, cy + s * 0.4, s * 0.12, s * 0.08, rng, fill=(120, 20, 30, 255), w=w)
    else:  # happy / neutral
        for sx in (-1, 1):
            ellipse(d, cx + sx * ex, ey, s * 0.1, s * 0.12, rng, fill=INK, w=0)
        if mood == "happy":
            line(d, [(cx - s * 0.38, cy + s * 0.25), (cx, cy + s * 0.5), (cx + s * 0.38, cy + s * 0.25)], rng, w, ink)
        else:
            line(d, [(cx - s * 0.3, cy + s * 0.38), (cx + s * 0.3, cy + s * 0.36)], rng, w, ink)


# --------------------------------------------------------------------------- #
# space objects
# --------------------------------------------------------------------------- #
@element("sun")
def el_sun(p, rng, t):
    s = p.get("size", 520)
    pad = int(s * 0.42)
    W = s + 2 * pad
    im, d = canvas(W, W)
    c, r = W / 2, s / 2
    n = p.get("rays", 13)
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.04, 0.04)
        L = r * (1.42 + rng.uniform(-0.1, 0.1))
        pts = [(c + r * 0.85 * math.cos(a - 0.17), c + r * 0.85 * math.sin(a - 0.17)),
               (c + L * math.cos(a), c + L * math.sin(a)),
               (c + r * 0.85 * math.cos(a + 0.17), c + r * 0.85 * math.sin(a + 0.17))]
        shape(d, pts, rng, fill=ORANGE, w=5)
    body = Image.new("L", im.size, 0)
    ImageDraw.Draw(body).polygon(blob_pts(c, c, r, r, rng, 0.03), fill=255)
    ellipse(d, c, c, r, r, rng, fill=(255, 206, 46, 255), w=8, wob=0.03)
    # orange shading crescent + hatching
    shade, sd = canvas(W, W)
    sd.ellipse([c - r * 0.75, c - r * 0.75, c + r * 1.3, c + r * 1.3], fill=(255, 140, 20, 150))
    shade.putalpha(ImageChops.multiply(shade.getchannel("A"), body))
    im.alpha_composite(shade)
    face(d, c, c, r * 0.8, p.get("mood", "angry"), rng)
    if p.get("hot", False):
        hatch(im, body, rng, col=(200, 40, 0, 70), gap=22)
    return im, (c, c)


@element("earth")
def el_earth(p, rng, t):
    s = p.get("size", 420)
    pad = 20
    W = s + 2 * pad
    im, d = canvas(W, W)
    c, r = W / 2, s / 2
    body = Image.new("L", im.size, 0)
    ImageDraw.Draw(body).ellipse([c - r, c - r, c + r, c + r], fill=255)
    d.ellipse([c - r, c - r, c + r, c + r], fill=BLUE)
    land, ld = canvas(W, W)
    lr = __import__("random").Random(p.get("seed", 7))  # continents stay put; only outlines boil
    for _ in range(6):
        lx, ly = c + lr.uniform(-r, r) * 0.8, c + lr.uniform(-r, r) * 0.8
        shape(ld, blob_pts(lx, ly, r * lr.uniform(0.18, 0.38), r * lr.uniform(0.15, 0.3), rng, 0.25), rng,
              fill=GREEN, outline=(30, 90, 30, 255), w=4)
    land.putalpha(ImageChops.multiply(land.getchannel("A"), body))
    im.alpha_composite(land)
    shade, sd = canvas(W, W)
    sd.ellipse([c - r * 0.6, c - r * 0.6, c + r * 1.5, c + r * 1.5], fill=(0, 0, 40, 90))
    shade.putalpha(ImageChops.multiply(shade.getchannel("A"), body))
    im.alpha_composite(shade)
    d2 = ImageDraw.Draw(im)
    ellipse(d2, c, c, r, r, rng, outline=INK, w=8, wob=0.015)
    if p.get("mood"):
        face(d2, c, c + r * 0.05, r * 0.6, p["mood"], rng)
    return im, (c, c)


@element("moon")
def el_moon(p, rng, t):
    s = p.get("size", 260)
    W = s + 40
    im, d = canvas(W, W)
    c, r = W / 2, s / 2
    ellipse(d, c, c, r, r, rng, fill=(200, 200, 205, 255), w=7)
    for _ in range(5):
        ellipse(d, c + rng.uniform(-r, r) * 0.55, c + rng.uniform(-r, r) * 0.55, r * 0.14, r * 0.12, rng,
                fill=(160, 160, 168, 255), w=3)
    if p.get("mood"):
        face(d, c, c, r * 0.6, p["mood"], rng)
    return im, (c, c)


@element("planet")
def el_planet(p, rng, t):
    s = p.get("size", 300)
    W, H = s * 1.9, s * 1.2
    im, d = canvas(W, H)
    cx, cy, r = W / 2, H / 2, s / 2
    col = rgba(p.get("color"), (200, 120, 70, 255))
    ellipse(d, cx, cy, r * 1.8, r * 0.45, rng, outline=(230, 200, 140, 255), w=10, wob=0.01)
    ellipse(d, cx, cy, r, r, rng, fill=col, w=7)
    if p.get("mood"):
        face(d, cx, cy, r * 0.6, p["mood"], rng)
    return im, (cx, cy)


@element("comet")
def el_comet(p, rng, t):
    s = p.get("size", 300)
    W, H = s * 2.4, s
    im, d = canvas(W, H)
    hx, hy, r = W - s * 0.5, H / 2, s * 0.32
    for k, col in enumerate([(255, 120, 20, 200), (255, 200, 40, 220), (255, 250, 200, 230)]):
        sc = 1 - k * 0.3
        pts = [(hx, hy - r * sc), (hx - W * 0.8 * sc, hy + rng.uniform(-8, 8)), (hx, hy + r * sc)]
        shape(d, pts, rng, fill=col, outline=None if k else INK, w=5)
    ellipse(d, hx, hy, r, r, rng, fill=(150, 140, 130, 255), w=7, wob=0.15)
    if p.get("mood"):
        face(d, hx, hy, r * 0.75, p["mood"], rng)
    return im, (hx, hy)


@element("asteroid")
def el_asteroid(p, rng, t):
    """Lumpy grey space rock with craters (optional face)."""
    s = p.get("size", 320)
    W = s * 1.25
    im, d = canvas(W, W)
    c, r = W / 2, s / 2
    import random as _r
    fr = _r.Random(p.get("seed", 4))  # shape stays put, outline boils
    body = Image.new("L", im.size, 0)
    pts = blob_pts(c, c, r, r * 0.82, fr, 0.22, rot=0.4)
    ImageDraw.Draw(body).polygon(pts, fill=255)
    shape(d, pts, rng, fill=(150, 140, 128, 255), w=7)
    for _ in range(6):
        cx_, cy_ = c + fr.uniform(-0.55, 0.55) * r, c + fr.uniform(-0.45, 0.45) * r
        rr = r * fr.uniform(0.08, 0.18)
        ellipse(d, cx_, cy_, rr, rr * 0.8, rng, fill=(115, 105, 95, 255), outline=(80, 72, 64, 255), w=4)
    shade, sd = canvas(W, W)
    sd.ellipse([c - r * 0.5, c - r * 0.5, c + r * 1.6, c + r * 1.6], fill=(20, 10, 30, 90))
    shade.putalpha(ImageChops.multiply(shade.getchannel("A"), body))
    im.alpha_composite(shade)
    if p.get("mood"):
        face(ImageDraw.Draw(im), c, c, r * 0.55, p["mood"], rng)
    return im, (c, c)


@element("eiffel")
def el_eiffel(p, rng, t):
    s = p.get("size", 700)
    W = s * 0.62
    im, d = canvas(W, s)
    cx = W / 2
    col = (120, 90, 60, 255)
    for sx in (-1, 1):
        line(d, [(cx + sx * W * 0.45, s * 0.98), (cx + sx * W * 0.2, s * 0.55), (cx + sx * W * 0.06, s * 0.2), (cx, s * 0.03)], rng, 9, col)
    for yy, ww in ((0.55, 0.22), (0.35, 0.12), (0.2, 0.07)):
        line(d, [(cx - W * ww, s * yy), (cx + W * ww, s * yy)], rng, 10, col)
    d.arc([cx - W * 0.3, s * 0.72, cx + W * 0.3, s * 1.1], 180, 360, fill=col, width=9)
    for k in range(8):  # lattice scribbles
        y0 = s * (0.58 + k * 0.05)
        line(d, [(cx - W * (0.2 + k * 0.03), y0), (cx + W * (0.2 + k * 0.03), y0 + s * 0.04)], rng, 3, col)
    return im, (cx, s / 2)


@element("ark")
def el_ark(p, rng, t):
    """Wooden ark / big boat with a cabin."""
    s = p.get("size", 700)
    W, H = s, s * 0.6
    im, d = canvas(W, H)
    wood, dark = (150, 95, 50, 255), (95, 60, 30, 255)
    hull = [(W * 0.02, H * 0.42), (W * 0.98, H * 0.42), (W * 0.86, H * 0.9), (W * 0.14, H * 0.9)]
    shape(d, hull, rng, fill=wood, w=7)
    for k in range(1, 4):
        y = H * (0.42 + 0.12 * k)
        line(d, [(W * (0.02 + 0.04 * k), y), (W * (0.98 - 0.04 * k), y)], rng, 4, dark)
    rect(d, W * 0.3, H * 0.14, W * 0.7, H * 0.42, rng, fill=(175, 120, 70, 255), w=6)
    shape(d, [(W * 0.26, H * 0.16), (W * 0.5, H * 0.02), (W * 0.74, H * 0.16)], rng, fill=dark, w=6)
    for x in (0.38, 0.5, 0.62):
        rect(d, W * x - W * 0.03, H * 0.22, W * x + W * 0.03, H * 0.3, rng, fill=(255, 220, 120, 255), w=3, skew=1)
    if p.get("mood"):
        face(d, W * 0.5, H * 0.66, H * 0.16, p["mood"], rng)
    return im, (W / 2, H / 2)


@element("drill")
def el_drill(p, rng, t):
    """Drilling rig (sondaj kulesi)."""
    s = p.get("size", 600)
    W = s * 0.7
    im, d = canvas(W, s)
    cx = W / 2
    col = (230, 160, 40, 255)
    for sx in (-1, 1):
        line(d, [(cx + sx * W * 0.35, s * 0.78), (cx + sx * W * 0.06, s * 0.05)], rng, 8, col)
    for k in range(5):
        y = s * (0.15 + k * 0.13)
        w_ = W * (0.08 + k * 0.055)
        line(d, [(cx - w_, y), (cx + w_, y + s * 0.06)], rng, 4, col)
        line(d, [(cx + w_, y), (cx - w_, y + s * 0.06)], rng, 4, col)
    rect(d, cx - W * 0.4, s * 0.76, cx + W * 0.4, s * 0.84, rng, fill=(90, 90, 100, 255), w=5)
    line(d, [(cx, s * 0.05), (cx, s * 0.98)], rng, 7, (60, 60, 70, 255))
    return im, (cx, s / 2)


@element("rain", animated=True, cut=False)
def el_rain(p, rng, t):
    """Full-screen animated rain streaks."""
    W, H = p.get("w", 1080), p.get("h", 1600)
    im, d = canvas(W, H)
    import random as _r
    pr = _r.Random(9)
    n = p.get("count", 90)
    sp = p.get("speed", 1500)
    for _ in range(n):
        x0, ph, L = pr.uniform(-100, W), pr.uniform(0, H), pr.uniform(40, 90)
        y = (ph + t * sp) % (H + 100) - 100
        x = x0 + (y * 0.18)
        d.line([(x, y), (x + L * 0.18, y + L)], fill=(170, 200, 255, 190), width=4)
    return im, (W / 2, H / 2)


@element("water", animated=True, cut=False)
def el_water(p, rng, t):
    """Wavy sea; its top sits at the element's y. Animate rising with move."""
    W, H = 1300, p.get("h", 1400)
    im, d = canvas(W, H)
    amp = p.get("amp", 30)
    for k, col in enumerate([(30, 70, 160, 255), (40, 95, 190, 235), (70, 130, 220, 220)]):
        top = []
        for xi in range(0, W + 20, 20):
            y = 30 + k * 45 + amp * math.sin(xi * 0.012 + t * (1.6 + 0.5 * k) + k * 1.3)
            top.append((xi, y))
        shape(d, top + [(W, H), (0, H)], rng, fill=col, outline=INK if k == 0 else None, w=5, amp=1)
        if k == 2:  # foam
            for (x, y) in top[::5]:
                ellipse(d, x, y, 14, 7, rng, fill=WHITE, outline=None, w=0, wob=0.3)
    return im, (W / 2, 30)


@element("mountain")
def el_mountain(p, rng, t):
    s = p.get("size", 800)
    W, H = s * 1.3, s
    im, d = canvas(W, H)
    pts = [(0, H), (W * 0.32, H * 0.25), (W * 0.42, H * 0.3), (W * 0.52, H * 0.05), (W * 0.7, H * 0.4), (W, H)]
    shape(d, pts, rng, fill=(120, 110, 125, 255), w=7)
    if p.get("snow", True):
        shape(d, [(W * 0.43, H * 0.29), (W * 0.52, H * 0.05), (W * 0.62, H * 0.27), (W * 0.56, H * 0.22),
                  (W * 0.5, H * 0.28)], rng, fill=WHITE, w=5)
    return im, (W / 2, H / 2)


@element("animal")
def el_animal(p, rng, t):
    """Doodle animals: lion|elephant|giraffe|sheep|dove|cat."""
    s = p.get("size", 300)
    kind = p.get("kind", "sheep")
    im, d = canvas(s * 1.4, s * 1.4)
    c = s * 0.7
    leg = (60, 50, 40, 255)
    def legs(x0, x1, y0, y1, col):
        for x in (x0, x0 + (x1 - x0) * 0.3, x0 + (x1 - x0) * 0.7, x1):
            line(d, [(x, y0), (x, y1)], rng, s * 0.06, col)
    if kind == "sheep":
        legs(c - s * 0.25, c + s * 0.25, c + s * 0.1, c + s * 0.4, INK)
        for k in range(7):
            a = 2 * math.pi * k / 7
            ellipse(d, c + s * 0.26 * math.cos(a), c + s * 0.15 * math.sin(a), s * 0.15, s * 0.13, rng, fill=WHITE, w=4)
        ellipse(d, c, c, s * 0.3, s * 0.18, rng, fill=WHITE, outline=None, w=0)
        ellipse(d, c + s * 0.38, c - s * 0.08, s * 0.12, s * 0.1, rng, fill=INK, w=3)
        ellipse(d, c + s * 0.41, c - s * 0.1, s * 0.02, s * 0.02, rng, fill=WHITE, w=0)
    elif kind == "lion":
        legs(c - s * 0.3, c + s * 0.2, c + s * 0.05, c + s * 0.4, (200, 150, 60, 255))
        ellipse(d, c - s * 0.05, c, s * 0.35, s * 0.18, rng, fill=(230, 170, 70, 255), w=5)
        line(d, [(c - s * 0.38, c), (c - s * 0.55, c - s * 0.15)], rng, 5, INK)
        shape(d, blob_pts(c + s * 0.3, c - s * 0.12, s * 0.22, s * 0.22, rng, 0.25), rng, fill=(170, 90, 30, 255), w=5)
        ellipse(d, c + s * 0.32, c - s * 0.1, s * 0.13, s * 0.13, rng, fill=(240, 190, 90, 255), w=4)
        face(d, c + s * 0.32, c - s * 0.1, s * 0.1, p.get("mood", "happy"), rng)
    elif kind == "elephant":
        legs(c - s * 0.3, c + s * 0.2, c + s * 0.05, c + s * 0.42, (130, 130, 145, 255))
        ellipse(d, c - s * 0.05, c - s * 0.02, s * 0.38, s * 0.24, rng, fill=(150, 150, 165, 255), w=5)
        ellipse(d, c + s * 0.32, c - s * 0.15, s * 0.18, s * 0.17, rng, fill=(150, 150, 165, 255), w=5)
        ellipse(d, c + s * 0.22, c - s * 0.12, s * 0.12, s * 0.16, rng, fill=(170, 170, 185, 255), w=4)
        line(d, [(c + s * 0.45, c - s * 0.1), (c + s * 0.52, c + s * 0.1), (c + s * 0.6, c + s * 0.15)], rng, s * 0.07, (150, 150, 165, 255))
        ellipse(d, c + s * 0.36, c - s * 0.2, s * 0.025, s * 0.03, rng, fill=INK, w=0)
    elif kind == "giraffe":
        legs(c - s * 0.25, c + s * 0.15, c + s * 0.05, c + s * 0.5, (220, 170, 60, 255))
        ellipse(d, c - s * 0.05, c, s * 0.28, s * 0.14, rng, fill=(240, 190, 70, 255), w=5)
        line(d, [(c + s * 0.15, c - s * 0.05), (c + s * 0.3, c - s * 0.55)], rng, s * 0.08, (240, 190, 70, 255))
        ellipse(d, c + s * 0.35, c - s * 0.58, s * 0.1, s * 0.07, rng, fill=(240, 190, 70, 255), w=4)
        for _ in range(5):
            ellipse(d, c + rng.uniform(-0.25, 0.15) * s, c + rng.uniform(-0.08, 0.08) * s, s * 0.04, s * 0.035, rng,
                    fill=(150, 90, 30, 255), w=0)
        ellipse(d, c + s * 0.37, c - s * 0.6, s * 0.015, s * 0.015, rng, fill=INK, w=0)
    elif kind == "dove":
        ellipse(d, c, c, s * 0.28, s * 0.16, rng, fill=WHITE, w=5)
        ellipse(d, c + s * 0.27, c - s * 0.1, s * 0.11, s * 0.1, rng, fill=WHITE, w=5)
        shape(d, [(c - s * 0.05, c - s * 0.05), (c - s * 0.3, c - s * 0.45), (c + s * 0.12, c - s * 0.08)], rng, fill=(235, 235, 240, 255), w=5)
        shape(d, [(c + s * 0.37, c - s * 0.11), (c + s * 0.47, c - s * 0.07), (c + s * 0.37, c - s * 0.05)], rng, fill=ORANGE, w=3)
        ellipse(d, c + s * 0.3, c - s * 0.13, s * 0.02, s * 0.02, rng, fill=INK, w=0)
        if p.get("branch", True):
            line(d, [(c + s * 0.45, c - s * 0.07), (c + s * 0.62, c + s * 0.05)], rng, 4, (90, 60, 30, 255))
            for k in range(3):
                ellipse(d, c + s * (0.5 + k * 0.05), c - s * 0.03 + k * s * 0.04, s * 0.04, s * 0.02, rng, fill=GREEN, w=2)
    if p.get("flip"):
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return im, (c, c)


@element("hammer")
def el_hammer(p, rng, t):
    s = p.get("size", 260)
    im, d = canvas(s, s)
    line(d, [(s * 0.3, s * 0.85), (s * 0.62, s * 0.32)], rng, s * 0.07, (150, 100, 50, 255))
    rect(d, s * 0.45, s * 0.12, s * 0.85, s * 0.32, rng, fill=(120, 120, 130, 255), w=5)
    return im, (s / 2, s / 2)


@element("planks")
def el_planks(p, rng, t):
    s = p.get("size", 400)
    im, d = canvas(s, s * 0.6)
    for k in range(4):
        y = s * 0.12 + k * s * 0.11
        rect(d, s * 0.05 + k * 8, y, s * 0.95 - k * 8, y + s * 0.08, rng, fill=(170, 115, 60, 255), w=4, skew=3)
    return im, (s / 2, s * 0.3)


@element("light", cut=False)
def el_light(p, rng, t):
    """Respectful representation of a prophet: a soft glowing light (no face)."""
    s = p.get("size", 360)
    im, d = canvas(s * 1.4, s * 1.4)
    c = s * 0.7
    for k in range(6, 0, -1):
        r = s * 0.1 * k
        d.ellipse([c - r, c - r, c + r, c + r], fill=(255, 240, 180, int(35 + 20 * (6 - k))))
    shape(d, star_pts(c, c, s * 0.62, s * 0.2, 8, rng, 0.2, 0.15), rng, fill=(255, 245, 200, 120), outline=None, w=0)
    im = im.filter(ImageFilter.GaussianBlur(6))
    d = ImageDraw.Draw(im)
    ellipse(d, c, c, s * 0.16, s * 0.16, rng, fill=(255, 252, 230, 255), outline=None, w=0)
    return im, (c, c)


@element("blackhole")
def el_blackhole(p, rng, t):
    s = p.get("size", 500)
    W = s * 1.5
    im, d = canvas(W, W)
    c = W / 2
    for k in range(5):
        rr = s * (0.7 - k * 0.08)
        ellipse(d, c, c, rr, rr * 0.35, rng, outline=(255, 150 + k * 20, 40, 255), w=12 - k, wob=0.05)
    ellipse(d, c, c, s * 0.28, s * 0.28, rng, fill=(5, 5, 10, 255), outline=(255, 220, 120, 255), w=6)
    if p.get("mood"):
        face(d, c, c, s * 0.2, p["mood"], rng, ink=(255, 230, 150, 255))
    return im, (c, c)


@element("stream", animated=True, cut=False)
def el_stream(p, rng, t):
    """Particles flying from (x0,y0) to (x1,y1). Coordinates are canvas coords."""
    x0, y0, x1, y1 = p["from"] + p["to"]
    pad = 80
    minx, miny = min(x0, x1) - pad, min(y0, y1) - pad
    W, H = abs(x1 - x0) + 2 * pad, abs(y1 - y0) + 2 * pad
    im, d = canvas(W, H)
    n = p.get("count", 14)
    speed = p.get("speed", 0.9)
    col = rgba(p.get("color"), (255, 170, 40, 255))
    import random as _r
    pr = _r.Random(3)
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    for i in range(n):
        ph = pr.random()
        u = (ph + t * speed) % 1.0
        off = pr.uniform(-1, 1) * p.get("spread", 60)
        px = x0 + (x1 - x0) * u - uy * off - minx
        py = y0 + (y1 - y0) * u + ux * off - miny
        rr = pr.uniform(9, 18)
        line(d, [(px - ux * rr * 4, py - uy * rr * 4), (px, py)], rng, rr * 0.8, (255, 230, 120, 160), amp=0.5)
        ellipse(d, px, py, rr, rr, rng, fill=col, w=3, wob=0.2)
        if p.get("letter"):
            d.text((px, py), p["letter"], font=font(int(rr * 1.6)), fill=INK, anchor="mm")
    return im, (-minx, -miny)


@element("aurora", animated=True, cut=False)
def el_aurora(p, rng, t):
    W, H = p.get("w", 1080), p.get("h", 700)
    sw, sh = W // 3, H // 3
    im, d = canvas(sw, sh)
    cols = [(60, 255, 140), (120, 255, 200), (230, 90, 220), (80, 200, 255)]
    for k in range(4):
        col = cols[k % len(cols)]
        top = []
        for xi in range(0, sw + 6, 6):
            y = sh * (0.25 + 0.1 * k) + 18 * math.sin(xi * 0.025 + t * (0.8 + 0.3 * k) + k) + 8 * math.sin(xi * 0.07 - t * 1.3)
            top.append((xi, y))
        poly = top + [(sw, sh * (0.75 + 0.05 * k)), (0, sh * (0.75 + 0.05 * k))]
        d.polygon(poly, fill=col + (85,))
        d.line(top, fill=col + (200,), width=3)
    im = im.filter(ImageFilter.GaussianBlur(4)).resize((W, H))
    return im, (W / 2, H / 2)


# --------------------------------------------------------------------------- #
# people
# --------------------------------------------------------------------------- #
@element("person")
def el_person(p, rng, t):
    """A doodle person. kind: scientist|miner|operator|kid|agent|caveman|king|plain."""
    s = p.get("size", 700)
    kind = p.get("kind", "plain")
    W, H = s * 1.5, s * 1.12
    im, d = canvas(W, H)
    cx = W / 2
    top = s * 0.1
    hr = s * 0.13
    hy = top + hr + s * 0.04
    coat = rgba(p.get("coat"), {"scientist": (90, 70, 60), "miner": (70, 90, 140), "operator": (60, 60, 70),
                                  "agent": (30, 30, 36), "caveman": (150, 100, 50), "king": (160, 30, 60),
                                  "kid": (220, 80, 80)}.get(kind, (80, 110, 160)), )
    sh_y = hy + hr + s * 0.05
    hip_y = s * 0.72
    # legs
    for sx in (-1, 1):
        line(d, [(cx + sx * s * 0.08, hip_y - 10), (cx + sx * s * 0.11, s * 1.0)], rng, s * 0.07, (50, 50, 70, 255))
        ellipse(d, cx + sx * s * 0.15, s * 1.02, s * 0.08, s * 0.035, rng, fill=INK, w=0)
    # body
    body = [(cx - s * 0.17, sh_y), (cx + s * 0.17, sh_y), (cx + s * 0.2, hip_y), (cx - s * 0.2, hip_y)]
    shape(d, body, rng, fill=coat, w=6)
    if kind == "scientist":
        shape(d, [(cx - s * 0.05, sh_y), (cx + s * 0.05, sh_y), (cx, sh_y + s * 0.15)], rng, fill=WHITE, w=4)
    if kind == "agent":
        shape(d, [(cx - s * 0.02, sh_y), (cx + s * 0.02, sh_y), (cx, sh_y + s * 0.2)], rng, fill=RED, w=3)
    # arms
    pose = p.get("pose", "point")
    lsh, rsh = (cx - s * 0.17, sh_y + s * 0.03), (cx + s * 0.17, sh_y + s * 0.03)
    arm_w = s * 0.06
    if pose == "point":
        hands = [(cx - s * 0.25, hip_y - s * 0.02), (cx + s * 0.48, sh_y - s * 0.05)]
    elif pose == "up":
        hands = [(cx - s * 0.38, top), (cx + s * 0.38, top)]
    elif pose == "hold":
        hands = [(cx - s * 0.2, hip_y - s * 0.12), (cx + s * 0.36, sh_y + s * 0.12)]
    else:  # down
        hands = [(cx - s * 0.24, hip_y), (cx + s * 0.24, hip_y)]
    for shp, hnd in ((lsh, hands[0]), (rsh, hands[1])):
        mid = ((shp[0] + hnd[0]) / 2 + rng.uniform(-6, 6), (shp[1] + hnd[1]) / 2 + s * 0.03)
        line(d, [shp, mid, hnd], rng, arm_w, coat)
        ellipse(d, hnd[0], hnd[1], s * 0.04, s * 0.04, rng, fill=SKIN, w=4)
    prop = p.get("prop")
    hx, hy2 = hands[1]
    if prop == "pan":
        line(d, [(hx, hy2), (hx + s * 0.14, hy2 - s * 0.02)], rng, s * 0.025, INK)
        ellipse(d, hx + s * 0.25, hy2 - s * 0.03, s * 0.12, s * 0.045, rng, fill=(60, 60, 60, 255), w=4)
        ellipse(d, hx + s * 0.25, hy2 - s * 0.05, s * 0.06, s * 0.02, rng, fill=WHITE, w=2)
        ellipse(d, hx + s * 0.25, hy2 - s * 0.055, s * 0.02, s * 0.012, rng, fill=YELLOW, w=0)
    elif prop == "sign":
        line(d, [(hx, hy2 + s * 0.1), (hx, hy2 - s * 0.35)], rng, s * 0.02, (120, 80, 40, 255))
        rect(d, hx - s * 0.2, hy2 - s * 0.55, hx + s * 0.2, hy2 - s * 0.33, rng, fill=WHITE, w=5)
        hand_text(d, (hx, hy2 - s * 0.44), p.get("sign_text", "SON!"), int(s * 0.1), rng, fill=RED)
    elif prop == "phone":
        rect(d, hx - s * 0.03, hy2 - s * 0.1, hx + s * 0.05, hy2 + s * 0.02, rng, fill=INK, w=3)
    elif prop == "key":
        line(d, [(hx, hy2), (hx + s * 0.12, hy2)], rng, s * 0.02, YELLOW)
        ellipse(d, hx + s * 0.14, hy2, s * 0.035, s * 0.035, rng, outline=YELLOW, w=6)
    # neck + head
    line(d, [(cx, hy + hr * 0.8), (cx, sh_y + 4)], rng, s * 0.06, SKIN)
    ellipse(d, cx, hy, hr * 0.92, hr, rng, fill=SKIN, w=6)
    if kind == "scientist":  # big beard + top hat
        shape(d, blob_pts(cx, hy + hr * 0.75, hr * 0.85, hr * 0.55, rng, 0.15), rng, fill=(110, 80, 50, 255), w=5)
        rect(d, cx - hr * 0.75, hy - hr * 2.2, cx + hr * 0.75, hy - hr * 0.8, rng, fill=INK, w=4, skew=3)
        rect(d, cx - hr * 1.2, hy - hr * 0.95, cx + hr * 1.2, hy - hr * 0.75, rng, fill=INK, w=4, skew=2)
    elif kind == "miner":
        shape(d, [(cx - hr * 1.05, hy - hr * 0.3), (cx - hr * 0.8, hy - hr * 1.1), (cx + hr * 0.8, hy - hr * 1.1),
                  (cx + hr * 1.05, hy - hr * 0.3)], rng, fill=YELLOW, w=5)
        ellipse(d, cx, hy - hr * 0.8, hr * 0.2, hr * 0.18, rng, fill=WHITE, w=4)
        shape(d, blob_pts(cx, hy + hr * 0.5, hr * 0.6, hr * 0.25, rng, 0.2), rng, fill=(60, 40, 30, 255), w=0)
    elif kind == "operator":
        ellipse(d, cx, hy - hr * 0.75, hr * 0.95, hr * 0.35, rng, fill=(40, 60, 110, 255), w=5)
        rect(d, cx - hr * 0.2, hy - hr * 0.75, cx + hr * 1.3, hy - hr * 0.55, rng, fill=INK, w=3, skew=2)
    elif kind == "agent":
        rect(d, cx - hr * 0.75, hy - hr * 0.35, cx - hr * 0.05, hy - hr * 0.05, rng, fill=INK, w=3, skew=1)
        rect(d, cx + hr * 0.05, hy - hr * 0.35, cx + hr * 0.75, hy - hr * 0.05, rng, fill=INK, w=3, skew=1)
        shape(d, blob_pts(cx, hy - hr * 0.85, hr * 0.9, hr * 0.3, rng, 0.1), rng, fill=INK, w=0)
    elif kind == "caveman":
        shape(d, blob_pts(cx, hy - hr * 0.6, hr * 1.0, hr * 0.55, rng, 0.3), rng, fill=(70, 40, 20, 255), w=4)
        shape(d, blob_pts(cx, hy + hr * 0.6, hr * 0.8, hr * 0.5, rng, 0.25), rng, fill=(70, 40, 20, 255), w=4)
    elif kind == "king":
        shape(d, [(cx - hr * 0.8, hy - hr * 0.7), (cx - hr * 0.8, hy - hr * 1.5), (cx - hr * 0.4, hy - hr * 1.1),
                  (cx, hy - hr * 1.7), (cx + hr * 0.4, hy - hr * 1.1), (cx + hr * 0.8, hy - hr * 1.5),
                  (cx + hr * 0.8, hy - hr * 0.7)], rng, fill=YELLOW, w=5)
    elif kind == "kid":
        shape(d, blob_pts(cx, hy - hr * 0.7, hr * 0.9, hr * 0.35, rng, 0.2), rng, fill=(200, 140, 60, 255), w=4)
    if kind != "agent":
        face(d, cx, hy + hr * 0.1 if kind != "scientist" else hy - hr * 0.05, hr * 0.7, p.get("mood", "neutral"), rng)
    else:
        line(d, [(cx - hr * 0.3, hy + hr * 0.45), (cx + hr * 0.3, hy + hr * 0.45)], rng, 5, INK)
    if p.get("flip"):
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return im, (W / 2, H * 0.55)


# --------------------------------------------------------------------------- #
# props
# --------------------------------------------------------------------------- #
@element("telescope")
def el_telescope(p, rng, t):
    s = p.get("size", 500)
    im, d = canvas(s, s)
    bx, by = s * 0.45, s * 0.6
    for ex in (s * 0.2, s * 0.45, s * 0.7):
        line(d, [(bx, by), (ex, s * 0.97)], rng, s * 0.025, (120, 80, 40, 255))
    ang = math.radians(-35)
    L = s * 0.7
    ux, uy = math.cos(ang), math.sin(ang)
    nx, ny = -uy, ux
    x0, y0 = bx - ux * L * 0.35, by - uy * L * 0.35
    x1, y1 = bx + ux * L * 0.65, by + uy * L * 0.65
    r0, r1 = s * 0.05, s * 0.09
    shape(d, [(x0 + nx * r0, y0 + ny * r0), (x1 + nx * r1, y1 + ny * r1), (x1 - nx * r1, y1 - ny * r1),
              (x0 - nx * r0, y0 - ny * r0)], rng, fill=(200, 160, 60, 255), w=6)
    ellipse(d, x1, y1, r1 * 0.5, r1, rng, fill=(150, 210, 255, 255), w=5)
    return im, (s / 2, s / 2)


@element("pole")
def el_pole(p, rng, t):
    s = p.get("size", 900)
    W = s * 0.9
    im, d = canvas(W, s)
    cx = W / 2
    line(d, [(cx, s * 0.05), (cx, s)], rng, s * 0.04, (120, 80, 40, 255))
    for yy in (s * 0.12, s * 0.22):
        line(d, [(cx - W * 0.3, yy), (cx + W * 0.3, yy)], rng, s * 0.025, (120, 80, 40, 255))
        for xx in (cx - W * 0.25, cx - W * 0.1, cx + W * 0.1, cx + W * 0.25):
            ellipse(d, xx, yy - s * 0.02, s * 0.012, s * 0.02, rng, fill=(120, 200, 120, 255), w=3)
            curve(d, (xx, yy - s * 0.03), (0 if xx < cx else W, yy + s * 0.05), s * 0.06, rng, w=3, col=INK)
    return im, (cx, s / 2)


@element("spark")
def el_spark(p, rng, t):
    s = p.get("size", 260)
    im, d = canvas(s * 1.4, s * 1.4)
    c = s * 0.7
    shape(d, star_pts(c, c, s * 0.62, s * 0.25, 10, rng, rng.uniform(0, 1), 0.3), rng, fill=YELLOW, w=6)
    shape(d, star_pts(c, c, s * 0.32, s * 0.14, 8, rng, rng.uniform(0, 1), 0.3), rng, fill=WHITE, w=0)
    if p.get("text"):
        hand_text(d, (c, c), p["text"], int(s * 0.24), rng, fill=RED, stroke=3, stroke_fill=INK)
    return im, (c, c)


@element("burst")
def el_burst(p, rng, t):
    """Comic-book explosion with text (BOOM!, ÇÖKTÜ! ...)."""
    s = p.get("size", 520)
    im, d = canvas(s * 1.3, s * 1.0)
    cx, cy = s * 0.65, s * 0.5
    pts = star_pts(cx, cy, s * 0.58, s * 0.36, 14, rng, 0, 0.18)
    pts = [(cx + (x - cx), cy + (y - cy) * 0.72) for x, y in pts]
    shape(d, pts, rng, fill=rgba(p.get("color"), RED), w=8)
    pts2 = [(cx + (x - cx) * 0.7, cy + (y - cy) * 0.7) for x, y in pts]
    shape(d, pts2, rng, fill=YELLOW, w=0)
    hand_text(d, (cx, cy), p.get("text", "BOOM!"), int(s * p.get("text_scale", 0.2)), rng, fill=INK)
    return im, (cx, cy)


@element("icon")
def el_icon(p, rng, t):
    """Small tech icons: satellite|gps|bulb|wifi|phone|card|plane|tower|skull|clock|book|bomb."""
    s = p.get("size", 220)
    what = p.get("what", "bulb")
    im, d = canvas(s * 1.3, s * 1.3)
    c = s * 0.65
    if what == "satellite":
        rect(d, c - s * 0.15, c - s * 0.15, c + s * 0.15, c + s * 0.15, rng, fill=(200, 200, 210, 255), w=5)
        for sx in (-1, 1):
            x0 = c + sx * s * 0.2
            x1 = c + sx * s * 0.6
            rect(d, min(x0, x1), c - s * 0.12, max(x0, x1), c + s * 0.12, rng, fill=(40, 70, 170, 255), w=5)
            for k in range(1, 3):
                xx = x0 + (x1 - x0) * k / 3
                line(d, [(xx, c - s * 0.12), (xx, c + s * 0.12)], rng, 2, WHITE)
        line(d, [(c, c - s * 0.15), (c, c - s * 0.35)], rng, 4, INK)
        ellipse(d, c, c - s * 0.38, s * 0.04, s * 0.04, rng, fill=RED, w=3)
    elif what == "gps":
        shape(d, [(c, c + s * 0.5)] + [(c + s * 0.3 * math.cos(a), c - s * 0.1 + s * 0.3 * math.sin(a))
                                       for a in [math.pi * (0.8 + i * 1.4 / 12) for i in range(13)]],
              rng, fill=RED, w=6)
        ellipse(d, c, c - s * 0.1, s * 0.11, s * 0.11, rng, fill=WHITE, w=4)
    elif what == "bulb":
        ellipse(d, c, c - s * 0.1, s * 0.3, s * 0.32, rng, fill=YELLOW, w=6)
        rect(d, c - s * 0.12, c + s * 0.2, c + s * 0.12, c + s * 0.38, rng, fill=(150, 150, 160, 255), w=5)
        line(d, [(c - s * 0.1, c), (c - s * 0.03, c - s * 0.12), (c + s * 0.04, c), (c + s * 0.1, c - s * 0.12)], rng, 4, ORANGE)
    elif what == "wifi":
        for k, rr in enumerate((0.5, 0.35, 0.2)):
            d.arc([c - s * rr, c - s * rr + s * 0.15, c + s * rr, c + s * rr + s * 0.15], 220, 320, fill=INK,
                  width=int(s * 0.06))
        ellipse(d, c, c + s * 0.22, s * 0.05, s * 0.05, rng, fill=INK, w=0)
    elif what == "phone":
        rect(d, c - s * 0.2, c - s * 0.38, c + s * 0.2, c + s * 0.38, rng, fill=INK, w=5)
        rect(d, c - s * 0.16, c - s * 0.31, c + s * 0.16, c + s * 0.28, rng, fill=(90, 160, 230, 255), w=0)
    elif what == "card":
        rect(d, c - s * 0.4, c - s * 0.25, c + s * 0.4, c + s * 0.25, rng, fill=(70, 140, 90, 255), w=5)
        rect(d, c - s * 0.3, c - s * 0.1, c - s * 0.1, c + s * 0.05, rng, fill=YELLOW, w=3)
    elif what == "plane":
        shape(d, [(c - s * 0.45, c), (c + s * 0.4, c - s * 0.05), (c + s * 0.48, c + s * 0.02), (c - s * 0.45, c + s * 0.08)],
              rng, fill=WHITE, w=5)
        shape(d, [(c - s * 0.05, c), (c + s * 0.1, c - s * 0.4), (c + s * 0.2, c - s * 0.4), (c + s * 0.12, c)], rng,
              fill=(200, 200, 210, 255), w=5)
    elif what == "tower":
        for sx in (-1, 1):
            line(d, [(c + sx * s * 0.3, c + s * 0.5), (c, c - s * 0.5)], rng, 6, (180, 180, 190, 255))
        for k in range(4):
            yy = c + s * 0.5 - k * s * 0.25
            w = s * 0.3 * (1 - k * 0.25)
            line(d, [(c - w, yy), (c + w, yy)], rng, 4, (180, 180, 190, 255))
    elif what == "skull":
        ellipse(d, c, c - s * 0.05, s * 0.35, s * 0.32, rng, fill=WHITE, w=6)
        rect(d, c - s * 0.18, c + s * 0.15, c + s * 0.18, c + s * 0.35, rng, fill=WHITE, w=5)
        for sx in (-1, 1):
            ellipse(d, c + sx * s * 0.14, c - s * 0.05, s * 0.09, s * 0.1, rng, fill=INK, w=0)
    elif what == "clock":
        ellipse(d, c, c, s * 0.42, s * 0.42, rng, fill=WHITE, w=7)
        line(d, [(c, c), (c, c - s * 0.3)], rng, 7, INK)
        line(d, [(c, c), (c + s * 0.2, c + s * 0.05)], rng, 7, INK)
    elif what == "book":
        rect(d, c - s * 0.4, c - s * 0.3, c + s * 0.4, c + s * 0.3, rng, fill=(130, 40, 40, 255), w=6)
        line(d, [(c, c - s * 0.3), (c, c + s * 0.3)], rng, 5, INK)
    elif what == "bomb":
        ellipse(d, c, c + s * 0.08, s * 0.33, s * 0.33, rng, fill=INK, w=4)
        line(d, [(c + s * 0.2, c - s * 0.2), (c + s * 0.35, c - s * 0.4)], rng, 6, (180, 140, 80, 255))
        shape(d, star_pts(c + s * 0.38, c - s * 0.45, s * 0.1, s * 0.04, 6, rng), rng, fill=YELLOW, w=0)
    return im, (c, c)


@element("calendar")
def el_calendar(p, rng, t):
    s = p.get("size", 420)
    W, H = s, s * 1.05
    im, d = canvas(W, H)
    rect(d, W * 0.06, H * 0.08, W * 0.94, H * 0.95, rng, fill=(245, 240, 225, 255), w=7)
    rect(d, W * 0.06, H * 0.08, W * 0.94, H * 0.3, rng, fill=RED, w=7)
    hand_text(d, (W / 2, H * 0.19), p.get("top", "EYLÜL"), int(s * 0.15), rng, fill=WHITE)
    hand_text(d, (W / 2, H * 0.6), p.get("text", "1859"), int(s * p.get("text_scale", 0.3)), rng, fill=INK)
    for xx in (W * 0.3, W * 0.7):
        rect(d, xx - 8, H * 0.02, xx + 8, H * 0.13, rng, fill=(150, 150, 160, 255), w=3, skew=1)
    return im, (W / 2, H / 2)


@element("frame")
def el_frame(p, rng, t):
    """A pinned paper note / evidence card with a few lines of handwriting."""
    lines = p.get("lines", ["KANIT #1"])
    s = p.get("size", 560)
    fs = int(p.get("font", s * 0.13))
    W = s
    H = fs * 1.2 * len(lines) + fs * 1.2
    im, d = canvas(W, H + 30)
    rect(d, 10, 30, W - 10, H + 20, rng, fill=rgba(p.get("paper"), (250, 236, 170, 255)), w=6)
    ellipse(d, W / 2, 34, 16, 16, rng, fill=RED, w=4)
    for i, ln in enumerate(lines):
        hand_text(d, (W / 2, 30 + fs * 1.1 + i * fs * 1.2), ln, fs, rng, fill=rgba(p.get("ink"), INK))
    return im, (W / 2, (H + 30) / 2)


@element("orbit", cut=False)
def el_orbit(p, rng, t):
    rx, ry = p.get("rx", 420), p.get("ry", 170)
    W, H = rx * 2 + 40, ry * 2 + 40
    im, d = canvas(W, H)
    cx, cy = W / 2, H / 2
    n = 60
    for i in range(0, n, 2):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        line(d, [(cx + rx * math.cos(a0), cy + ry * math.sin(a0)), (cx + rx * math.cos(a1), cy + ry * math.sin(a1))],
             rng, 5, (255, 255, 255, 200), amp=0.8)
    return im, (cx, cy)


@element("ground", cut=False)
def el_ground(p, rng, t):
    W, H = 1300, p.get("h", 520)
    im, d = canvas(W, H)
    shape(d, [(0, H * 0.35), (W * 0.18, H * 0.05), (W * 0.32, H * 0.3), (W * 0.5, 0), (W * 0.7, H * 0.28),
              (W * 0.85, H * 0.1), (W, H * 0.3), (W, H), (0, H)], rng, fill=(120, 120, 140, 255), w=6)
    shape(d, [(0, H * 0.55), (W * 0.3, H * 0.45), (W * 0.6, H * 0.52), (W, H * 0.42), (W, H), (0, H)], rng,
          fill=(80, 160, 70, 255), w=7)
    return im, (W / 2, 0)


@element("cross", cut=False)
def el_cross(p, rng, t):
    s = p.get("size", 300)
    im, d = canvas(s, s)
    for (a, b) in (((s * 0.1, s * 0.1), (s * 0.9, s * 0.9)), ((s * 0.9, s * 0.1), (s * 0.1, s * 0.9))):
        line(d, [a, b], rng, s * 0.09, RED, amp=4)
    return im, (s / 2, s / 2)


@element("check", cut=False)
def el_check(p, rng, t):
    s = p.get("size", 260)
    im, d = canvas(s, s)
    line(d, [(s * 0.1, s * 0.55), (s * 0.4, s * 0.85), (s * 0.92, s * 0.12)], rng, s * 0.1, (60, 220, 90, 255), amp=3)
    return im, (s / 2, s / 2)


# --------------------------------------------------------------------------- #
# typography
# --------------------------------------------------------------------------- #
@element("label", cut=False)
def el_label(p, rng, t):
    """Handwritten caption, optional underline and arrow (arrow = [dx, dy] to target)."""
    txt = p["text"]
    size = p.get("size", 90)
    col = rgba(p.get("color"), WHITE)
    tw, th = text_size(txt, size)
    ax_, ay_ = p.get("arrow", (0, 0)) if p.get("arrow") else (0, 0)
    pad = 40
    minx = min(-tw / 2, ax_) - pad
    maxx = max(tw / 2, ax_) + pad
    miny = min(-th, ay_) - pad
    maxy = max(th, ay_) + pad
    im, d = canvas(maxx - minx, maxy - miny)
    ox, oy = -minx, -miny
    hand_text(d, (ox, oy), txt, size, rng, fill=col, stroke=p.get("stroke", 0), stroke_fill=INK)
    if p.get("underline", False):
        line(d, [(ox - tw / 2, oy + th * 0.62), (ox + tw / 2, oy + th * 0.55)], rng, max(4, size * 0.06), col, amp=2)
    if p.get("arrow"):
        sx = ox + (tw / 2 + 10 if ax_ > tw / 2 else (-tw / 2 - 10 if ax_ < -tw / 2 else 0))
        sy = oy + (th * 0.7 if ay_ > 0 else -th * 0.6)
        arrow(d, (sx, sy), (ox + ax_, oy + ay_), rng, max(5, size * 0.07), col)
    return im, (ox, oy)


@element("bigtext", cut=False)
def el_bigtext(p, rng, t):
    lines = p["text"].split("\n")
    size = p.get("size", 150)
    col = rgba(p.get("color"), YELLOW)
    widths = [text_size(ln, size)[0] for ln in lines]
    W = max(widths) + 80
    H = size * 1.05 * len(lines) + 60
    im, d = canvas(W, H)
    for i, ln in enumerate(lines):
        hand_text(d, (W / 2, 30 + size * 0.55 + i * size * 1.05), ln, size, rng, fill=col,
                  stroke=int(size * 0.07), stroke_fill=INK, jit=0.04)
    return im, (W / 2, H / 2)


@element("stamp", cut=False)
def el_stamp(p, rng, t):
    txt = p.get("text", "GİZLİ!")
    size = p.get("size", 120)
    col = rgba(p.get("color"), RED)
    tw, th = text_size(txt, size)
    W, H = tw + size * 0.9, size * 1.6
    im, d = canvas(W + 20, H + 20)
    x0, y0, x1, y1 = 10 + size * 0.15, 10 + size * 0.15, W + 10 - size * 0.15, H + 10 - size * 0.15
    rect(d, x0, y0, x1, y1, rng, outline=col, w=size * 0.09, skew=3)
    rect(d, x0 + size * 0.14, y0 + size * 0.14, x1 - size * 0.14, y1 - size * 0.14, rng, outline=col, w=size * 0.04, skew=2)
    d.text(((W + 20) / 2, (H + 20) / 2), txt, font=font(size), fill=col, anchor="mm")
    # worn ink: punch random holes in the alpha
    holes = Image.new("L", im.size, 255)
    hd = ImageDraw.Draw(holes)
    for _ in range(int(W * H / 900)):
        x, y = rng.uniform(0, W + 20), rng.uniform(0, H + 20)
        r = rng.uniform(1, 5)
        hd.ellipse([x - r, y - r, x + r, y + r], fill=0)
    im.putalpha(ImageChops.multiply(im.getchannel("A"), holes))
    return im, ((W + 20) / 2, (H + 20) / 2)


def render_element(p, rng, t):
    kind = p["type"]
    fn = ELEMENTS[kind]
    im, (ax, ay) = fn(p, rng, t)
    if p.get("cutout", kind not in NO_CUTOUT):
        im, (dx, dy) = cutout(im, border=p.get("border", 9), rng=rng)
        ax, ay = ax + dx, ay + dy
    return im, (ax, ay)
