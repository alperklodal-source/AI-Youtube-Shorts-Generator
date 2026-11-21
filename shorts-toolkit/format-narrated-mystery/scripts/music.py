# Original procedural cinematic score, synced to the narration segments.
import json, numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve
sr = 48000; OFF = 0.15
S = json.load(open('/home/user/short-lycurgus/audio/nar.json'))['segments']
dur = S[-1]['end'] + OFF + 1.2; N = int(dur * sr); T = np.arange(N) / sr
rng = np.random.default_rng(3)
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, f): return sosfilt(butter(2, f, 'low', fs=sr, output='sos'), x)
def hp(x, f): return sosfilt(butter(2, f, 'high', fs=sr, output='sos'), x)
def env_adsr(n, a, r):
    e = np.ones(n); a = min(int(a*sr), n); r = min(int(r*sr), n - a)
    e[:a] = np.linspace(0, 1, a); e[n-r:] = np.linspace(1, 0, r); return e
def saw(f, n, det=0.0):
    t = np.arange(n) / sr; ph = (f * (1 + det)) * t + rng.random()
    return 2 * (ph % 1) - 1
s = lambda k: S[k]['start'] + OFF   # segment start
# scene markers
A0, B0, IT, WHO, C0, D0, BRK, E0, END = 0, s(1), S[2]['end']+OFF-1.4, s(3), s(4), s(5), s(6), s(7), s(8)
# A-minor harmonic progression; each chord lasts 3.0 s (80 bpm, 4/4)
prog = [[57,60,64],[53,57,60],[50,53,57],[52,56,59]]   # Am F Dm E
bass = [45, 41, 38, 40]
BAR = 3.0
pad = np.zeros(N); bas = np.zeros(N); puls = np.zeros(N); arp = np.zeros(N); bell = np.zeros(N); hits = np.zeros(N)
nb = int(np.ceil(dur / BAR))
for b in range(nb):
    t0 = b * BAR; i0 = int(t0 * sr); n = int(BAR * sr) + int(0.8 * sr); n = min(n, N - i0)
    if n <= 0: break
    ch = prog[b % 4]
    # strings pad: detuned saws, soft attack
    x = sum(saw(mtof(m), n, d) for m in ch for d in (-0.004, 0.0, 0.005)) / 9
    pad[i0:i0+n] += x * env_adsr(n, 1.2, 0.9)
    # low bass: sine + sub
    tt = np.arange(n) / sr; f = mtof(bass[b % 4])
    bas[i0:i0+n] += (np.sin(2*np.pi*f*tt) + 0.5*np.sin(2*np.pi*f/2*tt)) * env_adsr(n, 0.6, 0.9)
    # pulsing staccato eighths on the root (tension section)
    for k in range(8):
        tk = t0 + k * BAR / 8; ik = int(tk * sr); L = int(0.16 * sr)
        if ik + L >= N: break
        tl = np.arange(L) / sr
        puls[ik:ik+L] += saw(mtof(bass[b % 4] + 12), L) * np.exp(-tl * 22) * (1.0 if k % 2 == 0 else 0.7)
    # plucked arpeggio (16ths) up the chord + octave
    notes = ch + [ch[0] + 12]
    for k in range(16):
        tk = t0 + k * BAR / 16; ik = int(tk * sr); L = int(0.5 * sr)
        if ik + L >= N: break
        tl = np.arange(L) / sr; fq = mtof(notes[k % 4] + 12)
        arp[ik:ik+L] += (np.sin(2*np.pi*fq*tl) + 0.3*np.sin(2*np.pi*2*fq*tl)) * np.exp(-tl * 9)
# bell motif (E5 C5 A4 B4) at hook and outro
def bellnote(t, m, a=1.0):
    i = int(t * sr); L = min(int(3 * sr), N - i); tl = np.arange(L) / sr; f = mtof(m)
    bell[i:i+L] += a * (np.sin(2*np.pi*f*tl) + 0.4*np.sin(2*np.pi*2.76*f*tl)*np.exp(-tl*3) + 0.2*np.sin(2*np.pi*5.4*f*tl)*np.exp(-tl*6)) * np.exp(-tl * 1.6)
for j, m in enumerate([76, 72, 69, 71]):
    bellnote(0.35 + j * 0.75, m, 0.9)
for j, m in enumerate([76, 72, 69, 68]):
    bellnote(END + j * 0.6, m, 0.8)
# impacts
def hit(t, a=1.0, L=2.8):
    i = int(t * sr); L = min(int(L * sr), N - i); tl = np.arange(L) / sr
    f = 55 * np.exp(-tl * 1.5) + 30
    hits[i:i+L] += a * (np.sin(2*np.pi*np.cumsum(f)/sr) * np.exp(-tl * 2.0) + 0.25 * lp(rng.standard_normal(L), 900) * np.exp(-tl * 6))
hit(0.0, 1.0); hit(IT, 0.8); hit(BRK, 1.1); hit(END, 1.0, 3.5)
# riser into the theories section
Lr = int(3.0 * sr); ir = int(D0 * sr) - Lr
rs = hp(rng.standard_normal(Lr), 2000) * np.linspace(0, 1, Lr) ** 2
hits[ir:ir+Lr] += 0.25 * rs
# --- arrangement automation (layer volumes per scene) ---
def auto(points):
    ts, vs = zip(*points); return np.interp(T, ts, vs)
g_pad  = auto([(0,.0),(0.8,.5),(B0,.55),(C0,.6),(D0,.7),(BRK,.75),(E0,.35),(END,.55),(dur-1.5,.45),(dur,0)])
g_bass = auto([(0,.0),(1.0,.5),(B0,.6),(D0,.8),(BRK,.9),(E0,.3),(END,.6),(dur,0)])
g_puls = auto([(0,0),(B0-0.1,0),(B0+0.5,.35),(C0,.45),(D0,.6),(BRK,.75),(E0-0.1,.75),(E0+0.2,0),(dur,0)])
g_arp  = auto([(0,0),(C0-0.1,0),(C0+0.8,.22),(D0,.28),(BRK,.32),(E0,0),(END,.0),(dur,0)])
mix = (lp(pad, 2200) * g_pad * 0.5 + lp(bas, 400) * g_bass * 0.6 + lp(puls, 1400) * g_puls * 0.5
       + lp(arp, 5000) * g_arp * 0.35 + bell * 0.22 + hits * 0.55)
# simple hall reverb: exponentially decaying noise IR (stereo)
L = int(2.6 * sr); tl = np.arange(L) / sr
out = []
for ch in range(2):
    ir_ = rng.standard_normal(L) * np.exp(-tl * 2.4); ir_ = lp(ir_, 6000); ir_ /= np.sqrt((ir_**2).sum())
    wet = fftconvolve(mix, ir_)[:N]
    out.append(0.75 * mix + 0.45 * wet)
st = np.stack(out, 1); st /= np.abs(st).max() / 0.9
sf.write('/home/user/short-lycurgus/audio/music.wav', st, sr)
print('music', round(dur, 2))
