"""'Every bounce = +1 ball. Will they escape?' — real physics simulation Short, fully synthesized (video + sound).

Rotating neon ring with a gap; gravity; each ring bounce spawns a new ball at the centre and plays the next note
of a pentatonic melody; balls that pass through the gap escape and fly off. Counters drawn per frame.
"""
import math, subprocess, sys, wave, colorsys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
W, H, FPS, DUR, SR = 1080, 1920, 30, 15.0, 48000
SUB = 8                                   # physics substeps per frame
CX, CY, R = 540, 1000, 430
BR = 13                                   # ball radius
GAP = math.radians(38); OMEGA = 1.1       # gap size, ring rotation (rad/s)
G = 0.45 / SUB ** 2                       # gravity: 0.45 px/frame^2
MAXB = 450
rng = np.random.default_rng(3)
font = lambda s: ImageFont.truetype(str(Path.home() / '.fonts/Anton-Regular.ttf'), s)
F_BIG, F_MID, F_NUM = font(120), font(84), font(150)

pos = np.array([[CX + 0.0, CY - 120.0]]); vel = np.array([[11.0, -3.0]]) / SUB   # px per substep
hue = np.array([0.55])
alive_in = np.array([True])
escaped = 0; total = 1
events = []                               # (time, note index)
note_i = 0
canvas = np.zeros((H, W, 3), np.float32)


def gap_contains(theta, t):
    gc = (OMEGA * t) % (2 * math.pi)
    d = (theta - gc + math.pi) % (2 * math.pi) - math.pi
    return abs(d) < GAP / 2


def ring_layer(t):
    lay = Image.new('RGB', (W, H), (0, 0, 0)); d = ImageDraw.Draw(lay)
    gc = math.degrees((OMEGA * t) % (2 * math.pi))
    g2 = math.degrees(GAP) / 2
    hue_r = (t * 0.06) % 1
    col = tuple(int(c * 255) for c in colorsys.hsv_to_rgb(hue_r, 0.85, 1.0))
    # PIL angles are clockwise from +x in screen coords; our theta uses atan2(dy, dx) in screen coords too
    for wdt, c in ((26, tuple(v // 4 for v in col)), (14, tuple(v // 2 for v in col)), (7, col)):
        d.arc((CX - R - BR, CY - R - BR, CX + R + BR, CY + R + BR), start=gc + g2, end=gc - g2 + 360, fill=c, width=wdt)
    return np.asarray(lay, np.float32)


frames = int(DUR * FPS)
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                      '-i', '-', '-c:v', 'libx264', '-crf', '17', '-pix_fmt', 'yuv420p', str(OUT / 'sim.mp4')], stdin=subprocess.PIPE)
for fi in range(frames):
    for s in range(SUB):
        t = (fi + s / SUB) / FPS
        vel[:, 1] += G
        pos += vel
        d = pos - [CX, CY]
        dist = np.hypot(d[:, 0], d[:, 1])
        hit = alive_in & (dist + BR >= R)
        for i in np.where(hit)[0]:
            theta = math.atan2(d[i, 1], d[i, 0])
            if gap_contains(theta, t):
                alive_in[i] = False; escaped += 1          # flies out through the gap
                continue
            n = d[i] / dist[i]
            vn = vel[i] @ n
            if vn > 0:
                vel[i] -= 2 * vn * n
                vel[i] *= 1.012                          # tiny energy gain keeps it lively
                pos[i] = [CX, CY] + n * (R - BR - 0.5)
                events.append((t, note_i)); note_i += 1
                if len(pos) < MAXB:                      # every bounce = +1 ball
                    a = rng.uniform(0, 2 * math.pi); sp = rng.uniform(8, 14) / SUB
                    pos = np.vstack([pos, [CX, CY - 60]]); vel = np.vstack([vel, [sp * math.cos(a), sp * math.sin(a)]])
                    hue = np.append(hue, (hue[-1] + 0.061) % 1); alive_in = np.append(alive_in, True)
                    total += 1
        # keep speeds sane
        sp_ = np.hypot(vel[:, 0], vel[:, 1]); fast = sp_ > 26 / SUB
        vel[fast] *= ((26 / SUB) / sp_[fast])[:, None]
    # drop balls far off-screen
    keep = (pos[:, 1] < H + 200) & (pos[:, 0] > -200) & (pos[:, 0] < W + 200)
    pos, vel, hue, alive_in = pos[keep], vel[keep], hue[keep], alive_in[keep]

    t = fi / FPS
    canvas *= 0.74                                         # motion trails
    lay = Image.new('RGB', (W, H), (0, 0, 0)); dr = ImageDraw.Draw(lay)
    for (x, y), h in zip(pos, hue):
        c = tuple(int(v * 255) for v in colorsys.hsv_to_rgb(h, 0.75, 1.0))
        dr.ellipse((x - BR, y - BR, x + BR, y + BR), fill=c)
    canvas = np.maximum(canvas, np.asarray(lay, np.float32))
    img = np.clip(canvas + ring_layer(t), 0, 255).astype(np.uint8)
    im = Image.fromarray(img); dt = ImageDraw.Draw(im)

    def ctext(txt, f, y, fill):
        w = dt.textlength(txt, font=f); dt.text(((W - w) / 2, y), txt, font=f, fill=fill, stroke_width=6, stroke_fill='black')
    inside = int(alive_in.sum())
    if t < 2.2:
        ctext('EVERY BOUNCE = +1 BALL', F_MID, 160, 'white')
        ctext('WILL THEY ESCAPE?', F_BIG, 270, '#FFE500')
    else:
        ctext(f'BALLS: {total}', F_NUM, 170, 'white')
        ctext(f'ESCAPED: {escaped}', F_MID, 350, '#FFE500')
    if t >= 12.6:
        ctext('HOW MANY', F_BIG, 1560, 'white'); ctext('WILL ESCAPE?', F_BIG, 1690, '#FFE500')
    p.stdin.write(np.asarray(im).tobytes())
    if fi % 90 == 0:
        print('frame', fi, 'balls', len(pos), 'escaped', escaped, flush=True)
p.stdin.close(); p.wait()

# ---------- sound: each bounce plays the next pentatonic note ----------
scale = [0, 2, 4, 7, 9, 12, 14, 16, 19, 21, 24, 21, 19, 16, 14, 12, 9, 7, 4, 2]   # up-down C major pentatonic
audio = np.zeros(int(DUR * SR) + SR)
last_t = -1; per_frame = {}
nd = int(0.35 * SR); tt = np.arange(nd) / SR
for (t, k) in events:
    fr = int(t * FPS); per_frame[fr] = per_frame.get(fr, 0) + 1
    if per_frame[fr] > 3:                 # limit polyphony when it gets busy
        continue
    f = 523.25 * 2 ** (scale[k % len(scale)] / 12)
    tone = (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(4 * np.pi * f * tt) + 0.12 * np.sin(6 * np.pi * f * tt)) * np.exp(-tt * 9)
    i0 = int(t * SR); audio[i0:i0 + nd] += 0.32 * tone
audio = audio[:int(DUR * SR)]
audio = np.tanh(audio * 1.2) * 0.8
fo = int(0.5 * SR); audio[-fo:] *= np.linspace(1, 0, fo)
with wave.open(str(OUT / 'notes.wav'), 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((audio * 32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(OUT / 'sim.mp4'), '-i', str(OUT / 'notes.wav'), '-filter_complex',
                '[1:a]aformat=channel_layouts=stereo,aecho=0.8:0.5:60|120:0.25|0.15,loudnorm=I=-14:TP=-2[a]', '-map', '0:v',
                '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-t', str(DUR),
                str(OUT / 'every_bounce_plus_one.mp4')], check=True)
print('done', len(events), 'bounces, total', total, 'escaped', escaped)
