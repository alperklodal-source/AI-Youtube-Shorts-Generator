"""Render a 'Would you rather live here or here?' split-screen Short from PROJECT/spec.json.

spec = {
  "voice": "audio/brian.wav", "voice_delay": 0.25,
  "music": {"file": "...mp3", "start": 35.18, "pre_vol": 0.35, "post_vol": 1.0, "drop_at": 5.0},
  "segments": [{"end": 2.63, "top": ["clips/a.mp4", 0], "bottom": ["clips/b.mp4", 0]}, ...],
  "labels": {"at": 3.45, "top": "A · NORWAY", "bottom": "B · MALDIVES"},
  "texts": [{"at": 0.25, "end": 2.55, "text": "YOU CAN ONLY LIVE IN ONE", "style": "Band"}, ...],
  "out": "out/short.mp4"
}
"""
import json, subprocess, sys
from pathlib import Path

W, H, FPS, DIV = 1080, 1920, 30, 6
HH = (H - DIV) // 2  # height of each half
proj = Path(sys.argv[1]).resolve()
S = json.load(open(proj / 'spec.json'))
segs = S['segments']
total = segs[-1]['end']


def ts(t):
    m, s = divmod(max(t, 0), 60)
    return f"0:{int(m):02d}:{s:05.2f}"


# ---------- overlays (ASS) ----------
ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       # white text on a black box, centred on the divider
       "Style: Band,Inter Black,66,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,1,0,3,18,0,5,40,40,0,1",
       "Style: Big,Inter Black,150,&H0000E5FF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,10,4,5,40,40,0,1",
       "Style: Label,Inter Black,58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,1,0,0,0,100,100,2,0,1,6,3,7,48,48,0,1",
       "Style: Sub,Inter SemiBold,40,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,0,0,0,0,100,100,1,0,1,4,2,7,48,48,0,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
cy = HH + DIV // 2
for t in S.get('texts', []):
    st = t.get('style', 'Band')
    fx = r"\fscx70\fscy70\t(0,160,\fscx104\fscy104)\t(160,280,\fscx100\fscy100)" if t.get('pop') else r"\fad(80,0)"
    ass.append(f"Dialogue: 3,{ts(t['at'])},{ts(t.get('end', total))},{st},,0,0,0,,{{\\pos({W // 2},{t.get('y', cy)}){fx}}}{t['text']}")
L = S.get('labels')
if L:
    for key, y in (('top', 60), ('bottom', HH + DIV + 60)):
        ass.append(f"Dialogue: 2,{ts(L['at'])},{ts(L.get('end', total))},Label,,0,0,0,,{{\\pos(48,{y})\\fad(150,0)}}{L[key]}")
        if L.get(key + '_sub'):
            ass.append(f"Dialogue: 2,{ts(L['at'])},{ts(L.get('end', total))},Sub,,0,0,0,,{{\\pos(48,{y + 74})\\fad(150,0)}}{L[key + '_sub']}")
(proj / 'out').mkdir(exist_ok=True)
(proj / 'out' / 'overlay.ass').write_text('\n'.join(ass) + '\n')

# ---------- video ----------
cmd, fc, n, t0 = ['ffmpeg', '-v', 'error', '-y'], [], 0, 0.0
for k, sg in enumerate(segs):
    dur = sg['end'] - t0
    for side in ('top', 'bottom'):
        clip, start = sg[side]
        cmd += ['-ss', str(start), '-t', f'{dur + 0.1:.3f}', '-i', str(proj / clip)]
        fc.append(f"[{n}:v]fps={FPS},scale={W}:{HH}:force_original_aspect_ratio=increase,crop={W}:{HH},setsar=1,"
                  f"trim=duration={dur:.3f},setpts=PTS-STARTPTS[{side[0]}{k}]")
        n += 1
    fc.append(f"[t{k}]pad={W}:{HH + DIV}:0:0:white[tp{k}];[tp{k}][b{k}]vstack[s{k}]")
    t0 = sg['end']
fc.append(''.join(f"[s{k}]" for k in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=0,"
          "eq=contrast=1.07:saturation=1.15,vignette=angle=PI/6,"
          f"ass={proj / 'out' / 'overlay.ass'}[vout]")
# ---------- audio ----------
VD = S.get('voice_delay', 0)
cmd += ['-i', str(proj / S['voice'])]
fc.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-2,"
          f"adelay={int(VD * 1000)}:all=1,apad,atrim=0:{total}[voice]")
M = S['music']
cmd += ['-ss', str(M['start']), '-i', str(proj / M['file'])]
d, pre, post = M['drop_at'], M.get('pre_vol', 0.35), M.get('post_vol', 1.0)
fc.append(f"[{n + 1}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total},asetpts=PTS-STARTPTS,"
          f"volume='if(lt(t,{d - 0.15}),{pre},{post})':eval=frame,afade=t=in:d=0.4,"
          f"afade=t=out:st={total - 1.2}:d=1.2[mus]")
fc.append("[voice][mus]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.89[aout]")
cmd += ['-filter_complex', ';'.join(fc), '-map', '[vout]', '-map', '[aout]',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', str(FPS),
        '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-t', f'{total:.3f}', str(proj / S['out'])]
subprocess.run(cmd, check=True)
print('rendered', proj / S['out'], f'{total:.2f}s')
