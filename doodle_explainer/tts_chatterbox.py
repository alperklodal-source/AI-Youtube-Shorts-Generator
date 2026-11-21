"""Batch TTS with Chatterbox Multilingual (run inside the venv that has torch).

usage: python tts_chatterbox.py job.json
job.json = {"texts": [...], "wavs": [...], "lang": "tr", "exaggeration": 0.7,
            "cfg_weight": 0.4, "temperature": 0.8, "voice_ref": "optional/ref.wav", "seed": 1}
"""
import json
import sys

import torch
import torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

job = json.load(open(sys.argv[1], encoding="utf-8"))
model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
kw = dict(language_id=job.get("lang", "tr"), exaggeration=job.get("exaggeration", 0.7),
          cfg_weight=job.get("cfg_weight", 0.4), temperature=job.get("temperature", 0.8))
if job.get("voice_ref"):
    kw["audio_prompt_path"] = job["voice_ref"]
seeds = job.get("seeds") or [job.get("seed", 1)] * len(job["texts"])
for i, (txt, out, seed) in enumerate(zip(job["texts"], job["wavs"], seeds)):
    print(f"[chatterbox] {i + 1}/{len(job['texts'])} seed={seed}: {txt[:50]}", flush=True)
    torch.manual_seed(seed)
    wav = model.generate(txt, **kw)
    ta.save(out, wav, model.sr)
