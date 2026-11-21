"""Hand-drawn ("MS Paint doodle + cut-out collage") drawing primitives.

Everything here is deliberately imperfect: lines wobble, circles are lumpy,
and each call takes an RNG so the same element can be redrawn with a slightly
different wobble every few frames ("line boil"), which gives the cheap
stop-motion feel of conspiracy-explainer animations.
"""
from __future__ import annotations

import math
import os
import random
from functools import lru_cache

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

INK = (22, 20, 26, 255)
WHITE = (250, 248, 240, 255)
YELLOW = (255, 214, 48, 255)
ORANGE = (255, 150, 30, 255)
RED = (220, 36, 36, 255)
BLUE = (60, 120, 220, 255)
GREEN = (70, 170, 70, 255)
SKIN = (240, 198, 160, 255)

FONT_DIR = os.path.join(os.path.dirname(__file__), "assets", "fonts")


@lru_cache(maxsize=64)
def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    name = "Caveat-700.ttf" if bold else "Caveat-400.ttf"
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


# --------------------------------------------------------------------------- #
# geometry helpers
# --------------------------------------------------------------------------- #
def jitter_pts(pts, rng: random.Random, amp: float, step: float = 16, closed: bool = False):
    """Subdivide a polyline and push each point sideways by a small random amount."""
    out = []
    n = len(pts)
    segs = n if closed else n - 1
    for i in range(segs):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        length = math.hypot(x1 - x0, y1 - y0)
        k = max(1, int(length / step))
        nx, ny = ((-(y1 - y0) / length, (x1 - x0) / length) if length else (0.0, 0.0))
        for j in range(k):
            t = j / k
            d = rng.uniform(-amp, amp) if (i or j) else 0
            out.append((x0 + (x1 - x0) * t + nx * d, y0 + (y1 - y0) * t + ny * d))
    if not closed:
        out.append(pts[-1])
    return out


def line(d: ImageDraw.ImageDraw, pts, rng, w=6, col=INK, amp=1.8):
    p = jitter_pts(pts, rng, amp)
    d.line(p, fill=col, width=int(w), joint="curve")
    r = w / 2
    for (x, y) in (p[0], p[-1]):
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)


def curve(d, p0, p1, sag, rng, w=4, col=INK, n=20):
    """A sagging wire / quadratic curve between two points."""
    (x0, y0), (x1, y1) = p0, p1
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2 + sag
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * mx + t * t * x1
        y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * my + t * t * y1
        pts.append((x, y))
    line(d, pts, rng, w, col, amp=1.0)


def blob_pts(cx, cy, rx, ry, rng, wob=0.035, n=56, rot=0.0):
    ph = [rng.uniform(0, 6.283) for _ in range(3)]
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = 1 + wob * (math.sin(2 * a + ph[0]) + 0.6 * math.sin(3 * a + ph[1]) + 0.4 * math.sin(5 * a + ph[2])) / 2
        r += rng.uniform(-wob, wob) * 0.25
        pts.append((cx + rx * r * math.cos(a + rot), cy + ry * r * math.sin(a + rot)))
    return pts


def shape(d, pts, rng, fill=None, outline=INK, w=6, amp=1.4):
    if fill is not None:
        d.polygon(pts, fill=fill)
    if outline is not None and w > 0:
        p = jitter_pts(pts, rng, amp, closed=True)
        p.append(p[0])
        d.line(p, fill=outline, width=int(w), joint="curve")


def ellipse(d, cx, cy, rx, ry, rng, fill=None, outline=INK, w=6, wob=0.035):
    shape(d, blob_pts(cx, cy, rx, ry, rng, wob), rng, fill, outline, w)


def rect(d, x0, y0, x1, y1, rng, fill=None, outline=INK, w=6, skew=4):
    j = lambda: rng.uniform(-skew, skew)  # noqa: E731
    pts = [(x0 + j(), y0 + j()), (x1 + j(), y0 + j()), (x1 + j(), y1 + j()), (x0 + j(), y1 + j())]
    shape(d, pts, rng, fill, outline, w)


def star_pts(cx, cy, r_out, r_in, n, rng, rot=0.0, jit=0.12):
    pts = []
    for i in range(2 * n):
        a = rot + math.pi * i / n
        r = (r_out if i % 2 == 0 else r_in) * (1 + rng.uniform(-jit, jit))
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def arrow(d, p0, p1, rng, w=6, col=WHITE, head=34):
    (x0, y0), (x1, y1) = p0, p1
    # slightly bent shaft
    mx = (x0 + x1) / 2 + rng.uniform(-15, 15)
    my = (y0 + y1) / 2 + rng.uniform(-15, 15)
    line(d, [(x0, y0), (mx, my), (x1, y1)], rng, w, col)
    a = math.atan2(y1 - my, x1 - mx)
    for s in (-1, 1):
        aa = a + math.pi - s * 0.45
        line(d, [(x1, y1), (x1 + head * math.cos(aa), y1 + head * math.sin(aa))], rng, w, col)


def hatch(im: Image.Image, mask: Image.Image, rng, col=(0, 0, 0, 60), gap=14, w=3, angle=-35):
    """Scribbly cross-hatching restricted to a mask (shading)."""
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    W, H = im.size
    diag = W + H
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    for k in range(-diag, diag, gap):
        cx, cy = W / 2 + k * -sa, H / 2 + k * ca
        p0 = (cx - diag * ca, cy - diag * sa)
        p1 = (cx + diag * ca, cy + diag * sa)
        d.line([p0, p1], fill=col, width=w)
    layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask))
    im.alpha_composite(layer)


# --------------------------------------------------------------------------- #
# text
# --------------------------------------------------------------------------- #
def text_size(txt, size, bold=True):
    f = font(size, bold)
    l, t, r, b = f.getbbox(txt)
    return r - l, b - t


def hand_text(d, xy, txt, size, rng, fill=WHITE, stroke=0, stroke_fill=INK, bold=True, jit=0.06, anchor_center=True):
    """Draw text letter by letter with a tiny random bounce per glyph."""
    f = font(size, bold)
    total = f.getlength(txt)
    x, y = xy
    if anchor_center:
        x -= total / 2
    for ch in txt:
        dy = rng.uniform(-size * jit, size * jit)
        d.text((x, y + dy), ch, font=f, fill=fill, anchor="lm", stroke_width=stroke, stroke_fill=stroke_fill)
        x += f.getlength(ch)


# --------------------------------------------------------------------------- #
# cut-out paper look
# --------------------------------------------------------------------------- #
def cutout(im: Image.Image, border: int = 9, shadow: int = 12, rough: bool = True, rng=None) -> tuple[Image.Image, tuple[int, int]]:
    """Give an RGBA drawing a white paper border and a soft drop shadow.

    Returns the new image and the (dx, dy) by which the original was shifted.
    """
    pad = border + shadow + 6
    W, H = im.size
    big = Image.new("RGBA", (W + 2 * pad, H + 2 * pad), (0, 0, 0, 0))
    big.alpha_composite(im, (pad, pad))
    a = big.getchannel("A").point(lambda v: 255 if v > 40 else 0)
    # dilate in two cheap passes (MaxFilter size must be odd)
    grown = a
    step = border
    while step > 0:
        k = min(step, 6)
        grown = grown.filter(ImageFilter.MaxFilter(2 * k + 1))
        step -= k
    if rough and rng is not None:
        grown = grown.filter(ImageFilter.GaussianBlur(1.6)).point(lambda v: 255 if v > 110 else 0)
    paper = Image.new("RGBA", big.size, (248, 246, 236, 255))
    paper.putalpha(grown)
    shadow_im = Image.new("RGBA", big.size, (0, 0, 0, 0))
    sh = Image.new("RGBA", big.size, (0, 0, 0, 120))
    sh.putalpha(grown.point(lambda v: v * 120 // 255))
    shadow_im.alpha_composite(sh, (shadow // 2, shadow))
    shadow_im = shadow_im.filter(ImageFilter.GaussianBlur(5))
    out = Image.new("RGBA", big.size, (0, 0, 0, 0))
    out.alpha_composite(shadow_im)
    out.alpha_composite(paper)
    out.alpha_composite(big)
    return out, (pad, pad)
