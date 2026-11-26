"""Render a 'Guess the place' Short from a project spec (spec.json).

spec = {
  "voice": "audio/v1.wav", "words": "audio/v1.words.json",
  "pause_after": 4.48, "pause": 1.2,          # silence inserted before the reveal
  "shots": [{"clip": "clips/x.mp4", "start": 0, "dur": 2.5, "text": "..."}...],
  "countdown_at": 4.5,                        # optional "3 2 1" over the pause
  "reveal": {"at": 5.9, "title": "FAROE ISLANDS", "sub": "..."},
  "fact":   {"at": 7.2, "lines": ["70,000 SHEEP", "54,000 PEOPLE"]},
  "out": "out/short.mp4"
}
"""
import json, subprocess, sys
from pathlib import Path

W, H, FPS = 1080, 1920, 30
proj = Path(sys.argv[1]).resolve()
S = json.load(open(proj / 'spec.json'))
total = sum(s['dur'] for s in S['shots'])


def ts(t):
    h, r = divmod(max(t, 0), 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


# ---------- subtitles (ASS) ----------
words = json.load(open(proj / S['words']))
for w in words:  # fix ASR spellings, e.g. "1" -> "one"
    w['w'] = S.get('fix', {}).get(w['w'], w['w'])
for w in words:  # shift words after the inserted pause
    if w['s'] >= S['pause_after']:
        w['s'] += S['pause']; w['e'] += S['pause']
groups, cur = [], []
for w in words:
    cur.append(w)
    if len(cur) == 3 or w['w'].endswith(('.', ',', '!', '?')):
        groups.append(cur); cur = []
if cur: groups.append(cur)

ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "",
       "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Cap,Inter Black,88,&H00FFFFFF,&H0000E5FF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,7,3,2,60,60,560,1",
       "Style: Top,Inter Black,84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,6,2,8,60,60,230,1",
       "Style: Big,Inter Black,190,&H0000E5FF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,10,4,5,40,40,0,1",
       "Style: Reveal,Inter Black,120,&H0000E5FF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,9,4,5,40,40,0,1",
       "Style: Fact,Inter Black,92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,7,3,5,40,40,0,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for gi, g in enumerate(groups):  # active word highlighted yellow
    nxt = groups[gi + 1][0]['s'] if gi + 1 < len(groups) else 1e9
    for i, w in enumerate(g):
        end = g[i + 1]['s'] if i + 1 < len(g) else min(w['e'] + 0.15, nxt)
        txt = ' '.join((r"{\c&H00E5FF&}" + x['w'].upper() + r"{\c&HFFFFFF&}") if j == i else x['w'].upper() for j, x in enumerate(g))
        ass.append(f"Dialogue: 0,{ts(w['s'])},{ts(end)},Cap,,0,0,0,,{{\\fad(40,0)}}{txt}")
t = 0
for s in S['shots']:
    if s.get('text'):
        ass.append(f"Dialogue: 1,{ts(t)},{ts(t + s['dur'])},Top,,0,0,0,,{{\\fad(120,120)}}{s['text']}")
    t += s['dur']
if 'countdown_at' in S:
    step = S['pause'] / 3
    for i, n in enumerate('321'):
        a = S['countdown_at'] + i * step
        ass.append(f"Dialogue: 2,{ts(a)},{ts(a + step)},Big,,0,0,0,,{{\\fscx140\\fscy140\\t(0,200,\\fscx100\\fscy100)}}{n}")
r = S['reveal']
ass.append(f"Dialogue: 2,{ts(r['at'])},{ts(r.get('end', S['fact']['at']))},Reveal,,0,0,0,,{{\\pos({W//2},{H//2 - 140})\\fscx60\\fscy60\\t(0,180,\\fscx105\\fscy105)\\t(180,300,\\fscx100\\fscy100)}}{r['title']}")
f = S['fact']
ass.append(f"Dialogue: 2,{ts(f['at'])},{ts(total)},Fact,,0,0,0,,{{\\pos({W//2},{H//2 - 160})\\fad(120,0)}}" + r"\N".join(f['lines']))
(proj / 'out').mkdir(exist_ok=True)
(proj / 'out' / 'subs.ass').write_text('\n'.join(ass) + '\n')

# ---------- video ----------
cmd = ['ffmpeg', '-v', 'error', '-y']
for s in S['shots']:
    cmd += ['-ss', str(s['start']), '-t', str(s['dur']), '-i', str(proj / s['clip'])]
vi = len(S['shots'])
cmd += ['-i', str(proj / S['voice'])]
fc = []
for i, s in enumerate(S['shots']):
    fc.append(f"[{i}:v]fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,"
              f"trim=duration={s['dur']},setpts=PTS-STARTPTS[v{i}]")
fc.append(''.join(f"[v{i}]" for i in range(vi)) + f"concat=n={vi}:v=1:a=0,eq=contrast=1.06:saturation=1.12,"
          f"ass={proj / 'out' / 'subs.ass'}[vout]")
pa, pz = S['pause_after'], S['pause']
fc.append(f"[{vi}:a]asplit=2[a1][a2];[a1]atrim=0:{pa},asetpts=PTS-STARTPTS[p1];"
          f"[a2]atrim={pa},asetpts=PTS-STARTPTS,adelay={int(pz * 1000)}:all=1[p2];"
          f"[p1][p2]concat=n=2:v=0:a=1,loudnorm=I=-14:TP=-1.5,apad,atrim=0:{total}[aout]")
cmd += ['-filter_complex', ';'.join(fc), '-map', '[vout]', '-map', '[aout]',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', str(FPS),
        '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-t', str(total), str(proj / S['out'])]
subprocess.run(cmd, check=True)
print('rendered', proj / S['out'], f'{total:.2f}s')
