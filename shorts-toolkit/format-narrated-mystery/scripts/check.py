import sys, numpy as np, soundfile as sf
from faster_whisper import WhisperModel
m = WhisperModel("base.en", device="cpu", compute_type="int8")
for f in sys.argv[1:]:
    y, sr = sf.read(f); y = y if y.ndim == 1 else y.mean(1)
    # crude expressiveness: pitch (autocorrelation) std in semitones + loudness dynamics
    fr = int(0.04*sr); hop = int(0.02*sr); f0=[]; rms=[]
    for i in range(0, len(y)-fr, hop):
        w = y[i:i+fr]; r = np.sqrt((w**2).mean()); rms.append(r)
        if r < 0.02: continue
        ac = np.correlate(w, w, 'full')[fr-1:]; lo, hi = int(sr/300), int(sr/70)
        k = lo + np.argmax(ac[lo:hi])
        if ac[k] > 0.3*ac[0]: f0.append(sr/k)
    f0 = np.array(f0); st = 12*np.log2(f0/np.median(f0))
    rms = np.array(rms); rms = rms[rms > 0.02]
    y16 = np.interp(np.arange(0, len(y), sr/16000), np.arange(len(y)), y).astype(np.float32)
    segs, _ = m.transcribe(y16, language="en")
    txt = " ".join(s.text.strip() for s in segs)
    print(f"{f.split('/')[-1]}: pitch-range {np.percentile(st,95)-np.percentile(st,5):.1f} st | loudness-var {20*np.log10(np.percentile(rms,95)/np.percentile(rms,10)):.1f} dB | {len(y)/sr:.1f}s\n  {txt}\n")
