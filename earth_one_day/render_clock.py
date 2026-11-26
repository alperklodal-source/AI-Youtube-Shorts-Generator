"""'If Earth's history was one day' Short: a 24-hour clock races (then crawls) through 4.54 billion years.

spec = {
  "shots": [{"clip": "...", "start": 0, "dur": 2.6}, ...],
  "clock": [[0.6, 0], [3.0, 14100], ...],      # keyframes: video seconds -> clock seconds (piecewise linear)
  "tenths_after": 11.8,                          # show HH:MM:SS.s from here
  "hook": {"end": 2.4, "lines": ["if Earth's history", "was one day…"]},
  "events": [{"at": 0.6, "end": 2.6, "title": "Earth is born", "sub": "4.5 billion years ago"}, ...],
  "finale": {"at": 16.4, "lines": ["we've been here", "for 6 seconds."]},
  "music": {"file": "...", "start": 0, "vol": 0.9},
  "out": "out/x.mp4"
}
"""
import bisect, json, subprocess, sys
from pathlib import Path

W, H, FPS, STEP = 1080, 1920, 30, 1 / 30
proj = Path(sys.argv[1]).resolve()
S = json.load(open(proj / 'spec.json'))
total = sum(s['dur'] for s in S['shots'])
KF = S['clock']


def clock_at(t):
    xs = [k[0] for k in KF]
    if t <= xs[0]:
        return KF[0][1]
    if t >= xs[-1]:
        return KF[-1][1]
    i = bisect.bisect_right(xs, t) - 1
    (x0, y0), (x1, y1) = KF[i], KF[i + 1]
    return y0 + (y1 - y0) * (t - x0) / (x1 - x0)


def fmt_clock(c, tenths):
    h, r = divmod(c, 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:04.1f}" if tenths else f"{int(h):02d}:{int(m):02d}:{int(s):02d}"


def ts(t):
    m, s = divmod(max(t, 0), 60)
    return f"0:{int(m):02d}:{s:05.2f}"


ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Clock,JetBrains Mono,128,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,0,6,5,20,20,0,1",
       "Style: Hook,Inter Black,88,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,0,6,5,70,70,0,1",
       "Style: Ev,Inter Black,80,&H0000E5FF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,0,6,5,60,60,0,1",
       "Style: Sub,Inter SemiBold,48,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,2,0,1,0,4,5,60,60,0,1",
       "Style: Final,Inter Black,100,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,0,7,5,60,60,0,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
E = lambda layer, a, b, st, txt: ass.append(f"Dialogue: {layer},{ts(a)},{ts(b)},{st},,0,0,0,,{txt}")
CX = W // 2
fin = S['finale']

# clock: one event per frame-ish, only when the text changes
t, last, seg_start = 0.0, None, 0.0
end_clock = fin['at']
while t < end_clock + 1e-6:
    txt = fmt_clock(clock_at(t), t >= S.get('tenths_after', 1e9))
    if txt != last:
        if last is not None:
            E(2, seg_start, t, 'Clock', f"{{\\pos({CX},560)}}{last}")
        last, seg_start = txt, t
    t = round(t + STEP, 4)
E(2, seg_start, end_clock, 'Clock', f"{{\\pos({CX},560)}}{last}")
E(2, end_clock, total, 'Clock', f"{{\\pos({CX},560)\\fad(0,400)}}{last}")

hk = S['hook']
E(3, 0, hk['end'], 'Hook', f"{{\\pos({CX},1000)\\fad(200,250)}}" + r"\N".join(hk['lines']))
for ev in S['events']:
    E(3, ev['at'], ev['end'], 'Ev', f"{{\\pos({CX},1060)\\fscx80\\fscy80\\t(0,200,\\fscx100\\fscy100)\\fad(0,150)}}{ev['title']}")
    E(3, ev['at'] + 0.1, ev['end'], 'Sub', f"{{\\pos({CX},1160)\\fad(150,150)}}{ev['sub']}")
E(4, fin['at'], total, 'Final', f"{{\\pos({CX},1060)\\fad(300,0)}}" + r"\N".join(fin['lines']))
(proj / 'out').mkdir(exist_ok=True)
(proj / 'out' / 'clock.ass').write_text('\n'.join(ass) + '\n')

cmd, fc = ['ffmpeg', '-v', 'error', '-y'], []
for i, s in enumerate(S['shots']):
    cmd += ['-ss', str(s['start']), '-t', f"{s['dur'] + 0.1:.2f}", '-i', str(proj / s['clip'])]
    fc.append(f"[{i}:v]fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,"
              f"trim=duration={s['dur']},setpts=PTS-STARTPTS[v{i}]")
n = len(S['shots'])
fc.append(''.join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0,eq=brightness=-0.09:contrast=1.06,"
          f"vignette=angle=PI/4,ass={proj / 'out' / 'clock.ass'}[vout]")
M = S['music']
cmd += ['-ss', str(M.get('start', 0)), '-i', str(proj / M['file'])]
fc.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total},asetpts=PTS-STARTPTS,"
          f"volume={M.get('vol', 0.9)},afade=t=in:d=0.4,afade=t=out:st={total - 1.2:.2f}:d=1.2,loudnorm=I=-14:TP=-2[aout]")
cmd += ['-filter_complex', ';'.join(fc), '-map', '[vout]', '-map', '[aout]',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', str(FPS),
        '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-t', f'{total:.2f}', str(proj / S['out'])]
subprocess.run(cmd, check=True)
print('rendered', proj / S['out'], f'{total:.2f}s')
