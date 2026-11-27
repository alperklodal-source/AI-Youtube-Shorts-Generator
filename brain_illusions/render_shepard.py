"""'This sound never stops rising' — Shepard tone Short (12 s, seamless loop), fully synthesized.

Audio: N octave-spaced sine partials glide up continuously; loudness follows a Gaussian over log-frequency,
so partials fade in at the bottom and out at the top -> pitch seems to rise forever.
Video: one glowing bar per partial, moving up exactly with its pitch, brightness = its loudness.
"""
import subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
W, H, FPS, SR = 1080, 1920, 30, 48000
DUR, CYCLE, N = 12.0, 6.0, 8          # one octave every 6 s -> 12 s = 2 octaves = seamless loop
F0, CENTER, SIGMA = 40.0, 4.2, 1.35   # lowest partial 40 Hz; loudness peak ~ 40*2^4.2 Hz (~735 Hz)

# ---------- audio ----------
t = np.arange(int(DUR * SR)) / SR
p = (t / CYCLE) % 1.0
audio = np.zeros_like(t)
for k in range(N):
    oct_ = (k + p) % N                                   # position in octaves, wraps top->bottom
    f = F0 * 2.0 ** oct_
    amp = np.exp(-0.5 * ((oct_ - CENTER) / SIGMA) ** 2)
    phase = 2 * np.pi * np.cumsum(f) / SR
    audio += amp * np.sin(phase)
audio /= np.max(np.abs(audio)) * 1.25
fade = int(0.03 * SR)
audio[:fade] *= np.linspace(0, 1, fade); audio[-fade:] *= np.linspace(1, 0, fade)
pcm = (audio * 32767).astype(np.int16)
import wave
with wave.open(str(OUT / 'shepard.wav'), 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

# ---------- video ----------
TOP, BOT = 330, 1640                      # vertical range of the "pitch" axis
cols = [(255, 64, 129), (255, 145, 0), (255, 229, 0), (0, 230, 118), (0, 229, 255), (41, 121, 255),
        (170, 0, 255), (255, 64, 129)]
p_ = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                       '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p',
                       str(OUT / 'bars.mp4')], stdin=subprocess.PIPE)
for i in range(int(DUR * FPS)):
    tt = i / FPS
    pp = (tt / CYCLE) % 1.0
    img = Image.new('RGB', (W, H), (6, 8, 18))
    glow = Image.new('RGB', (W, H), (0, 0, 0))
    d, g = ImageDraw.Draw(img), ImageDraw.Draw(glow)
    for k in range(N):
        oct_ = (k + pp) % N
        a = float(np.exp(-0.5 * ((oct_ - CENTER) / SIGMA) ** 2))
        y = BOT - (BOT - TOP) * oct_ / (N - 1)
        if y < TOP - 60:
            continue
        c = cols[k % len(cols)]
        cc = tuple(int(v * a) for v in c)
        half = int(160 + 300 * a)
        g.rounded_rectangle((W / 2 - half - 30, y - 34, W / 2 + half + 30, y + 34), radius=34, fill=cc)
        d.rounded_rectangle((W / 2 - half, y - 14, W / 2 + half, y + 14), radius=14, fill=cc)
    glow = glow.filter(ImageFilter.GaussianBlur(28))
    frame = np.clip(np.asarray(img, np.int16) + np.asarray(glow, np.int16), 0, 255).astype(np.uint8)
    p_.stdin.write(frame.tobytes())
p_.stdin.close(); p_.wait()


# ---------- text ----------
def ts(x):
    m, s = divmod(max(x, 0), 60); return f"0:{int(m):02d}:{s:05.2f}"

ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Big,Anton,175,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,2,0,1,8,4,5,50,50,0,1",
       "Style: Yel,Anton,190,&H0000E5FF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,2,0,1,8,4,5,50,50,0,1",
       "Style: Small,Oswald Medium,92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,5,3,5,50,50,0,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
E = lambda a, b, st, y, txt, fx=r"\fad(120,120)": ass.append(f"Dialogue: 3,{ts(a)},{ts(b)},{st},,0,0,0,,{{\\pos(540,{y}){fx}}}{txt}")
POP = r"\fscx80\fscy80\t(0,160,\fscx100\fscy100)"
E(0.0, 2.6, 'Big', 170, r"THIS SOUND NEVER", POP)
E(0.0, 2.6, "Yel", 360, r"STOPS RISING", POP)
E(0.0, 2.6, 'Small', 1790, "SOUND ON")
E(2.6, 6.0, 'Big', 200, "LISTEN…")
E(2.6, 6.0, 'Small', 1790, "it keeps going up")
E(6.0, 9.2, 'Big', 170, "STILL RISING…")
E(6.0, 9.2, "Yel", 360, "RIGHT?", POP)
E(9.2, 12.0, 'Big', 170, "IT NEVER", POP)
E(9.2, 12.0, "Yel", 360, "GETS HIGHER", POP)
E(9.4, 12.0, 'Small', 1790, "your brain is being tricked")
(OUT / 'shepard.ass').write_text('\n'.join(ass) + '\n')

subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(OUT / 'bars.mp4'), '-i', str(OUT / 'shepard.wav'),
                '-filter_complex', f"[0:v]ass={OUT / 'shepard.ass'}[v];[1:a]aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-2[a]",
                '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac',
                '-b:a', '192k', '-movflags', '+faststart', '-t', str(DUR), str(OUT / 'shepard_tone.mp4')], check=True)
print('rendered', OUT / 'shepard_tone.mp4')
