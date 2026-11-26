"""'Stare at the center for 10 seconds' — motion-aftereffect Short.

A rotating black/white logarithmic spiral (looks like it is flowing inward) for 11 s, then a hard cut to a
still real landscape that seems to warp/expand for a few seconds (motion aftereffect). Text via ASS,
synthesized drone hum + ticks + whoosh (no licensing).
Usage: render_stare.py OUTDIR real_clip.mp4 real_start
"""
import subprocess, sys
from pathlib import Path
import numpy as np

OUT = Path(sys.argv[1]); REAL = sys.argv[2]; RS = float(sys.argv[3])
W, H, FPS = 1080, 1920, 30
SPIRAL, REALD, END = 11.0, 5.0, 1.2          # spiral incl. 1 s hook, real scene, end card on real scene
total = SPIRAL + REALD + END
OUT.mkdir(parents=True, exist_ok=True)

# ---------- spiral ----------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
cx, cy = W / 2, 880
dx, dy = xx - cx, yy - cy
r = np.sqrt(dx * dx + dy * dy) + 1e-3
th = np.arctan2(dy, dx)
R = 520
mask = r < R
edge = np.clip((R - r) / 18, 0, 1)                   # soft edge
logr = np.log(r)
spf = SPIRAL - 0.0
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                      '-i', '-', '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', str(OUT / 'spiral.mp4')],
                     stdin=subprocess.PIPE)
for k in range(int(SPIRAL * FPS)):
    t = k / FPS
    phase = 8 * th + 16.0 * logr - 2 * np.pi * 1.4 * t   # 8-arm fine log spiral flowing inward
    v = (np.sin(phase) > 0).astype(np.float32)
    img = (v * 255 * edge)
    g = np.where(mask, img, 0).astype(np.uint8)
    frame = np.stack([g, g, g], axis=-1)
    frame[r < 16] = (230, 30, 30)
    frame[(r >= 16) & (r < 20)] = (255, 255, 255)
    p.stdin.write(frame.tobytes())
p.stdin.close(); p.wait()

# ---------- text ----------
def ts(t):
    m, s = divmod(max(t, 0), 60); return f"0:{int(m):02d}:{s:05.2f}"

ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Big,Montserrat Black,76,&H00FFFFFF,&H00FFFFFF,&H64000000,&H64000000,1,0,0,0,100,100,0,0,3,22,0,5,60,60,0,1",
       "Style: Sub,Montserrat SemiBold,46,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,0,4,5,60,60,0,1",
       "Style: Count,Bebas Neue,170,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,4,0,1,0,4,5,40,40,0,1",
       "Style: Dot,Arial,20,&H002020E0,&H002020E0,&H00FFFFFF,&H00000000,0,0,0,0,100,100,0,0,1,4,0,7,0,0,0,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
E = lambda a, b, st, txt: ass.append(f"Dialogue: 3,{ts(a)},{ts(b)},{st},,0,0,0,,{txt}")
CX = W // 2
E(0, 1.6, 'Big', r"{\pos(540,240)\fad(0,300)}STARE AT THE RED DOT")
E(0, 1.6, 'Sub', r"{\pos(540,1560)\fad(0,300)}for 10 seconds. don't look away.")
E(1.6, SPIRAL - 0.05, 'Sub', r"{\pos(540,240)\fad(300,0)}keep staring…")
for i in range(10):
    a = 1.0 + i
    E(a, a + 1, 'Count', fr"{{\pos(540,1600)\fscx80\fscy80\t(0,150,\fscx100\fscy100)}}{10 - i}")
# red dot drawn over the spiral centre (ASS so it stays crisp)
E(SPIRAL + 0.4, SPIRAL + 2.6, 'Big', r"{\pos(540,330)\fad(150,150)}it's moving…\Nright? 👀".replace(' 👀', ''))
E(SPIRAL + 2.7, total, 'Big', r"{\pos(540,330)\fad(200,0)}it's not.\Nthat's your brain.")
E(SPIRAL + REALD, total, 'Sub', r"{\pos(540,1640)\fad(200,0)}watch again")
(OUT / 'stare.ass').write_text('\n'.join(ass) + '\n')

# ---------- final ----------
hum = "0.25*sin(2*PI*55*t)*(0.7+0.3*sin(2*PI*0.25*t))+0.12*sin(2*PI*110*t)"
cmd = ['ffmpeg', '-v', 'error', '-y', '-i', str(OUT / 'spiral.mp4'),
       '-ss', str(RS), '-t', f'{REALD + END + 0.2}', '-i', REAL,
       '-f', 'lavfi', '-t', f'{SPIRAL}', '-i', f"aevalsrc='{hum}':s=48000",
       '-f', 'lavfi', '-t', '1.2', '-i', "aevalsrc='0.6*sin(2*PI*(900-700*t)*t)*exp(-3*t)':s=48000"]
ticks = []
for i in range(10):
    cmd += ['-f', 'lavfi', '-t', '0.08', '-i', "aevalsrc='0.45*sin(2*PI*1600*t)*exp(-90*t)':s=48000"]
    ticks.append(1.0 + i)
fc = [f"[0:v]fps={FPS},setsar=1[s]",
      f"[1:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS},"
      f"trim=duration={REALD + END},setpts=PTS-STARTPTS,eq=contrast=1.06:saturation=1.1[r]",
      f"[s][r]concat=n=2:v=1:a=0,ass={OUT / 'stare.ass'}[v]",
      f"[2:a]aformat=channel_layouts=stereo,afade=t=in:d=0.5,afade=t=out:st={SPIRAL - 0.4}:d=0.4[hum]",
      f"[3:a]aformat=channel_layouts=stereo,adelay={int(SPIRAL * 1000)}:all=1[wh]"]
names = ['[hum]', '[wh]']
for j, a in enumerate(ticks):
    fc.append(f"[{4 + j}:a]aformat=channel_layouts=stereo,adelay={int(a * 1000)}:all=1[t{j}]"); names.append(f'[t{j}]')
fc.append(''.join(names) + f"amix=inputs={len(names)}:normalize=0,apad,atrim=0:{total},loudnorm=I=-15:TP=-2[a]")
cmd += ['-filter_complex', ';'.join(fc), '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
        '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-t', f'{total}',
        str(OUT / 'stare_10_seconds.mp4')]
subprocess.run(cmd, check=True)
print('rendered', OUT / 'stare_10_seconds.mp4', total)
