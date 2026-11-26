"""Render a guided 'Do this with me' breathing Short from PROJECT/spec.json.

A translucent circle in the middle grows on inhales and shrinks on exhales; a label sits inside it;
short voice cues (trimmed wavs) are placed at given times; calm footage plays behind.

spec = {
  "shots": [{"clip": "clips/a.mp4", "start": 0, "dur": 11.7}, ...],
  "phases": [{"t": 2.6, "dur": 2.0, "scale": 0.85, "label": "inhale"}, ...],   # circle animates to `scale`
  "base_scale": 0.42,
  "cues": [{"t": 0.2, "wav": "audio/t0.wav"}, ...],
  "texts": [{"at": 0.0, "end": 2.5, "lines": ["Feeling anxious?", "Breathe with me"]}, ...],
  "out": "out/x.mp4"
}
"""
import json, subprocess, sys
from pathlib import Path

W, H, FPS = 1080, 1920, 30
CX, CY, R = W // 2, 880, 330
proj = Path(sys.argv[1]).resolve()
S = json.load(open(proj / 'spec.json'))
total = sum(s['dur'] for s in S['shots'])


def ts(t):
    m, s = divmod(max(t, 0), 60)
    return f"0:{int(m):02d}:{s:05.2f}"


k = 0.5523 * R  # bezier circle
pts = lambda x, y: f"{x + R:.0f} {y + R:.0f}"  # shift into positive space so \an5 centres the shape
circle = (f"m {pts(0, -R)} b {pts(k, -R)} {pts(R, -k)} {pts(R, 0)} b {pts(R, k)} {pts(k, R)} {pts(0, R)} "
          f"b {pts(-k, R)} {pts(-R, k)} {pts(-R, 0)} b {pts(-R, -k)} {pts(-k, -R)} {pts(0, -R)}")
ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       # circle: white fill ~80% transparent, white outline ~25% transparent
       "Style: Ring,Arial,20,&HC8FFFFFF,&HC8FFFFFF,&H40FFFFFF,&H00000000,0,0,0,0,100,100,0,0,1,7,0,7,0,0,0,1",
       "Style: Label,Inter Bold,76,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,2,0,1,3,2,5,40,40,0,1",
       "Style: Head,Inter Black,78,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,1,0,0,0,100,100,0,0,1,6,3,5,60,60,0,1",
       "Style: Small,Inter SemiBold,46,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,0,0,0,0,100,100,0,0,1,4,2,5,70,70,0,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]

# one circle event per phase, animating from the previous scale to this phase's scale
prev = S.get('base_scale', 0.42)
phases = S['phases']
first, last = phases[0]['t'], phases[-1]['t'] + phases[-1]['dur']
ass.append(f"Dialogue: 0,{ts(first - 0.6)},{ts(first)},Ring,,0,0,0,,{{\\pos({CX},{CY})\\an5\\fad(400,0)"
           f"\\fscx{prev*100:.0f}\\fscy{prev*100:.0f}\\p1}}{circle}")
for i, p in enumerate(phases):
    a, b = prev * 100, p['scale'] * 100
    ms = int(p['dur'] * 1000)
    fade = r"\fad(0,500)" if i == len(phases) - 1 else ""
    ass.append(f"Dialogue: 0,{ts(p['t'])},{ts(p['t'] + p['dur'])},Ring,,0,0,0,,{{\\pos({CX},{CY})\\an5{fade}"
               f"\\fscx{a:.0f}\\fscy{a:.0f}\\t(0,{ms},0.8,\\fscx{b:.0f}\\fscy{b:.0f})\\p1}}{circle}")
    if p.get('label'):
        ass.append(f"Dialogue: 1,{ts(p['t'])},{ts(p['t'] + p['dur'])},Label,,0,0,0,,{{\\pos({CX},{CY})\\fad(150,150)}}{p['label']}")
    prev = p['scale']
for t in S.get('texts', []):
    st = t.get('style', 'Head')
    ass.append(f"Dialogue: 2,{ts(t['at'])},{ts(t['end'])},{st},,0,0,0,,{{\\pos({CX},{t.get('y', CY)})\\fad(250,250)}}"
               + r"\N".join(t['lines']))
(proj / 'out').mkdir(exist_ok=True)
(proj / 'out' / 'breath.ass').write_text('\n'.join(ass) + '\n')

cmd, fc = ['ffmpeg', '-v', 'error', '-y'], []
for i, s in enumerate(S['shots']):
    cmd += ['-ss', str(s['start']), '-t', f"{s['dur'] + 0.1:.2f}", '-i', str(proj / s['clip'])]
    fade_in = f",fade=t=in:st=0:d=0.6" if i else ""
    fc.append(f"[{i}:v]fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,"
              f"trim=duration={s['dur']},setpts=PTS-STARTPTS{fade_in}[v{i}]")
n = len(S['shots'])
fc.append(''.join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0,"
          "eq=brightness=-0.06:saturation=0.95,vignette=angle=PI/5,"
          f"ass={proj / 'out' / 'breath.ass'}[vout]")
cues = S.get('cues', [])
for c in cues:
    cmd += ['-i', str(proj / c['wav'])]
if cues:
    for j, c in enumerate(cues):
        fc.append(f"[{n + j}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(c['t'] * 1000)}:all=1[c{j}]")
    fc.append(''.join(f"[c{j}]" for j in range(len(cues))) +
              f"amix=inputs={len(cues)}:normalize=0,apad,atrim=0:{total},loudnorm=I=-16:TP=-2[aout]")
else:
    cmd += ['-f', 'lavfi', '-t', str(total), '-i', 'anullsrc=r=48000:cl=stereo']
    fc.append(f"[{n}:a]anull[aout]")
cmd += ['-filter_complex', ';'.join(fc), '-map', '[vout]', '-map', '[aout]',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', str(FPS),
        '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-t', f'{total:.2f}', str(proj / S['out'])]
subprocess.run(cmd, check=True)
print('rendered', proj / S['out'], f'{total:.2f}s')
