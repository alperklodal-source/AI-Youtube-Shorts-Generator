"""compact.py IN.wav OUT.wav [max_gap=0.22] — shorten pauses between sentences (uses IN.words.json)."""
import sys, json, numpy as np, soundfile as sf
src, dst = sys.argv[1], sys.argv[2]
gap = float(sys.argv[3]) if len(sys.argv) > 3 else 0.22
a, sr = sf.read(src, dtype='float32')
words = json.load(open(src.replace('.wav', '.words.json')))
pieces, out_words, cursor, shift = [], [], 0.0, 0.0
for i, w in enumerate(words):
    if i and w['s'] - words[i - 1]['e'] > gap:           # long pause: cut it down
        cut_from = words[i - 1]['e'] + gap / 2
        cut_to = w['s'] - gap / 2
        pieces.append(a[int(cursor * sr):int(cut_from * sr)])
        shift += cut_to - cut_from; cursor = cut_to
    out_words.append(dict(w=w['w'], s=round(w['s'] - shift, 2), e=round(w['e'] - shift, 2)))
end = min(len(a) / sr, words[-1]['e'] + 0.25)
pieces.append(a[int(cursor * sr):int(end * sr)])
y = np.concatenate(pieces)
fade = int(0.008 * sr)  # tiny fades at joins are unnecessary for cuts inside silence; keep tail fade
y[-fade:] *= np.linspace(1, 0, fade)
sf.write(dst, y, sr)
json.dump(out_words, open(dst.replace('.wav', '.words.json'), 'w'))
print(f'{len(a)/sr:.2f}s -> {len(y)/sr:.2f}s')
