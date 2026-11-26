"""'REAL or AI?' Short: play -> freeze ("REAL or AI?") -> reveal stamp + the tell.

Segments (in order):
  {"type": "play",   "clip": c, "start": s, "dur": d, "speed": 1.0, "crop": [x, y, w, h]?}
  {"type": "freeze", "clip": c, "at": s, "dur": d}
  {"type": "split",  "clip": c, "at": [s1, s2], "crop": [x, y, w, h], "dur": d}   # two zoomed stills stacked
crop values are fractions of the source frame. Text is ASS events in "texts" (style + absolute times).
"""
import json, subprocess, sys
from pathlib import Path

W, H, FPS = 1080, 1920, 30
proj = Path(sys.argv[1]).resolve()
S = json.load(open(proj / 'spec.json'))
segs = S['segments']
total = sum(s['dur'] for s in segs)


def ts(t):
    m, s = divmod(max(t, 0), 60)
    return f"0:{int(m):02d}:{s:05.2f}"


def cropf(c):
    if not c:
        return ''
    x, y, w, h = c
    return f"crop=iw*{w}:ih*{h}:iw*{x}:ih*{y},"


def fit(w, h):
    return f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1"


cmd, fc, n = ['ffmpeg', '-v', 'error', '-y'], [], 0
for k, s in enumerate(segs):
    clip = str(proj / s['clip'])
    if s['type'] == 'play':
        sp = s.get('speed', 1.0)
        cmd += ['-ss', str(s['start']), '-t', f"{s['dur'] * sp + 0.2:.2f}", '-i', clip]
        if s.get('full'):  # whole frame visible: sharp, width-fitted over a blurred fill
            fc.append(f"[{n}:v]{cropf(s.get('crop'))}setpts=(PTS-STARTPTS)/{sp},fps={FPS},trim=duration={s['dur']},setpts=PTS-STARTPTS,"
                      f"split[a{k}][b{k}];[a{k}]{fit(W, H)},boxblur=30:2,eq=brightness=-0.15[bg{k}];"
                      f"[b{k}]scale={W}:-2,setsar=1[fg{k}];[bg{k}][fg{k}]overlay=0:(H-h)/2[s{k}]")
        else:
            fc.append(f"[{n}:v]{cropf(s.get('crop'))}{fit(W, H)},setpts=(PTS-STARTPTS)/{sp},fps={FPS},"
                      f"trim=duration={s['dur']},setpts=PTS-STARTPTS{(',' + s['vf']) if s.get('vf') else ''}[s{k}]")
        n += 1
    elif s['type'] == 'freeze':
        cmd += ['-ss', str(s['at']), '-i', clip]
        if s.get('full'):
            fc.append(f"[{n}:v]trim=end_frame=1,{cropf(s.get('crop'))}loop=loop=-1:size=1,fps={FPS},trim=duration={s['dur']},setpts=PTS-STARTPTS,"
                      f"split[a{k}][b{k}];[a{k}]{fit(W, H)},boxblur=30:2,eq=brightness=-0.15[bg{k}];"
                      f"[b{k}]scale={W}:-2,setsar=1[fg{k}];[bg{k}][fg{k}]overlay=0:(H-h)/2[s{k}]")
        else:
            fc.append(f"[{n}:v]trim=end_frame=1,{cropf(s.get('crop'))}{fit(W, H)},loop=loop=-1:size=1,fps={FPS},"
                      f"trim=duration={s['dur']},setpts=PTS-STARTPTS,"
                      f"zoompan=z='min(1+0.03*on/{FPS},1.06)':d=1:s={W}x{H}:fps={FPS}[s{k}]")
        n += 1
    elif s['type'] == 'split':
        parts = []
        for j, a in enumerate(s['at']):
            cmd += ['-ss', str(a), '-i', clip]
            fc.append(f"[{n}:v]trim=end_frame=1,{cropf(s.get('crop'))}{fit(W, H // 2 - 4)},loop=loop=-1:size=1,"
                      f"fps={FPS},trim=duration={s['dur']},setpts=PTS-STARTPTS[p{k}_{j}]")
            parts.append(f"[p{k}_{j}]")
            n += 1
        fc.append(f"[p{k}_0]pad={W}:{H // 2 + 4}:0:0:white[pt{k}];[pt{k}][p{k}_1]vstack,scale={W}:{H},setsar=1[s{k}]")
fc.append(''.join(f"[s{k}]" for k in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=0,"
          "eq=contrast=1.04,vignette=angle=PI/5,"
          f"ass={proj / 'out' / 'roa.ass'}[vout]")

ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Big,Inter Black,120,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,1,0,0,0,100,100,0,0,1,0,8,5,40,40,0,1",
       "Style: Q,Inter Black,104,&H0000E5FF,&H00FFFFFF,&H00000000,&H90000000,1,0,0,0,100,100,0,0,1,0,8,5,40,40,0,1",
       "Style: Tag,Inter Black,46,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,6,0,3,14,0,5,40,40,0,1",
       "Style: AI,Inter Black,170,&H00FFFFFF,&H00FFFFFF,&H003C3CE6,&H003C3CE6,1,0,0,0,100,100,6,0,3,26,0,5,40,40,0,1",
       "Style: REAL,Inter Black,170,&H00FFFFFF,&H00FFFFFF,&H0050B428,&H0050B428,1,0,0,0,100,100,6,0,3,26,0,5,40,40,0,1",
       "Style: Tell,Inter Bold,60,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,1,0,0,0,100,100,0,0,1,0,6,5,70,70,0,1",
       "Style: Bar,Arial,20,&H00FFFFFF,&H00FFFFFF,&HFFFFFFFF,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
       "Style: BarBg,Arial,20,&HB0FFFFFF,&HB0FFFFFF,&HFFFFFFFF,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
       "Style: Small,Inter SemiBold,48,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,0,5,5,60,60,0,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
BW, BH = 600, 14
for b in S.get('timers', []):  # draining "thinking time" bar under the question
    a, e = b['at'], b['end']; ms = int((e - a) * 1000); x0, y = W // 2 - BW // 2, b.get('y', 1130)
    ass.append(f"Dialogue: 3,{ts(a)},{ts(e)},BarBg,,0,0,0,,{{\\pos({x0},{y})\\an7\\p1}}m 0 0 l {BW} 0 {BW} {BH} 0 {BH}")
    ass.append(f"Dialogue: 4,{ts(a)},{ts(e)},Bar,,0,0,0,,{{\\pos({x0},{y})\\an7\\t(0,{ms},\\fscx0)\\p1}}m 0 0 l {BW} 0 {BW} {BH} 0 {BH}")
for t in S['texts']:
    fx = t.get('fx', r"\fad(120,120)")
    if t.get('stamp'):
        fx = r"\fscx180\fscy180\frz-8\t(0,160,\fscx100\fscy100)"
    ass.append(f"Dialogue: {t.get('layer', 3)},{ts(t['at'])},{ts(t['end'])},{t['style']},,0,0,0,,"
               f"{{\\pos({W // 2},{t.get('y', 960)}){fx}}}" + r"\N".join(t['lines']))
(proj / 'out').mkdir(exist_ok=True)
(proj / 'out' / 'roa.ass').write_text('\n'.join(ass) + '\n')

M = S['music']
cmd += ['-ss', str(M.get('start', 0)), '-i', str(proj / M['file'])]
fc.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total},asetpts=PTS-STARTPTS,"
          f"volume={M.get('vol', 0.9)},afade=t=in:d=0.3,afade=t=out:st={total - 1.0:.2f}:d=1.0,loudnorm=I=-14:TP=-2[aout]")
# ---- synthesized SFX (no licensing): clock ticks during thinking time, a hit + chime on each stamp ----
sfx = []
for b in S.get('timers', []):
    k_ = 0
    while b['at'] + k_ * 0.5 < b['end'] - 0.05:
        sfx.append(('tick', b['at'] + k_ * 0.5)); k_ += 1
for t_ in S['texts']:
    if t_.get('stamp'):
        sfx.append(('hit', t_['at']))
if sfx:
    expr = {'tick': "0.55*sin(2*PI*1800*t)*exp(-90*t)",
            'hit': "0.9*sin(2*PI*55*t)*exp(-7*t)+0.35*sin(2*PI*880*t)*exp(-6*t)+0.2*sin(2*PI*1320*t)*exp(-8*t)"}
    dur = {'tick': 0.08, 'hit': 0.9}
    names = []
    for i, (kind, at) in enumerate(sfx):
        cmd += ['-f', 'lavfi', '-i', f"aevalsrc='{expr[kind]}':s=48000:d={dur[kind]}"]
        fc.append(f"[{n + 1 + i}:a]aformat=channel_layouts=stereo,adelay={int(at * 1000)}:all=1[fx{i}]")
        names.append(f"[fx{i}]")
    fc[-len(sfx) - 1] = fc[-len(sfx) - 1].replace('[aout]', '[mus]')
    fc.append('[mus]' + ''.join(names) + f"amix=inputs={len(sfx) + 1}:normalize=0:duration=first,alimiter=limit=0.8,volume=-2dB[aout]")
cmd += ['-filter_complex', ';'.join(fc), '-map', '[vout]', '-map', '[aout]',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', str(FPS),
        '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-t', f'{total:.2f}', str(proj / S['out'])]
subprocess.run(cmd, check=True)
print('rendered', proj / S['out'], f'{total:.2f}s')
