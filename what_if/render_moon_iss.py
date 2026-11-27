"""'What if the Moon was as close as the ISS?' — composite + synthesized animation, text only, synthesized sound.

Real footage: Pixabay sunset skyline (slowed). Moon: NASA full-moon photo (public domain) as a disc.
Timeline (s): 0-2 normal tiny moon | 2-6 approaches (distance counter) | 6-9 fills the sky |
9-13 tidal break-up into fragments that spread into a band | 13-15 ring across the sky.
"""
import json, math, subprocess, sys, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

P = Path(sys.argv[1])
W, H, FPS, DUR, SR = 1080, 1920, 30, 15.0, 48000
rng = np.random.default_rng(7)

# ---------- background frames (slowed real clip) ----------
bgdir = P / 'bgframes'; bgdir.mkdir(exist_ok=True)
if not (bgdir / 'f_0450.png').exists():
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(P / 'clips/pixabay_video_173137.mp4'), '-vf',
                    f'setpts=1.55*PTS,fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}',
                    '-frames:v', str(int(DUR * FPS)), '-start_number', '0', str(bgdir / 'f_%04d.png')], check=True)
ref = np.asarray(Image.open(bgdir / 'f_0060.png').convert('RGB')).astype(np.float32)
L = ref.mean(2)
yy = np.arange(H)[:, None]
fg = ((L < 115) & (yy > 820)) | (yy > 1300)                    # buildings / city = foreground
fgmask = Image.fromarray((fg * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1.5))

# ---------- moon disc (NASA photo) ----------
src = Image.open(P / 'img/GSFC_20171208_Archive_e000868.jpg').convert('RGB')
arr = np.asarray(src).astype(np.float32); lum = arr.mean(2)
ys, xs = np.where(lum > 40)
cx, cy = xs.mean(), ys.mean(); rad = 0.5 * ((xs.max() - xs.min()) + (ys.max() - ys.min())) / 2
moon = src.crop((int(cx - rad), int(cy - rad), int(cx + rad), int(cy + rad))).resize((1400, 1400), Image.LANCZOS)
m = Image.new('L', (1400, 1400), 0); ImageDraw.Draw(m).ellipse((4, 4, 1396, 1396), fill=255)
m = m.filter(ImageFilter.GaussianBlur(3))
moon_rgba = moon.convert('RGBA'); moon_rgba.putalpha(m)

# Voronoi fragments of the disc (for the break-up)
NF = 70
seeds = rng.uniform(0, 1400, (NF, 2))
gy, gx = np.mgrid[0:1400:4, 0:1400:4]
lab = np.argmin(((gx[..., None] - seeds[:, 0]) ** 2 + (gy[..., None] - seeds[:, 1]) ** 2), axis=2)
lab = np.kron(lab, np.ones((4, 4), dtype=lab.dtype))
frags = []
base = np.asarray(moon_rgba)
for i in range(NF):
    mk = lab == i
    if mk.sum() < 50:
        continue
    yy0, xx0 = np.where(mk)
    x0, x1, y0, y1 = xx0.min(), xx0.max() + 1, yy0.min(), yy0.max() + 1
    piece = base[y0:y1, x0:x1].copy(); piece[..., 3] = piece[..., 3] * mk[y0:y1, x0:x1]
    # dark crack edge
    frags.append(dict(img=Image.fromarray(piece), cx=(x0 + x1) / 2 - 700, cy=(y0 + y1) / 2 - 700,
                      ang=rng.uniform(0, 2 * math.pi), spin=rng.uniform(-40, 40), rr=rng.uniform(0.85, 1.15)))

ease = lambda x: 0.5 - 0.5 * math.cos(math.pi * min(max(x, 0), 1))
MX, MY0 = 540, 470


def moon_state(t):
    """(radius px, centre y)"""
    if t < 2.0:
        return 26, MY0
    if t < 6.0:
        k = (t - 2.0) / 4.0
        r = 26 * (1150 / 26) ** (k ** 1.6)                       # exponential approach
        return r, MY0 + (640 - MY0) * ease(k)
    return 1150 + 20 * (t - 6.0), 640 + 6 * (t - 6.0)


def ring_layer(t, alpha):
    """bright elliptical ring band across the sky, partially hidden behind the planet's horizon"""
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cxr, cyr = 540, 1450
    for k in range(34):
        a_ = 1450 + k * 8; b_ = 820 + k * 6
        c = int(225 + 30 * math.sin(k * 1.7)); op = int(alpha * (50 + 95 * math.sin(k * 0.8) ** 2) * (0.55 + 0.45 * math.sin(k * 0.27)))
        gap = 1 if 14 <= k <= 16 else 0                               # Cassini-like gap
        if gap:
            continue
        d.ellipse((cxr - a_, cyr - b_, cxr + a_, cyr + b_), outline=(c, c - 12, c - 40, op), width=5)
    blur = lay.filter(ImageFilter.GaussianBlur(9))
    return Image.alpha_composite(blur, lay.filter(ImageFilter.GaussianBlur(1)))


def frame(i):
    t = i / FPS
    bg = Image.open(bgdir / f'f_{i:04d}.png').convert('RGBA')
    sky = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if t < 9.0:
        r, my = moon_state(t)
        size = max(2, int(2 * r))
        mm = moon_rgba.resize((size, size), Image.LANCZOS)
        # atmospheric tint at sunset: a little warm and slightly transparent when small
        a = mm.split()[3].point(lambda v: int(v * (0.85 if r < 200 else 0.97)))
        mm.putalpha(a)
        sky.alpha_composite(mm, (int(MX - r), int(my - r)))
        if t > 6.0:   # slight shake when it fills the sky
            pass
    elif t < 13.0:
        k = (t - 9.0) / 4.0; e = ease(k)
        r = 1150 + 60; scale = (2 * r) / 1400
        for f in frags:
            # pieces drift outward and get stretched along a flat orbit (ring forming)
            dx = f['cx'] * scale * (1 + 1.6 * e) + math.cos(f['ang']) * 420 * e * f['rr']
            dy = f['cy'] * scale * (1 + 0.25 * e) + 900 * e * e * 0.35 + math.sin(f['ang']) * 120 * e
            sc = scale * (1 - 0.55 * e)
            im = f['img'].resize((max(2, int(f['img'].width * sc)), max(2, int(f['img'].height * sc))))
            im = im.rotate(f['spin'] * e, expand=True)
            if e > 0.6:
                al = im.split()[3].point(lambda v, q=(1 - (e - 0.6) / 0.4): int(v * q)); im.putalpha(al)
            sky.alpha_composite(im, (int(MX + dx - im.width / 2), int(640 + dy - im.height / 2)))
        if k > 0.3:
            sky = Image.alpha_composite(sky, ring_layer(t, min(1, (k - 0.3) / 0.6)))
        # flash at the break
        if t < 9.4:
            fl = Image.new('RGBA', (W, H), (255, 240, 220, int(200 * (1 - (t - 9.0) / 0.4))))
            sky = Image.alpha_composite(sky, fl)
    else:
        sky = ring_layer(t, 1.0)
    comp = Image.alpha_composite(bg, sky)
    comp.paste(bg, (0, 0), fgmask)                     # city stays in front
    if 6.0 <= t < 9.0:                                  # rumble shake
        s = 4 * math.sin(t * 90)
        comp = comp.transform((W, H), Image.AFFINE, (1, 0, s, 0, 1, s * 0.6))
    return comp.convert('RGB')


# ---------- text ----------
def ts(x):
    mm_, s = divmod(max(x, 0), 60); return f"0:{int(mm_):02d}:{s:05.2f}"

ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Big,Anton,150,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,2,0,1,9,5,5,40,40,0,1",
       "Style: Yel,Anton,150,&H0000E5FF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,2,0,1,9,5,5,40,40,0,1",
       "Style: Num,Anton,170,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,2,0,1,9,5,5,40,40,0,1",
       "Style: Small,Oswald Medium,70,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,6,3,5,40,40,0,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
POP = r"\fscx80\fscy80\t(0,160,\fscx100\fscy100)"
def E(a, b, st, y, txt, fx=r"\fad(100,120)"):
    ass.append(f"Dialogue: 3,{ts(a)},{ts(b)},{st},,0,0,0,,{{\\pos(540,{y}){fx}}}{txt}")
E(0, 2.2, 'Big', 1380, "WHAT IF THE MOON", POP)
E(0, 2.2, 'Yel', 1540, "WAS AS CLOSE", POP)
E(0, 2.2, 'Yel', 1700, "AS THE ISS?", POP)
# distance counter 384,400 km -> 400 km
for k in range(int(2.0 * 10), int(6.0 * 10)):
    t0 = k / 10; x = (t0 - 2.0) / 4.0
    dist = 384400 * (400 / 384400) ** (x ** 1.6)
    E(t0, t0 + 0.1, 'Num', 1450, f"{int(round(dist, -1 if dist > 1000 else 0)):,} km", "")
E(2.0, 6.0, 'Small', 1600, "distance to the Moon", r"\fad(150,0)")
E(6.0, 7.6, 'Big', 1420, "IT WOULD FILL", POP)
E(6.0, 7.6, 'Yel', 1580, "HALF THE SKY", POP)
E(7.6, 9.0, 'Big', 1420, "AND CIRCLE EARTH", POP)
E(7.6, 9.0, 'Yel', 1580, "EVERY 2 HOURS", POP)
E(9.3, 13.0, 'Big', 1420, "THEN GRAVITY WOULD", POP)
E(9.3, 13.0, 'Yel', 1580, "TEAR IT APART", POP)
E(13.0, 15.0, 'Big', 1420, "AND EARTH WOULD", POP)
E(13.0, 15.0, 'Yel', 1580, "HAVE RINGS", POP)
(P / 'out').mkdir(exist_ok=True)
(P / 'out/moon.ass').write_text('\n'.join(ass) + '\n')

# ---------- sound (synthesized) ----------
t = np.arange(int(DUR * SR)) / SR
out = np.zeros_like(t)
f = 38 + 22 * np.clip((t - 2) / 7, 0, 1) ** 2                      # rising drone 38 -> 60 Hz
ph = 2 * np.pi * np.cumsum(f) / SR
env = np.clip(t / 1.0, 0, 1) * np.where(t < 9, 0.35 + 0.65 * np.clip((t - 2) / 7, 0, 1), np.exp(-(t - 9) * 0.9))
out += env * (np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3.01 * ph))
noise = rng.standard_normal(len(t))
lp = np.convolve(noise, np.ones(400) / 400, mode='same')               # low rumble
out += 3.5 * lp * np.clip((t - 5.5) / 3.5, 0, 1) * (t < 9.2)
crack = (t >= 9.0) & (t < 11.5)
out[crack] += 1.6 * noise[crack] * np.exp(-(t[crack] - 9.0) * 3.0) + 1.2 * np.sin(2 * np.pi * 45 * (t[crack] - 9)) * np.exp(-(t[crack] - 9) * 2.0)
pad = (t >= 12.0)                                                        # calm major pad for the rings
for fr in (220, 277.2, 329.6, 440):
    out[pad] += 0.12 * np.sin(2 * np.pi * fr * t[pad]) * np.clip((t[pad] - 12) / 1.0, 0, 1)
out = out / np.max(np.abs(out)) * 0.9
fo = int(0.6 * SR); out[-fo:] *= np.linspace(1, 0, fo)
with wave.open(str(P / 'out/moon_sfx.wav'), 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())

# ---------- render ----------
pp = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                       '-i', '-', '-i', str(P / 'out/moon_sfx.wav'), '-filter_complex',
                       f"[0:v]ass={P / 'out/moon.ass'}[v];[1:a]aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-2[a]",
                       '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac',
                       '-b:a', '192k', '-movflags', '+faststart', '-t', str(DUR), str(P / 'out/moon_as_close_as_iss.mp4')],
                      stdin=subprocess.PIPE)
for i in range(int(DUR * FPS)):
    pp.stdin.write(frame(i).tobytes())
    if i % 90 == 0:
        print('frame', i, flush=True)
pp.stdin.close(); pp.wait()
print('done')
