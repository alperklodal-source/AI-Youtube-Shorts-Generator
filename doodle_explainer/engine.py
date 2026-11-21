"""Render a doodle-explainer Short from an episode JSON.

Pipeline: per-scene Turkish TTS (Piper, offline) -> scene timing -> frame
rendering (PIL) piped into ffmpeg -> procedural music + SFX mix -> mp4.
"""
from __future__ import annotations

import json
import math
import os
import random
import subprocess
import tempfile
import urllib.request
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .draw import INK, WHITE, YELLOW, blob_pts, ellipse, font, hand_text, line, rect, shape, star_pts
from .elements import ANIMATED, render_element

W, H = 1080, 1920
FPS = 30
BOIL_FPS = 8            # how often line wobble is redrawn
SR = 22050              # audio sample rate (Piper medium voices)
VOICE_DIR = os.path.expanduser(os.environ.get("DOODLE_VOICE_DIR", "~/.cache/doodle_explainer/voices"))
VOICE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/{lang}/{loc}/{name}/{q}/{loc}-{name}-{q}.onnx"


# --------------------------------------------------------------------------- #
# TTS
# --------------------------------------------------------------------------- #
def ensure_voice(voice: str) -> str:
    """voice like 'tr_TR-dfki-medium' -> local .onnx path (downloaded on first use)."""
    loc, name, q = voice.split("-")
    path = os.path.join(VOICE_DIR, f"{voice}.onnx")
    if not os.path.exists(path):
        os.makedirs(VOICE_DIR, exist_ok=True)
        url = VOICE_URL.format(lang=loc.split("_")[0], loc=loc, name=name, q=q)
        print(f"[voice] downloading {voice} ...")
        urllib.request.urlretrieve(url, path)
        urllib.request.urlretrieve(url + ".json", path + ".json")
    return path


def tts(text: str, voice_path: str, out_wav: str, length_scale: float = 0.85, speaker: int | None = None):
    cmd = ["python3", "-m", "piper", "-m", voice_path, "--length-scale", str(length_scale), "-f", out_wav]
    if speaker is not None:
        cmd += ["--speaker", str(speaker)]
    subprocess.run(cmd, input=text.encode("utf-8"), check=True, capture_output=True)


def read_wav(path: str) -> np.ndarray:
    with wave.open(path) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        if w.getnchannels() > 1:
            x = x.reshape(-1, w.getnchannels()).mean(1)
    if sr != SR:
        idx = np.linspace(0, len(x) - 1, int(len(x) * SR / sr))
        x = np.interp(idx, np.arange(len(x)), x)
    return x


def trim(x: np.ndarray, thr=0.012, with_offset=False):
    env = np.convolve(np.abs(x), np.ones(256) / 256, "same")
    nz = np.where(env > thr)[0]
    a = max(0, nz[0] - 400) if len(nz) else 0
    y = x[a: nz[-1] + 1200] if len(nz) else x
    return (y, a / SR) if with_offset else y


def time_stretch(x: np.ndarray, speed: float, tmp: str) -> np.ndarray:
    """Pitch-preserving speed change via ffmpeg atempo."""
    a, b = os.path.join(tmp, "ts_in.wav"), os.path.join(tmp, "ts_out.wav")
    write_wav(a, x)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", a, "-af", f"atempo={speed}", b], check=True)
    return read_wav(b)


def write_wav(path: str, x: np.ndarray):
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def tts_edge(texts, wavs, cfg):
    """Microsoft neural voices via edge-tts (natural native Turkish: tr-TR-AhmetNeural / tr-TR-EmelNeural)."""
    import asyncio

    import edge_tts

    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")

    async def one(txt, wav):
        mp3 = wav[:-4] + ".mp3"
        for attempt in range(4):
            try:
                c = edge_tts.Communicate(txt, cfg.get("voice", "tr-TR-AhmetNeural"), rate=cfg.get("rate", "+8%"),
                                         pitch=cfg.get("pitch", "+0Hz"), volume=cfg.get("volume", "+0%"), proxy=proxy)
                await c.save(mp3)
                break
            except Exception as e:  # transient network errors
                if attempt == 3:
                    raise
                print(f"[edge] retry {attempt + 1}: {e}")
                await asyncio.sleep(2 * (attempt + 1))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-ac", "1", "-ar", str(SR), wav], check=True)

    async def run():
        for i, (t, w) in enumerate(zip(texts, wavs)):
            print(f"[edge] {i + 1}/{len(texts)}: {t[:50]}", flush=True)
            await one(t, w)

    asyncio.run(run())


EMA_SCRIPT = os.path.join(os.path.dirname(__file__), "tts_ema.py")


def tts_ema(texts, wavs, cfg):
    """EMA Lightning (open Turkish TTS) in the torch venv; returns exact word timings per text."""
    py = os.path.expanduser(os.environ.get("DOODLE_TORCH_PY", "~/.cache/doodle_explainer/cbx/bin/python3"))
    tmp = os.path.dirname(wavs[0])
    job, tim = os.path.join(tmp, "ema_job.json"), os.path.join(tmp, "ema_timings.json")
    with open(job, "w", encoding="utf-8") as f:
        json.dump({"texts": texts, "wavs": wavs, "timings": tim, **cfg}, f, ensure_ascii=False)
    subprocess.run([py, EMA_SCRIPT, job], check=True, stderr=subprocess.DEVNULL)
    with open(tim, encoding="utf-8") as f:
        return json.load(f)


VOXCPM_SCRIPT = os.path.join(os.path.dirname(__file__), "tts_voxcpm.py")
VOICES_DIR = os.path.join(os.path.dirname(__file__), "voices")


def tts_voxcpm(texts, wavs, cfg, seeds=None):
    """VoxCPM2 reading with a designed voice from doodle_explainer/voices/<name>."""
    py = os.path.expanduser(os.environ.get("DOODLE_TORCH_PY", "~/.cache/doodle_explainer/cbx/bin/python3"))
    job = os.path.join(os.path.dirname(wavs[0]), "vox_job.json")
    vdir = cfg.get("voice", "eglenceli_anlatici")
    vdir = vdir if os.path.isdir(vdir) else os.path.join(VOICES_DIR, vdir)
    with open(job, "w", encoding="utf-8") as f:
        json.dump({"texts": texts, "wavs": wavs, "seeds": seeds, "voice_dir": vdir, **cfg}, f, ensure_ascii=False)
    subprocess.run([py, VOXCPM_SCRIPT, job], check=True, stderr=subprocess.DEVNULL)


CHATTERBOX_SCRIPT = os.path.join(os.path.dirname(__file__), "tts_chatterbox.py")


def tts_chatterbox(texts, wavs, cfg, seeds=None):
    """Run Chatterbox Multilingual in its own venv (torch is heavy) for all scenes at once."""
    py = os.path.expanduser(os.environ.get("DOODLE_CHATTERBOX_PY", "~/.cache/doodle_explainer/cbx/bin/python3"))
    job = os.path.join(os.path.dirname(wavs[0]), "cbx_job.json")
    with open(job, "w", encoding="utf-8") as f:
        json.dump({"texts": texts, "wavs": wavs, "seeds": seeds, **cfg}, f, ensure_ascii=False)
    subprocess.run([py, CHATTERBOX_SCRIPT, job], check=True, stderr=subprocess.DEVNULL)


def _norm(s: str) -> str:
    s = s.replace("I", "ı").replace("İ", "i").lower()
    for ch in "'’`":
        s = s.replace(ch, "")
    return " ".join("".join(ch if ch.isalnum() else " " for ch in s).split())


def similarity(heard: str, *targets: str) -> float:
    import difflib
    h = _norm(heard).split()
    return max(difflib.SequenceMatcher(None, h, _norm(t).split()).ratio() for t in targets)


class Aligner:
    _inst = None

    def __init__(self, model, tmp):
        from faster_whisper import WhisperModel
        self.m = WhisperModel(model, device="cpu", compute_type="int8")
        self.tmp = tmp

    @classmethod
    def get(cls, model, tmp):
        if cls._inst is None:
            try:
                cls._inst = cls(model, tmp)
            except Exception as e:  # faster-whisper missing / model download blocked
                print(f"[align] disabled: {e}")
                return None
        cls._inst.tmp = tmp
        return cls._inst

    def words(self, x: np.ndarray, lang: str):
        a16 = np.interp(np.linspace(0, len(x) - 1, int(len(x) * 16000 / SR)), np.arange(len(x)), x).astype(np.float32)
        segs, _ = self.m.transcribe(a16, language=lang, word_timestamps=True, beam_size=1)
        out = [(w.word.strip(), w.start, w.end) for s in segs for w in (s.words or []) if w.word.strip()]
        return out or None


# --------------------------------------------------------------------------- #
# procedural audio
# --------------------------------------------------------------------------- #
def sfx(kind: str, rng: np.random.Generator) -> np.ndarray:
    def tt(sec):
        return np.arange(int(SR * sec)) / SR
    if kind == "pop":
        t = tt(0.09)
        f = 900 * np.exp(-t * 25) + 250
        return 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 40)
    if kind == "whoosh":
        t = tt(0.35)
        n = rng.standard_normal(len(t))
        env = np.sin(np.pi * t / t[-1]) ** 2
        out = np.zeros_like(n)
        a = 0.0
        for i in range(len(n)):          # sweeping one-pole low-pass
            k = 0.02 + 0.25 * env[i]
            a += k * (n[i] - a)
            out[i] = a
        return 0.6 * out * env
    if kind == "stamp":
        t = tt(0.25)
        return 0.9 * np.sin(2 * np.pi * 70 * t) * np.exp(-t * 18) + 0.3 * rng.standard_normal(len(t)) * np.exp(-t * 60)
    if kind == "zap":
        t = tt(0.45)
        sq = np.sign(np.sin(2 * np.pi * (120 + 40 * np.sin(2 * np.pi * 30 * t)) * t))
        return 0.25 * sq * (0.5 + 0.5 * rng.random(len(t))) * np.exp(-t * 4)
    if kind == "boom":
        t = tt(0.9)
        n = rng.standard_normal(len(t))
        lp = np.convolve(n, np.ones(60) / 60, "same")
        return 1.2 * (lp * 3 + 0.6 * np.sin(2 * np.pi * 50 * t)) * np.exp(-t * 4)
    if kind == "ding":
        t = tt(0.6)
        return 0.35 * (np.sin(2 * np.pi * 1320 * t) + 0.5 * np.sin(2 * np.pi * 1980 * t)) * np.exp(-t * 6)
    return np.zeros(1)


def music_bed(n: int, mood: str = "mystery") -> np.ndarray:
    """Cheap dark synth pad + ticking pulse (mystery) or a bouncy pizzicato loop (fun)."""
    t = np.arange(n) / SR
    if mood == "fun":
        return fun_bed(n)
    if mood == "sneaky":  # playful-mysterious: minor pizzicato, cartoon-detective feel
        return 0.8 * fun_bed(n, bpm=100, prog=[(57, 60, 64, 69), (53, 57, 60, 65), (50, 53, 57, 62), (52, 56, 59, 64)]) \
            + 0.35 * dark_pad(n)
    roots = {"mystery": [55.0, 65.41, 49.0, 58.27], "upbeat": [65.41, 73.42, 87.31, 98.0]}[mood]
    bar = 4.0
    out = np.zeros(n)
    for i, f in enumerate(roots * int(math.ceil(n / SR / bar / len(roots)) + 1)):
        s0 = int(i * bar * SR)
        if s0 >= n:
            break
        s1 = min(n, s0 + int((bar + 0.6) * SR))
        tt = t[s0:s1] - t[s0]
        env = np.minimum(1, tt / 0.8) * np.minimum(1, (bar + 0.6 - tt) / 0.8)
        chord = sum(np.sin(2 * np.pi * f * m * tt + m) * a for m, a in ((1, 1), (1.5, 0.5), (2, 0.35), (2.003, 0.3), (3, 0.12)))
        out[s0:s1] += chord * env
    # pulse: soft tick on every beat
    beat = 60 / 96
    k = (t % beat)
    out += 0.25 * np.sin(2 * np.pi * 1800 * t) * np.exp(-k * 90)
    out += 0.4 * np.sin(2 * np.pi * 45 * t) * np.exp(-((t + beat / 2) % (beat * 2)) * 10)
    return out / (np.abs(out).max() + 1e-6)


def dark_pad(n: int) -> np.ndarray:
    t = np.arange(n) / SR
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t)
    return lfo * (np.sin(2 * np.pi * 55 * t) + 0.5 * np.sin(2 * np.pi * 82.4 * t + 1) + 0.3 * np.sin(2 * np.pi * 110.3 * t))


def fun_bed(n: int, bpm: float = 112, prog=None) -> np.ndarray:
    """Playful cartoon loop: plucked major arpeggios, bouncy bass, finger snaps."""
    out = np.zeros(n)
    beat = 60 / bpm
    step = beat / 2
    prog = prog or [(60, 64, 67, 72), (57, 60, 64, 69), (65, 69, 72, 77), (67, 71, 74, 79)]  # C Am F G
    pattern = [0, 2, 1, 3, 2, 1, 3, 2]
    rng = np.random.default_rng(2)

    def pluck(freq, dur, amp):
        tt = np.arange(int(dur * SR)) / SR
        return amp * (np.sin(2 * np.pi * freq * tt) + 0.3 * np.sin(4 * np.pi * freq * tt)) * np.exp(-tt * 9)

    k = 0
    while True:
        s0 = int(k * step * SR)
        if s0 >= n:
            break
        bar = int(k // 8) % len(prog)
        chord = prog[bar]
        note = chord[pattern[k % 8]] + (12 if (k // 32) % 2 else 0)
        seg = pluck(440 * 2 ** ((note - 69) / 12), step * 1.6, 0.35)
        if k % 2 == 0:  # bass on beats, octave bounce
            bn = chord[0] - 24 + (12 if (k // 2) % 2 else 0)
            seg = seg[: int(step * 1.6 * SR)]
            b = pluck(440 * 2 ** ((bn - 69) / 12), step * 1.8, 0.6)
            m = max(len(seg), len(b))
            seg = np.pad(seg, (0, m - len(seg))) + np.pad(b, (0, m - len(b)))
        if k % 4 == 2:  # snap on 2 and 4
            sn = int(0.06 * SR)
            snap = rng.standard_normal(sn) * np.exp(-np.arange(sn) / SR * 70) * 0.5
            seg = np.pad(seg, (0, max(0, sn - len(seg))))
            seg[:sn] += snap
        e = min(n, s0 + len(seg))
        out[s0:e] += seg[: e - s0]
        k += 1
    return out / (np.abs(out).max() + 1e-6)


# --------------------------------------------------------------------------- #
# backgrounds
# --------------------------------------------------------------------------- #
def make_bg(kind: str, seed: int) -> Image.Image:
    rng = random.Random(seed)
    if kind == "paper":
        im = Image.new("RGBA", (W, H), (233, 222, 192, 255))
        d = ImageDraw.Draw(im)
        for _ in range(9):
            x, y = rng.uniform(0, W), rng.uniform(0, H)
            ellipse(d, x, y, rng.uniform(60, 180), rng.uniform(40, 140), rng, fill=(215, 200, 160, 120), outline=None, w=0)
        for _ in range(6000):
            x, y = rng.uniform(0, W), rng.uniform(0, H)
            d.point((x, y), fill=(190, 175, 140, 255))
        rect(d, 40, 260, W - 40, H - 330, rng, outline=(120, 90, 50, 255), w=8, skew=8)
        return im
    top, bot = {"space": ((14, 22, 58), (30, 42, 96)), "alert": ((50, 10, 16), (110, 22, 30)),
                "night": ((10, 14, 40), (40, 40, 90)), "dawn": ((40, 30, 80), (210, 110, 80))}.get(kind, ((14, 22, 58), (30, 42, 96)))
    g = np.linspace(0, 1, H)[:, None, None]
    arr = (np.array(top)[None, None] * (1 - g) + np.array(bot)[None, None] * g) * np.ones((1, W, 1))
    noise = np.random.default_rng(seed).normal(0, 5, (H, W, 1))
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    im = Image.fromarray(arr, "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    for _ in range(260):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        r = rng.choice([1, 1, 1.5, 2, 2.5])
        a = rng.randint(120, 255)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 240, a))
    for _ in range(14):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        shape(d, star_pts(x, y, rng.uniform(10, 18), 3, 4, rng, 0, 0.1), rng, fill=(255, 250, 220, 230), w=0)
    return im


def twinkle(bg: Image.Image, variant: int, seed: int) -> Image.Image:
    rng = random.Random(seed * 31 + variant)
    im = bg.copy()
    d = ImageDraw.Draw(im)
    for _ in range(25):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(255, 255, 255, 255))
    return im


# --------------------------------------------------------------------------- #
# animation helpers
# --------------------------------------------------------------------------- #
def ease_out_back(x, s=1.9):
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


def ease_out_cubic(x):
    return 1 - (1 - x) ** 3


def ease_out_bounce(x):
    n1, d1 = 7.5625, 2.75
    if x < 1 / d1:
        return n1 * x * x
    if x < 2 / d1:
        x -= 1.5 / d1
        return n1 * x * x + 0.75
    if x < 2.5 / d1:
        x -= 2.25 / d1
        return n1 * x * x + 0.9375
    x -= 2.625 / d1
    return n1 * x * x + 0.984375


def transform(e, te, tscene, boil, idx, dur=1.0):
    """Return (dx, dy, scale, rot_deg, alpha) for an element te seconds after appearing."""
    dx = dy = rot = 0.0
    sc, al = 1.0, 1.0
    kind = e.get("in", "pop")
    dur = e.get("in_dur", 0.18 if kind == "stamp" else 0.4)
    x = min(1.0, max(0.0, te / dur))
    if kind == "pop":
        sc = max(0.0, ease_out_back(x))
    elif kind == "stamp":
        sc = 2.4 - 1.4 * ease_out_cubic(x)
        al = min(1, x * 3)
    elif kind == "slide_l":
        dx = -1300 * (1 - ease_out_cubic(x))
    elif kind == "slide_r":
        dx = 1300 * (1 - ease_out_cubic(x))
    elif kind == "slide_u":
        dy = 1500 * (1 - ease_out_cubic(x))
    elif kind == "drop":
        dur = e.get("in_dur", 0.7)
        x = min(1.0, max(0.0, te / dur))
        dy = -1400 * (1 - ease_out_bounce(x))
    elif kind == "fade":
        al = x
    elif kind == "grow":
        sc = ease_out_cubic(x)
    # path movement
    if "move" in e:
        mx, my = e["move"]
        m0, m1 = (v * dur for v in e.get("move_t", (0.0, 1.0)))  # fractions of the scene
        u = min(1, max(0, (tscene - m0) / max(1e-3, m1 - m0)))
        u = u * u * (3 - 2 * u)
        dx += (mx - e["x"]) * u
        dy += (my - e["y"]) * u
    loop = e.get("loop", "")
    ph = idx * 1.7
    amp = e.get("loop_amp", 1.0)
    if loop == "float":
        dy += 14 * amp * math.sin(2 * math.pi * 0.5 * tscene + ph)
    elif loop == "shake":
        dx += 7 * amp * math.sin(tscene * 55 + ph)
        dy += 4 * amp * math.sin(tscene * 41 + ph)
    elif loop == "pulse":
        sc *= 1 + 0.06 * amp * math.sin(2 * math.pi * 1.6 * tscene + ph)
    elif loop == "wiggle":
        rot += 5 * amp * math.sin(2 * math.pi * 1.1 * tscene + ph)
    elif loop == "spin":
        rot -= 25 * amp * tscene
    elif loop == "bob":
        rot += 3 * amp * math.sin(2 * math.pi * 0.7 * tscene + ph)
        dy += 8 * amp * math.sin(2 * math.pi * 1.4 * tscene + ph)
    # stop-motion jitter (cheap cut-out animation look)
    if e.get("jitter", True):
        r = random.Random(boil * 977 + idx * 13)
        dx += r.uniform(-2.5, 2.5)
        dy += r.uniform(-2.5, 2.5)
        rot += r.uniform(-0.8, 0.8)
    rot += e.get("rot", 0)
    sc *= e.get("scale", 1.0)
    return dx, dy, sc, rot, al


def paste(canvas: Image.Image, im: Image.Image, anchor, pos, sc, rot, al):
    if sc <= 0.01 or al <= 0.01:
        return
    ax, ay = anchor
    w, h = im.size
    if abs(sc - 1) > 1e-3:
        im = im.resize((max(1, int(w * sc)), max(1, int(h * sc))), Image.BILINEAR)
        ax, ay = ax * sc, ay * sc
        w, h = im.size
    ox, oy = ax - w / 2, ay - h / 2
    if abs(rot) > 0.05:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
        a = math.radians(rot)
        ox, oy = ox * math.cos(a) + oy * math.sin(a), -ox * math.sin(a) + oy * math.cos(a)
        w, h = im.size
    if al < 1:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * al)))
    x = int(pos[0] - (w / 2 + ox))
    y = int(pos[1] - (h / 2 + oy))
    # clip to canvas
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    crop = im.crop((x0 - x, y0 - y, x1 - x, y1 - y))
    canvas.alpha_composite(crop, (x0, y0))


# --------------------------------------------------------------------------- #
# captions + header
# --------------------------------------------------------------------------- #
def chunk_words(words, max_chars=16, max_words=3):
    chunks, cur = [], []
    for w in words:
        if cur and (len(" ".join(cur + [w])) > max_chars or len(cur) >= max_words):
            chunks.append(cur)
            cur = []
        cur.append(w)
        if w[-1] in ".!?…":
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return chunks


def caption_track(text, t0, t1, spoken=None):
    """Time caption words across [t0, t1].

    Without ``spoken`` the words are spread proportionally to their length.
    With ``spoken`` (whisper words: [(word, start, end)] relative to t0) the
    caption's character position is mapped onto the spoken character position,
    so captions follow the real speech even if the caption text differs from
    the spoken text (digits vs. words, etc.).
    """
    words = text.split()
    weights = [len(w) + 2 + (6 if w[-1] in ".!?," else 0) for w in words]
    total = sum(weights)
    if spoken:
        sw = [len(w) + 1 for w, _, _ in spoken]
        stot = sum(sw)
        xs, ys, acc = [0.0], [spoken[0][1]], 0
        for (w, a, b), n in zip(spoken, sw):
            xs += [acc / stot, (acc + n) / stot]
            ys += [a, b]
            acc += n
        xs.append(1.0)
        ys.append(spoken[-1][2])
        warp = lambda u: t0 + float(np.interp(u, xs, ys))  # noqa: E731
    else:
        warp = lambda u: t0 + (t1 - t0) * u  # noqa: E731
    times, acc = [], 0
    for wgt in weights:
        times.append((warp(acc / total), warp((acc + wgt) / total)))
        acc += wgt
    out, i = [], 0
    for ch in chunk_words(words):
        out.append({"words": ch, "times": times[i:i + len(ch)]})
        i += len(ch)
    return out


def draw_caption(canvas, chunk, t, y=1430):
    d = ImageDraw.Draw(canvas)
    size = 104
    f = font(size)
    words = chunk["words"]
    gap = f.getlength(" ")
    total = sum(f.getlength(w) for w in words) + gap * (len(words) - 1)
    t_start = chunk["times"][0][0]
    pop = min(1, (t - t_start) / 0.12)
    s = 0.85 + 0.15 * ease_out_back(pop)
    if s != 1:
        f = font(int(size * s))
        gap = f.getlength(" ")
        total = sum(f.getlength(w) for w in words) + gap * (len(words) - 1)
    x = W / 2 - total / 2
    for w, (a, b) in zip(words, chunk["times"]):
        col = YELLOW if a <= t < b + 0.05 else WHITE
        d.text((x, y), w, font=f, fill=col, anchor="lm", stroke_width=10, stroke_fill=INK)
        x += f.getlength(w) + gap


def make_header(series, ep, seed=5):
    rng = random.Random(seed)
    im = Image.new("RGBA", (W, 230), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    txt = f"{series}  #{ep}" if ep else series
    tw = font(64).getlength(txt)
    x0, x1 = W / 2 - tw / 2 - 50, W / 2 + tw / 2 + 50
    pts = [(x0, 120)] + [(x0 + (x1 - x0) * i / 24, 115 + rng.uniform(-6, 6)) for i in range(25)] + \
          [(x1, 200)] + [(x1 - (x1 - x0) * i / 24, 205 + rng.uniform(-6, 6)) for i in range(25)]
    shape(d, pts, rng, fill=(245, 238, 215, 245), w=4)
    hand_text(d, (W / 2, 160), txt, 64, rng, fill=(160, 20, 20, 255))
    return im


# --------------------------------------------------------------------------- #
# main render
# --------------------------------------------------------------------------- #
def render_episode(ep_path: str, out_path: str, preview: bool = False, keep_tmp: bool = False):
    with open(ep_path, encoding="utf-8") as f:
        ep = json.load(f)
    tmp = tempfile.mkdtemp(prefix="doodle_")
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    rng_np = np.random.default_rng(1)

    # 1) narration per scene (one batch so heavy TTS models load once)
    scenes = ep["scenes"]
    engine = ep.get("tts", "piper")
    wavs = [os.path.join(tmp, f"s{i:02d}.wav") for i in range(len(scenes))]
    texts = [sc.get("say", sc["text"]) for sc in scenes]
    word_times = None
    if engine == "ema":
        word_times = tts_ema(texts, wavs, ep.get("ema", {}))
    elif engine == "edge":
        tts_edge(texts, wavs, ep.get("edge", {}))
    elif engine in ("chatterbox", "voxcpm"):
        cfg = ep.get(engine, {})
        synth = tts_chatterbox if engine == "chatterbox" else tts_voxcpm
        seeds = [cfg.get("seed", 22)] * len(scenes)
        # cache: identical text + voice settings are never synthesized twice (fix visuals, re-render fast)
        import hashlib
        import shutil
        cache_dir = os.path.expanduser(os.environ.get("DOODLE_TTS_CACHE", "~/.cache/doodle_explainer/tts"))
        os.makedirs(cache_dir, exist_ok=True)
        ckey = {k: v for k, v in cfg.items() if k not in ("retries", "min_similarity")}
        cpaths = [os.path.join(cache_dir, hashlib.sha1(json.dumps([engine, ckey, t], ensure_ascii=False, sort_keys=True)
                                                     .encode()).hexdigest() + ".wav") for t in texts]
        todo = []
        for i, cp in enumerate(cpaths):
            if os.path.exists(cp) and not ep.get("no_cache"):
                shutil.copy(cp, wavs[i])
            else:
                todo.append(i)
        if len(todo) < len(scenes):
            print(f"[cache] {len(scenes) - len(todo)} sahne önbellekten")
        if todo:
            synth([texts[i] for i in todo], [wavs[i] for i in todo], cfg, [seeds[i] for i in todo])
        # transcript QC: re-roll scenes whose speech doesn't match the script
        qc = Aligner.get(ep.get("whisper_model", "small"), tmp)
        best = {}
        for attempt in range(cfg.get("retries", 3) + 1):
            bad = []
            for i in todo:
                sc = scenes[i]
                x = trim(read_wav(wavs[i]))
                heard = " ".join(w for w, _, _ in (qc.words(x, ep.get("lang", "tr")) or []))
                score = similarity(heard, texts[i], sc["text"])
                if i not in best or score > best[i][0]:
                    best[i] = (score, x)
                if best[i][0] < cfg.get("min_similarity", 0.85):
                    bad.append(i)
            if todo:
                print(f"[qc] attempt {attempt}: scores " + " ".join(f"{i}:{best[i][0]:.2f}" for i in sorted(best)))
            if not bad or attempt == cfg.get("retries", 3):
                break
            todo = bad
            sub_w = [os.path.join(tmp, f"r{i:02d}.wav") for i in bad]
            synth([texts[i] for i in bad], sub_w, cfg, [seeds[i] + 101 * (attempt + 1) for i in bad])
            for i, w in zip(bad, sub_w):
                os.replace(w, wavs[i])
        for i, (_, x) in best.items():
            write_wav(wavs[i], x)
            shutil.copy(wavs[i], cpaths[i])
    else:
        voice = ensure_voice(ep.get("voice", "tr_TR-dfki-medium"))
        for txt, wav in zip(texts, wavs):
            tts(txt, voice, wav, ep.get("length_scale", 0.85), ep.get("speaker"))
    t_cursor = 0.0
    voice_parts = []
    for i, sc in enumerate(scenes):
        x, off = trim(read_wav(wavs[i]), with_offset=True)
        if word_times:
            sc["_words"] = [(w, a - off, b - off) for w, a, b in word_times[i]]
        if ep.get("speed", 1.0) != 1.0:
            x = time_stretch(x, ep["speed"], tmp)
        lead, tail = sc.get("lead", 0.12), sc.get("tail", 0.3)
        sc["_start"] = t_cursor
        sc["_voice"] = (t_cursor + lead, t_cursor + lead + len(x) / SR)
        sc["_dur"] = lead + len(x) / SR + tail
        sc["_wav"] = x
        voice_parts.append(np.concatenate([np.zeros(int(lead * SR)), x, np.zeros(int(tail * SR))]))
        t_cursor += sc["_dur"]
    total = t_cursor + ep.get("outro", 0.4)
    if preview:
        print(f"[timing] total {total:.1f}s")
        for i, sc in enumerate(scenes):
            print(f"  scene {i}: {sc['_dur']:.2f}s  {sc['text'][:60]}")
    n_frames = int(total * FPS)

    # 2) captions (word-aligned with faster-whisper when available)
    captions = []
    need_align = ep.get("align", True) and not word_times
    aligner = Aligner.get(ep.get("whisper_model", "small"), tmp) if need_align else None
    for sc in scenes:
        words = sc.get("_words") or (aligner.words(sc["_wav"], sc.get("lang", ep.get("lang", "tr"))) if aligner else None)
        captions += caption_track(sc["text"], *sc["_voice"], spoken=words)

    # 3) sfx timeline
    n_samp = int(total * SR) + SR
    voice_track = np.zeros(n_samp)
    pos = 0
    for part in voice_parts:
        voice_track[pos:pos + len(part)] += part
        pos += len(part)
    sfx_track = np.zeros(n_samp)

    def add(kind, at, gain=1.0):
        s = sfx(kind, rng_np) * gain
        i0 = int(at * SR)
        i1 = min(n_samp, i0 + len(s))
        sfx_track[i0:i1] += s[: i1 - i0]

    for i, sc in enumerate(scenes):
        if i:
            add("whoosh", max(0, sc["_start"] - 0.12), 0.8)
        for e in sc.get("elements", []):
            at = sc["_start"] + e.get("at", 0) * sc["_dur"]
            k = e.get("sfx") or {"pop": "pop", "stamp": "stamp", "drop": "pop"}.get(e.get("in", "pop"))
            if k:
                add(k, at + (0.12 if k == "stamp" else 0.0), e.get("sfx_gain", 0.8))

    music = music_bed(n_samp, ep.get("music", "mystery"))
    mix = voice_track * 1.0 + sfx_track * 0.35 + music * ep.get("music_gain", 0.07)
    mix = mix / max(1.0, np.abs(mix).max() / 0.95)
    mix_wav = os.path.join(tmp, "mix.wav")
    write_wav(mix_wav, mix)

    # 4) frames
    header = make_header(ep.get("series", "KIYAMET DOSYALARI"), ep.get("episode"))
    bg_cache, el_cache = {}, {}
    silent = os.path.join(tmp, "video.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset",
                           "veryfast" if preview else "medium", "-crf", "20", "-pix_fmt", "yuv420p", silent],
                          stdin=subprocess.PIPE)
    scene_idx = 0
    for fi in range(n_frames):
        t = fi / FPS
        while scene_idx + 1 < len(scenes) and t >= scenes[scene_idx + 1]["_start"]:
            scene_idx += 1
        sc = scenes[scene_idx]
        ts = t - sc["_start"]
        boil = int(t * BOIL_FPS) % 3
        bgk = (sc.get("bg", "space"), scene_idx if sc.get("bg") == "paper" else 0)
        if bgk not in bg_cache:
            bg_cache[bgk] = [twinkle(make_bg(bgk[0], 11 + bgk[1]), v, 11) if bgk[0] != "paper"
                             else make_bg("paper", 11 + bgk[1]) for v in range(3)]
        frame = bg_cache[bgk][boil].copy()
        shake = 0.0
        for idx, e in enumerate(sc.get("elements", [])):
            at = e.get("at", 0) * sc["_dur"]
            if ts < at or ("until" in e and ts > e["until"] * sc["_dur"]):
                continue
            te = ts - at
            if e.get("in") == "stamp" and 0.1 < te < 0.45:
                shake = max(shake, 1 - (te - 0.1) / 0.35)
            seed = hash((scene_idx, idx, boil)) & 0xFFFFFF
            if e["type"] in ANIMATED:
                im, anc = render_element(e, random.Random(seed), ts)
            else:
                key = (scene_idx, idx, boil)
                if key not in el_cache:
                    el_cache[key] = render_element(e, random.Random(seed), 0)
                im, anc = el_cache[key]
            dx, dy, s, rot, al = transform(e, te, ts, int(t * BOIL_FPS), idx, sc["_dur"])
            paste(frame, im, anc, (e["x"] + dx, e["y"] + dy), s, rot, al)
        # camera: punch-in on cut, then slow push
        z = 1.0 + 0.045 * (ts / max(0.1, sc["_dur"])) + 0.06 * max(0, 1 - ts / 0.22) ** 2
        if z > 1.001 or shake:
            zw, zh = int(W * z), int(H * z)
            big = frame.resize((zw, zh), Image.BILINEAR)
            sx = random.Random(fi).uniform(-18, 18) * shake
            sy = random.Random(fi + 7).uniform(-18, 18) * shake
            cx = int((zw - W) / 2 + sx)
            cy = int((zh - H) / 2 + sy)
            cx = min(max(cx, 0), zw - W)
            cy = min(max(cy, 0), zh - H)
            frame = big.crop((cx, cy, cx + W, cy + H))
        frame.alpha_composite(header, (0, 0))
        for ch in captions:
            if ch["times"][0][0] <= t < ch["times"][-1][1] + 0.08:
                draw_caption(frame, ch, t, ep.get("caption_y", 1430))
                break
        # light film grain / vignette is baked into bg; just push the frame
        ff.stdin.write(frame.convert("RGB").tobytes())
        if fi == int(n_frames * ep.get("thumb_at", 0.08)):
            frame.convert("RGB").save(os.path.splitext(out_path)[0] + "_thumb.jpg", quality=92)
        if fi % (FPS * 5) == 0:
            print(f"[render] {t:5.1f}s / {total:.1f}s")
        # drop caches from past scenes
        if fi % FPS == 0:
            for k in [k for k in el_cache if k[0] < scene_idx]:
                del el_cache[k]
    ff.stdin.close()
    ff.wait()

    # 5) mux + loudness
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", mix_wav,
                    "-af", "highpass=f=70,acompressor=threshold=-18dB:ratio=3:attack=5:release=80,loudnorm=I=-14:TP=-1.5",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-shortest", out_path], check=True)
    if not keep_tmp:
        for fn in os.listdir(tmp):
            os.remove(os.path.join(tmp, fn))
        os.rmdir(tmp)
    meta = ep.get("meta", {})
    if meta:
        with open(os.path.splitext(out_path)[0] + "_meta.txt", "w", encoding="utf-8") as f:
            f.write(f"BAŞLIK: {meta.get('title', '')}\n\nAÇIKLAMA:\n{meta.get('description', '')}\n\n")
            f.write("ETİKETLER: " + " ".join(meta.get("hashtags", [])) + "\n")
    print(f"[done] {out_path}  ({total:.1f}s)")
    return out_path
