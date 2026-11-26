import sys, json
from faster_whisper import WhisperModel
m = WhisperModel('small.en', device='cpu', compute_type='int8')
for f in sys.argv[1:]:
    import soundfile as sf, torch, torchaudio
    a, sr = sf.read(f, dtype="float32")
    a = a.mean(1) if a.ndim > 1 else a
    a = torchaudio.functional.resample(torch.from_numpy(a), sr, 16000).numpy()
    segs, _ = m.transcribe(a, word_timestamps=True, language='en')
    words = [dict(w=w.word.strip(), s=round(w.start, 2), e=round(w.end, 2)) for s in segs for w in s.words]
    json.dump(words, open(f.replace('.wav', '.words.json'), 'w'))
    print(f, ' '.join(w['w'] for w in words))
