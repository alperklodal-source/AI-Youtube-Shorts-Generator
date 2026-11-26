"""'Which one is AI?' split-screen quiz: A (top) vs B (bottom), same subject, one real one AI.

Per round: both halves play -> freeze with "A or B?" + draining thinking bar -> reveal: AI half replays the tell
(optionally slowed), stamps AI / REAL on the halves, one-line tell.

spec = {
  "hook": {"dur": 1.2, "lines": ["one of these is AI"]},
  "rounds": [{
     "top":    {"clip": "...", "start": 0, "ai": true,  "tell_start": 3.8, "tell_speed": 0.6},
     "bottom": {"clip": "...", "start": 1, "ai": false},
     "play": 2.6, "think": 3.2, "reveal": 3.2, "tell": ["watch the right ear…"]}, ...],
  "end": {"dur": 2.4, "lines": ["how many", "did you get?"], "sub": "..."},
  "music": {...}, "out": "out/x.mp4"
}
"""
import json, subprocess, sys
from pathlib import Path

W, H, FPS, DIV = 1080, 1920, 30, 8
HH = (H - DIV) // 2
proj = Path(sys.argv[1]).resolve()
S = json.load(open(proj / 'spec.json'))


def ts(t):
    m, s = divmod(max(t, 0), 60)
    return f"0:{int(m):02d}:{s:05.2f}"


FIT = f"scale={W}:{HH}:force_original_aspect_ratio=increase,crop={W}:{HH},setsar=1"
cmd, fc, n = ['ffmpeg', '-v', 'error', '-y'], [], 0
pieces = {'top': [], 'bottom': []}


def add_play(side, clip, start, dur, speed=1.0):
    global n
    cmd.extend(['-ss', str(start), '-t', f"{dur * speed + 0.2:.2f}", '-i', str(proj / clip)])
    lab = f"{side[0]}{len(pieces[side])}"
    fc.append(f"[{n}:v]{FIT},setpts=(PTS-STARTPTS)/{speed},fps={FPS},trim=duration={dur},setpts=PTS-STARTPTS[{lab}]")
    pieces[side].append(f"[{lab}]"); n += 1


def add_freeze(side, clip, at, dur):
    global n
    cmd.extend(['-ss', str(at), '-i', str(proj / clip)])
    lab = f"{side[0]}{len(pieces[side])}"
    fc.append(f"[{n}:v]trim=end_frame=1,{FIT},loop=loop=-1:size=1,fps={FPS},trim=duration={dur},setpts=PTS-STARTPTS[{lab}]")
    pieces[side].append(f"[{lab}]"); n += 1


ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Band,Inter Black,70,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,1,0,3,20,0,5,40,40,0,1",
       "Style: Q,Inter Black,72,&H00000000,&H00FFFFFF,&H0000E5FF,&H0000E5FF,1,0,0,0,100,100,1,0,3,22,0,5,40,40,0,1",
       "Style: Lbl,Inter Black,88,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,1,0,0,0,100,100,0,0,1,0,6,7,40,40,0,1",
       "Style: Tag,Inter Black,44,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,6,0,3,12,0,5,40,40,0,1",
       "Style: AI,Inter Black,150,&H00FFFFFF,&H00FFFFFF,&H003C3CE6,&H003C3CE6,1,0,0,0,100,100,6,0,3,24,0,5,40,40,0,1",
       "Style: REAL,Inter Black,150,&H00FFFFFF,&H00FFFFFF,&H0050B428,&H0050B428,1,0,0,0,100,100,6,0,3,24,0,5,40,40,0,1",
       "Style: Tell,Inter Bold,56,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,1,0,0,0,100,100,0,0,1,0,6,5,60,60,0,1",
       "Style: Big,Inter Black,110,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,1,0,0,0,100,100,0,0,1,0,8,5,40,40,0,1",
       "Style: Small,Inter SemiBold,48,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,0,5,5,60,60,0,1",
       "Style: Bar,Arial,20,&H00FFFFFF,&H00FFFFFF,&HFFFFFFFF,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
       "Style: BarBg,Arial,20,&HA0000000,&HA0000000,&HFFFFFFFF,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
E = lambda L, a, b, st, txt: ass.append(f"Dialogue: {L},{ts(a)},{ts(b)},{st},,0,0,0,,{txt}")
CX, MID = W // 2, HH + DIV // 2
CY = {'top': HH // 2, 'bottom': HH + DIV + HH // 2}
STAMP = r"\fscx190\fscy190\frz-8\t(0,170,\fscx100\fscy100)"

t = 0.0
hk = S['hook']; r0 = S['rounds'][0]
for side in ('top', 'bottom'):
    add_play(side, r0[side]['clip'], r0[side]['start'], hk['dur'])
E(5, 0, hk['dur'], 'Band', f"{{\\pos({CX},{MID})}}" + r"\N".join(hk['lines']))
t = hk['dur']
for ri, r in enumerate(S['rounds']):
    P, T, R = r['play'], r['think'], r['reveal']
    off = hk['dur'] if ri == 0 else 0.0  # round 1 continues the hook footage
    for side in ('top', 'bottom'):
        c = r[side]
        add_play(side, c['clip'], c['start'] + off, P)
        add_freeze(side, c['clip'], c['start'] + off + P - 0.05, T)
        if c.get('ai') and 'tell_start' in c:
            add_play(side, c['clip'], c['tell_start'], R, c.get('tell_speed', 1.0))
        else:
            add_play(side, c['clip'], c['start'] + off + P, R)
    a_play, a_think, a_rev, a_end = t, t + P, t + P + T, t + P + T + R
    E(3, a_play, a_rev, 'Tag', f"{{\\pos({CX},{MID})}}ROUND {ri + 1}/{len(S['rounds'])}")
    for side, letter in (('top', 'A'), ('bottom', 'B')):
        y0 = 40 if side == 'top' else HH + DIV + 40
        E(3, a_play, a_end, 'Lbl', f"{{\\pos(48,{y0})}}{letter}")
    E(5, a_think, a_rev, 'Q', f"{{\\pos({CX},{MID})\\fscx85\\fscy85\\t(0,150,\\fscx100\\fscy100)}}WHICH ONE IS AI?")
    bw, bh, bx, by = 520, 12, CX - 260, MID + 80
    E(4, a_think, a_rev, 'BarBg', f"{{\\pos({bx},{by})\\an7\\p1}}m 0 0 l {bw} 0 {bw} {bh} 0 {bh}")
    E(5, a_think, a_rev, 'Bar', f"{{\\pos({bx},{by})\\an7\\t(0,{int(T * 1000)},\\fscx0)\\p1}}m 0 0 l {bw} 0 {bw} {bh} 0 {bh}")
    for side in ('top', 'bottom'):
        st = 'AI' if r[side].get('ai') else 'REAL'
        sy = 120 if side == 'top' else HH + DIV + 120
        E(5, a_rev, a_end, st, f"{{\\pos({W - 230},{sy})\\fs110{STAMP}}}{st}")
        if r[side].get('ai'):
            E(5, a_rev + 0.3, a_end, 'Tell', f"{{\\pos({CX},{CY[side] + 170})\\fad(150,0)}}" + r"\N".join(r['tell']))
    t = a_end
en = S['end']; rl = S['rounds'][0]
for side in ('top', 'bottom'):
    add_play(side, rl[side]['clip'], rl[side]['start'], en['dur'])
E(5, t, t + en['dur'], 'Big', f"{{\\pos({CX},{MID - 60})\\fad(200,0)}}" + r"\N".join(en['lines']))
E(5, t + 0.3, t + en['dur'], 'Small', f"{{\\pos({CX},{MID + 140})\\fad(200,0)}}{en['sub']}")
total = t + en['dur']
(proj / 'out').mkdir(exist_ok=True)
(proj / 'out' / 'whichai.ass').write_text('\n'.join(ass) + '\n')

for side in ('top', 'bottom'):
    fc.append(''.join(pieces[side]) + f"concat=n={len(pieces[side])}:v=1:a=0[{side}]")
fc.append(f"[top]pad={W}:{HH + DIV}:0:0:white[tp];[tp][bottom]vstack,scale={W}:{H},setsar=1,eq=contrast=1.04,"
          f"ass={proj / 'out' / 'whichai.ass'}[vout]")
M = S['music']
cmd += ['-ss', str(M.get('start', 0)), '-i', str(proj / M['file'])]
fc.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total},asetpts=PTS-STARTPTS,"
          f"volume={M.get('vol', 0.9)},afade=t=in:d=0.3,afade=t=out:st={total - 1.0:.2f}:d=1.0,loudnorm=I=-14:TP=-2[aout]")
cmd += ['-filter_complex', ';'.join(fc), '-map', '[vout]', '-map', '[aout]',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', str(FPS),
        '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-t', f'{total:.2f}', str(proj / S['out'])]
subprocess.run(cmd, check=True)
print('rendered', proj / S['out'], f'{total:.2f}s')
