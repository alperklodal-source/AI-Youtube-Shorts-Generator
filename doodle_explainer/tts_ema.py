"""Batch Turkish TTS with EMA Lightning (https://github.com/canberk7/ema-lightning, Apache-2.0).

Runs inside the venv that has torch. Writes one wav per text plus a JSON file
with exact word timings (used for captions, no Whisper needed).

usage: python tts_ema.py job.json
job.json = {"texts": [...], "wavs": [...], "speed": 1.08, "seed": 1}
"""
import json
import sys

from ema_lightning import EMA

job = json.load(open(sys.argv[1], encoding="utf-8"))
tts = EMA()
timings = []
for i, (txt, out) in enumerate(zip(job["texts"], job["wavs"])):
    print(f"[ema] {i + 1}/{len(job['texts'])}: {txt[:50]}", flush=True)
    s = tts.say(txt, path=out, seed=job.get("seed", 1), speed=job.get("speed", 1.0), sample_rate=24000)
    timings.append([[w.text, float(w.start), float(w.end)] for w in s.words])
json.dump(timings, open(job["timings"], "w", encoding="utf-8"), ensure_ascii=False)
