"""Batch Turkish TTS with VoxCPM2 + a designed voice (run inside the torch venv).

Approach borrowed from github.com/alexturkey/voxcpm2-turkce-ses-tasarimi (Apache-2.0):
  1. a voice is *designed* once from an English description ("(description)text"),
  2. every later line is read with that design recording as both prompt and
     reference plus a fixed seed, so the voice never drifts between scenes,
  3. digits and quotes never reach the model; a small pronunciation dictionary
     fixes abbreviations.
Numbers/dates/percentages are spelled out with normalizer-tr (the text frontend
used by github.com/canberk7/ema-lightning).

usage: python tts_voxcpm.py job.json
job.json = {"texts": [...], "wavs": [...], "seeds": [...], "voice_dir": ".../voices/eglenceli_anlatici",
            "okunus": {"ABD": "Amerika"}, "timesteps": 10, "cfg": 2.0}
"""
import json
import os
import re
import sys

import soundfile as sf
import torch
from normalizer_tr import Normalizer
from voxcpm import VoxCPM

QUOTES = re.compile("[\"“”„«»‘’‚‹›`´']")


def spoken(text, okunus, norm):
    for k in sorted(okunus, key=len, reverse=True):
        text = re.sub(rf"(?<![\wçğıöşüÇĞİÖŞÜ]){re.escape(k)}(?![\wçğıöşüÇĞİÖŞÜ])", okunus[k], text, flags=re.I)
    text = norm.normalize(text, ambiguity_policy="fallback").normalized_text
    text = QUOTES.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


job = json.load(open(sys.argv[1], encoding="utf-8"))
torch.set_num_threads(os.cpu_count() or 4)
voice = json.load(open(os.path.join(job["voice_dir"], "ses.json"), encoding="utf-8"))
ref = os.path.join(job["voice_dir"], voice["referans"])
okunus = {**voice.get("okunus", {}), **job.get("okunus", {})}
norm = Normalizer()
model = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False, device="cpu")
sr = model.tts_model.sample_rate
seeds = job.get("seeds") or [voice.get("okuma_tohumu", 1)] * len(job["texts"])
for i, (txt, out, seed) in enumerate(zip(job["texts"], job["wavs"], seeds)):
    say = spoken(txt, okunus, norm)
    print(f"[voxcpm] {i + 1}/{len(job['texts'])} seed={seed}: {say[:60]}", flush=True)
    torch.manual_seed(seed)
    wav = model.generate(text=say, prompt_wav_path=ref, prompt_text=voice["referans_metni"], reference_wav_path=ref,
                         cfg_value=job.get("cfg", 2.0), inference_timesteps=job.get("timesteps", 10))
    sf.write(out, wav, sr)
