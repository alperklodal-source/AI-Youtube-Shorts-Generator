"""'While you watch this' Short: live counters driven by the viewer's own watch time.

Every value shown = rate × (seconds since the video started), updated 10×/s, so the numbers literally
measure how long the viewer has been watching.

spec = {
  "shots": [{"clip": "...", "start": 0, "dur": 2.3, "vf": ""}, ...],
  "intro": {"end": 2.3, "lines": ["since you started", "watching this video…"]},
  "stats": [{"at": 2.3, "end": 5.0, "rate": 44, "fmt": "{:,.0f}", "label": "lightning flashes on Earth"}, ...],
  "summary": {"at": 15.0, "title": "and it's still happening.", "items": [0, 1, 2, 3, 4]},
  "music": {"file": "...", "start": 0, "vol": 0.9},
  "out": "out/x.mp4"
}
"""
import json, subprocess, sys
from pathlib import Path

W, H, FPS, STEP = 1080, 1920, 30, 0.1
proj = Path(sys.argv[1]).resolve()
S = json.load(open(proj / 'spec.json'))
total = sum(s['dur'] for s in S['shots'])


def ts(t):
    m, s = divmod(max(t, 0), 60)
    return f"0:{int(m):02d}:{s:05.2f}"


ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Timer,JetBrains Mono,44,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,0,3,5,40,40,0,1",
       "Style: TimerLbl,Inter SemiBold,34,&H40FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,5,0,1,0,3,5,40,40,0,1",
       "Style: Title,Inter Black,86,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,0,6,5,70,70,0,1",
       "Style: Num,Inter Black,190,&H0000E5FF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,0,8,5,30,30,0,1",
       "Style: Label,Inter Bold,64,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,0,5,5,80,80,0,1",
       "Style: Row,Inter Bold,54,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,0,4,4,90,60,0,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
E = lambda layer, a, b, st, txt: ass.append(f"Dialogue: {layer},{ts(a)},{ts(b)},{st},,0,0,0,,{txt}")
CX = W // 2
ticks = [round(i * STEP, 2) for i in range(int(total / STEP) + 1)]

# watch-time HUD (whole video)
E(2, 0, total, 'TimerLbl', f"{{\\pos({CX},190)}}YOU'VE BEEN WATCHING")
for t in ticks:
    E(2, t, min(t + STEP, total), 'Timer', f"{{\\pos({CX},250)}}00:{t:04.1f}s")

it = S['intro']
E(3, 0, it['end'], 'Title', f"{{\\pos({CX},900)\\fad(250,200)}}" + r"\N".join(it['lines']))

for s in S['stats']:
    E(3, s['at'], s['end'], 'Label', f"{{\\pos({CX},1120)\\fad(150,150)}}{s['label']}")
    if s.get('pre'):
        E(3, s['at'], s['end'], 'Label', f"{{\\pos({CX},720)\\fad(150,150)}}{s['pre']}")
    first = True
    for t in ticks:
        if s['at'] <= t < s['end']:
            v = s['fmt'].format(s['rate'] * t)
            pop = r"\fscx85\fscy85\t(0,200,\fscx100\fscy100)" if first else ""
            E(4, t, min(t + STEP, s['end']), 'Num', f"{{\\pos({CX},930){pop}}}{v}")
            first = False

sm = S.get('summary')
if sm:
    E(3, sm['at'], total, 'Title', f"{{\\pos({CX},1480)\\fad(400,0)}}{sm['title']}")
    for row, idx in enumerate(sm['items']):
        s = S['stats'][idx]
        y = 560 + row * 150
        a = sm['at'] + row * 0.15
        for t in ticks:
            if t >= a:
                v = s['fmt'].format(s['rate'] * t)
                E(3, t, min(t + STEP, total), 'Row', f"{{\\pos(90,{y})}}{{\\c&H00E5FF&}}{v} {{\\c&HFFFFFF&\\fs40}}{s['short']}")
(proj / 'out').mkdir(exist_ok=True)
(proj / 'out' / 'live.ass').write_text('\n'.join(ass) + '\n')

cmd, fc = ['ffmpeg', '-v', 'error', '-y'], []
for i, s in enumerate(S['shots']):
    cmd += ['-ss', str(s['start']), '-t', f"{s['dur'] + 0.1:.2f}", '-i', str(proj / s['clip'])]
    vf = (',' + s['vf']) if s.get('vf') else ''
    fc.append(f"[{i}:v]fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,"
              f"trim=duration={s['dur']},setpts=PTS-STARTPTS{vf}[v{i}]")
n = len(S['shots'])
fc.append(''.join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0,eq=brightness=-0.08:contrast=1.05,"
          f"vignette=angle=PI/4,ass={proj / 'out' / 'live.ass'}[vout]")
M = S['music']
cmd += ['-ss', str(M.get('start', 0)), '-i', str(proj / M['file'])]
fc.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total},asetpts=PTS-STARTPTS,"
          f"volume={M.get('vol', 0.9)},afade=t=in:d=0.5,afade=t=out:st={total - 1.2:.2f}:d=1.2,loudnorm=I=-14:TP=-2[aout]")
cmd += ['-filter_complex', ';'.join(fc), '-map', '[vout]', '-map', '[aout]',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', str(FPS),
        '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-t', f'{total:.2f}', str(proj / S['out'])]
subprocess.run(cmd, check=True)
print('rendered', proj / S['out'], f'{total:.2f}s')
