import json, numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt
sr = 48000; OFF = 0.15
nar, nsr = sf.read('/home/user/short-dodeca/audio/ch_s21.wav')
nar = np.interp(np.arange(0, len(nar) * sr / nsr) / (sr / nsr), np.arange(len(nar)), nar)
mus, _ = sf.read('/home/user/short-dodeca/audio/music.wav'); N = len(mus)
v = np.zeros(N); i = int(OFF * sr); v[i:i+len(nar)] = nar[:N-i]
# voice polish: gentle high-pass + presence lift
v = sosfilt(butter(2, 80, 'high', fs=sr, output='sos'), v)
pres = sosfilt(butter(2, [2500, 5000], 'band', fs=sr, output='sos'), v); v = v + 0.25 * pres
v /= np.abs(v).max() / 0.9
# sidechain ducking: smoothed voice envelope (fast attack, slow release)
a = np.abs(v); env = np.zeros(N); acc = 0.0
att, rel = 1 - np.exp(-1 / (0.01 * sr)), 1 - np.exp(-1 / (0.35 * sr))
for k in range(0, N, 48):                       # 1 ms steps for speed
    x = a[k:k+48].max(); acc += (att if x > acc else rel) * 48 * (x - acc) if False else 0
env_blocks = np.array([a[k:k+480].max() for k in range(0, N, 480)])   # 10 ms blocks
sm = np.zeros_like(env_blocks); acc = 0.0
for j, x in enumerate(env_blocks):
    acc = acc + (0.6 if x > acc else 0.035) * (x - acc); sm[j] = acc
env = np.repeat(sm, 480)[:N]; env /= env.max()
duck = 1 - 0.62 * np.clip(env * 1.6, 0, 1)        # about -8 dB under speech
music_gain = 0.42
out = np.stack([v, v], 1) * 0.95 + mus * (music_gain * duck)[:, None]
out /= max(1.0, np.abs(out).max() / 0.97)
sf.write('/home/user/short-dodeca/audio/mix_raw.wav', out, sr)
print('ok', round(N / sr, 2))
