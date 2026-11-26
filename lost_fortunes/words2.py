import sys, json, soundfile as sf, torch, torchaudio
from faster_whisper import WhisperModel
f, lang = sys.argv[1], sys.argv[2]
m = WhisperModel('small', device='cpu', compute_type='int8')
a, sr = sf.read(f, dtype='float32'); a = a.mean(1) if a.ndim > 1 else a
a = torchaudio.functional.resample(torch.from_numpy(a), sr, 16000).numpy()
segs, _ = m.transcribe(a, word_timestamps=True, language=lang)
w = [dict(w=x.word.strip(), s=round(x.start, 2), e=round(x.end, 2)) for s in segs for x in s.words]
json.dump(w, open(f.replace('.wav', '.words.json'), 'w'), ensure_ascii=False)
print(f, ' '.join(f"{x['w']}@{x['s']}" for x in w))
