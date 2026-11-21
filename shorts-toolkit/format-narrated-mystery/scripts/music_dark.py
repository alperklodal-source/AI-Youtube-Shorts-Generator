# Original dark-ambient bed, hits locked to the narration's word timings.
import json, numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve
sr = 48000; rng = np.random.default_rng(9)
W = json.load(open('/home/user/short-lycurgus/video/src/words.json'))
dur = W[-1][1] + 1.6; N = int(dur * sr); T = np.arange(N) / sr
def lp(x, f): return sosfilt(butter(2, f, 'low', fs=sr, output='sos'), x)
def hp(x, f): return sosfilt(butter(2, f, 'high', fs=sr, output='sos'), x)
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], 'band', fs=sr, output='sos'), x)
def word(prefix, after=0.0):
    for a, b, w in W:
        if w.lower().strip('.,?!…').startswith(prefix) and a > after: return a
    return None
FLIP = word('again') + 0.35
GOLD = word('gold'); HUMAN = word('human'); NANO = word('nanotech', 20)
PUNCH = next(a for a, b, w in W if a > NANO + 0.3 and w.lower().startswith('in'))
OUTRO = word('genius'); END = W[-1][1]
# 1. drone: C#1/G#1/C#2 with slow beating, through a slowly sweeping low-pass
f0 = 34.65
drone = sum(a * np.sin(2*np.pi*f*T + p) for f, a, p in [(f0, .6, 0), (f0*1.003, .5, 1), (f0*1.5, .32, 2), (f0*2, .22, .5), (f0*2.997, .1, 1.7)])
sweep = 120 + 260 * (0.5 + 0.5*np.sin(2*np.pi*T/11.0))
dr = np.zeros(N); blk = 4800
for i in range(0, N, blk):
    dr[i:i+blk] = lp(drone[max(0, i-blk):i+blk], float(sweep[i]))[-len(drone[i:i+blk]):]
dr *= np.clip(T/2.0, 0, 1)
# 2. glass harmonica: soft sines that swell (glass theme), C# minor colours
glass = np.zeros(N)
for k, (t0, m) in enumerate([(0.3, 73), (6.0, 76), (11.5, 80), (16.6, 75), (22.0, 78), (28.1, 73), (OUTRO - 0.3, 80)]):
    f = 440 * 2 ** ((m - 69) / 12); i0 = int(t0 * sr); L = min(int(6.5 * sr), N - i0); tl = np.arange(L) / sr
    env = np.sin(np.pi * np.clip(tl / 6.5, 0, 1)) ** 2
    glass[i0:i0+L] += (np.sin(2*np.pi*f*tl) + 0.35*np.sin(2*np.pi*2.01*f*tl) + 0.12*np.sin(2*np.pi*3.02*f*tl)) * env * (1 + 0.004*np.sin(2*np.pi*5*tl))
# 3. air / wind texture
air = bp(rng.standard_normal(N), 300, 2400); air /= np.abs(air).max()
air *= 0.5 + 0.5 * np.sin(2*np.pi*T/7.3 + 1) ** 2
# 4. hits: sub boom + reversed swell into it
fx = np.zeros(N)
def add(at, sig):
    i = int(at * sr); 
    if i < 0: sig = sig[-i:]; i = 0
    fx[i:i+len(sig)] += sig[:max(0, N-i)]
def boom(L=3.0, f=42, g=0.9):
    x = np.arange(int(L*sr))/sr; fr = f*np.exp(-x*0.8)
    return np.sin(2*np.pi*np.cumsum(fr)/sr) * np.exp(-x*1.6) * g
def riser(L=1.2, g=0.35):
    x = np.arange(int(L*sr))/sr; n = bp(rng.standard_normal(len(x)), 500, 6000)
    return n/np.abs(n).max() * (x/L)**3 * g
for at, g in [(FLIP, 1.0), (GOLD, 0.45), (HUMAN, 0.4), (PUNCH, 0.85), (OUTRO, 0.7)]:
    add(at - 1.2, riser(g=0.3*g)); add(at, boom(g=g))
# 5. low heartbeat pulse under the science section
pulse = np.zeros(N)
for t0 in np.arange(GOLD - 0.5, PUNCH, 1.1):
    add_i = int(t0*sr); L = int(0.35*sr); x = np.arange(L)/sr
    pulse[add_i:add_i+L] += np.sin(2*np.pi*55*x) * np.exp(-x*14) * 0.35
mix = 0.55*dr + 0.07*glass + 0.05*air + pulse + fx
# long synthetic reverb on everything but the sub
ir_n = int(3.5*sr); t_ir = np.arange(ir_n)/sr
ir = rng.standard_normal(ir_n) * np.exp(-t_ir/0.9); ir = lp(ir, 5000); ir /= np.abs(ir).sum() ** 0.5 * 6
wet = fftconvolve(0.07*glass + 0.05*air + 0.3*fx, ir)[:N]
L = mix + wet; R = mix + np.roll(wet, int(0.013*sr))
st = np.stack([L, R], 1); st = hp(st.T, 25).T
st *= np.clip((dur - T)/1.5, 0, 1)[:, None]
st /= np.abs(st).max() / 0.9
sf.write('/home/user/short-lycurgus/audio/music.wav', st, sr); print('dark', round(dur, 2), 'flip', round(FLIP, 2), 'punch', round(PUNCH, 2), 'outro', round(OUTRO, 2))
