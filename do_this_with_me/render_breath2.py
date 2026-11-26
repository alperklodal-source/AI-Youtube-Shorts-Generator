"""Guided breathing Short, text-only + music (v2: clear instructions, countdown, progress bar, rounds).

spec = {
  "shots": [{"clip": "...", "start": 0, "dur": 10}, ...],          # crossfaded
  "music": {"file": "...mp3", "start": 0, "vol": 0.8},
  "intro": [{"at": 0, "end": 1.5, "lines": ["feeling anxious?"], "style": "Title"}, ...],
  "howto": {"at": 3.2, "end": 7.4, "header": "HOW IT WORKS", "steps": ["...", "...", "..."], "gap": 0.8,
            "footer": "let's do it together"},
  "name": "the physiological sigh",                                 # small title during the exercise
  "rounds": [[{"dur": 2, "scale": 0.85, "big": "INHALE", "sub": "through your nose"}, ...], ...],
  "start": 7.6, "round_gap": 0.2, "base_scale": 0.42,
  "outro": [{"at": 26.0, "end": 29.5, "lines": ["how do you feel now?"], "style": "Title"}, ...],
  "out": "out/x.mp4"
}
"""
import json, math, subprocess, sys
from pathlib import Path

W, H, FPS = 1080, 1920, 30
CX, CY, R = W // 2, 960, 300
proj = Path(sys.argv[1]).resolve()
S = json.load(open(proj / 'spec.json'))
XF = 0.8  # crossfade between shots
total = sum(s['dur'] for s in S['shots']) - XF * (len(S['shots']) - 1)


def ts(t):
    m, s = divmod(max(t, 0), 60)
    return f"0:{int(m):02d}:{s:05.2f}"


def shape(points):  # positive-space drawing helper
    return points


k = 0.5523 * R
P = lambda x, y: f"{x + R:.0f} {y + R:.0f}"
CIRCLE = (f"m {P(0, -R)} b {P(k, -R)} {P(R, -k)} {P(R, 0)} b {P(R, k)} {P(k, R)} {P(0, R)} "
          f"b {P(-k, R)} {P(-R, k)} {P(-R, 0)} b {P(-R, -k)} {P(-k, -R)} {P(0, -R)}")
BAR_W, BAR_H, BAR_Y = 640, 12, 1450
BAR = f"m 0 0 l {BAR_W} 0 {BAR_W} {BAR_H} 0 {BAR_H}"

ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Fill,Arial,20,&HD8FFFFFF,&HD8FFFFFF,&HFFFFFFFF,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
       "Style: Ring,Arial,20,&HFFFFFFFF,&HFFFFFFFF,&H30FFFFFF,&H00000000,0,0,0,0,100,100,0,0,1,6,0,7,0,0,0,1",
       "Style: BarBg,Arial,20,&HB0FFFFFF,&HB0FFFFFF,&HFFFFFFFF,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
       "Style: Bar,Arial,20,&H10FFFFFF,&H10FFFFFF,&HFFFFFFFF,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
       "Style: Title,Inter Black,92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,0,6,5,70,70,0,1",
       "Style: Sub,Inter SemiBold,52,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,0,4,5,80,80,0,1",
       "Style: Header,Inter Black,58,&H0000E5FF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,6,0,1,0,4,5,70,70,0,1",
       "Style: Step,Inter Bold,58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,0,5,4,110,80,0,1",
       "Style: Big,Inter Black,110,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,4,0,1,0,6,5,40,40,0,1",
       "Style: Count,Inter Black,150,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,0,4,5,40,40,0,1",
       "Style: Small,Inter SemiBold,42,&H30FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,4,0,1,0,3,5,40,40,0,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
E = lambda layer, a, b, style, text: ass.append(f"Dialogue: {layer},{ts(a)},{ts(b)},{style},,0,0,0,,{text}")
NL = r"\N"

for t in S.get('intro', []) + S.get('outro', []):
    E(3, t['at'], t['end'], t.get('style', 'Title'),
      f"{{\\pos({CX},{t.get('y', CY)})\\fad(300,300)}}" + NL.join(t['lines']))

h = S.get('howto')
if h:
    E(3, h['at'], h['end'], 'Header', f"{{\\pos({CX},640)\\fad(300,300)}}{h['header']}")
    for i, st in enumerate(h['steps']):
        a = h['at'] + 0.3 + i * h.get('gap', 0.8)
        E(3, a, h['end'], 'Step', f"{{\\pos(110,{800 + i * 150})\\fad(250,300)}}{{\\c&H00E5FF&}}{i + 1}  {{\\c&HFFFFFF&}}{st}")
    if h.get('footer'):
        fa = h['at'] + 0.3 + len(h['steps']) * h.get('gap', 0.8) + 0.2
        E(3, fa, h['end'], 'Sub', f"{{\\pos({CX},1330)\\fad(250,300)}}{h['footer']}")

t = S['start']
prev = S.get('base_scale', 0.42)
rounds = S['rounds']
ex_start = t
for ri, rnd in enumerate(rounds):
    r0 = t
    for ph in rnd:
        a, b = t, t + ph['dur']
        ms = int(ph['dur'] * 1000)
        s0, s1 = prev * 100, ph['scale'] * 100
        anim = f"\\fscx{s0:.0f}\\fscy{s0:.0f}\\t(0,{ms},0.7,\\fscx{s1:.0f}\\fscy{s1:.0f})"
        E(0, a, b, 'Fill', f"{{\\pos({CX},{CY})\\an5\\blur6{anim}\\p1}}{CIRCLE}")
        E(1, a, b, 'Ring', f"{{\\pos({CX},{CY})\\an5\\blur1{anim}\\p1}}{CIRCLE}")
        E(2, a, b, 'Big', f"{{\\pos({CX},470)\\fad(120,0)}}{ph['big']}")
        E(2, a, b, 'Sub', f"{{\\pos({CX},575)\\fad(120,0)}}{ph['sub']}")
        for j in range(math.ceil(ph['dur'] - 1e-6)):  # countdown 3..2..1 inside the circle
            n = math.ceil(ph['dur'] - j - 1e-6)
            E(3, a + j, min(a + j + 1, b), 'Count', f"{{\\pos({CX},{CY})\\fscx80\\fscy80\\t(0,180,\\fscx100\\fscy100)}}{n}")
        x0 = CX - BAR_W // 2
        E(1, a, b, 'BarBg', f"{{\\pos({x0},{BAR_Y})\\an7\\p1}}{BAR}")
        E(2, a, b, 'Bar', f"{{\\pos({x0},{BAR_Y})\\an7\\fscx0\\t(0,{ms},\\fscx100)\\p1}}{BAR}")
        prev = ph['scale']
        t = b
    E(2, r0, t, 'Small', f"{{\\pos({CX},1530)}}ROUND {ri + 1} OF {len(rounds)}")
    t += S.get('round_gap', 0.2)
if S.get('name'):
    E(2, ex_start, t, 'Small', f"{{\\pos({CX},300)\\fad(300,300)}}{S['name'].upper()}")
(proj / 'out').mkdir(exist_ok=True)
(proj / 'out' / 'breath2.ass').write_text('\n'.join(ass) + '\n')

# ---------- video: crossfaded calm shots ----------
cmd, fc = ['ffmpeg', '-v', 'error', '-y'], []
for i, s in enumerate(S['shots']):
    cmd += ['-ss', str(s['start']), '-t', f"{s['dur'] + 0.2:.2f}", '-i', str(proj / s['clip'])]
    fc.append(f"[{i}:v]fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,"
              f"trim=duration={s['dur']},setpts=PTS-STARTPTS,format=yuv420p[v{i}]")
last, off = 'v0', S['shots'][0]['dur']
for i in range(1, len(S['shots'])):
    fc.append(f"[{last}][v{i}]xfade=transition=fade:duration={XF}:offset={off - XF:.2f}[x{i}]")
    last, off = f"x{i}", off - XF + S['shots'][i]['dur']
fc.append(f"[{last}]eq=brightness=-0.10:saturation=0.9,vignette=angle=PI/4,ass={proj / 'out' / 'breath2.ass'}[vout]")
M = S['music']
n = len(S['shots'])
cmd += ['-ss', str(M.get('start', 0)), '-i', str(proj / M['file'])]
fc.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total},asetpts=PTS-STARTPTS,"
          f"volume={M.get('vol', 0.8)},afade=t=in:d=1.0,afade=t=out:st={total - 1.5:.2f}:d=1.5,"
          "loudnorm=I=-16:TP=-2[aout]")
cmd += ['-filter_complex', ';'.join(fc), '-map', '[vout]', '-map', '[aout]',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', str(FPS),
        '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-t', f'{total:.2f}', str(proj / S['out'])]
subprocess.run(cmd, check=True)
print('rendered', proj / S['out'], f'{total:.2f}s')
