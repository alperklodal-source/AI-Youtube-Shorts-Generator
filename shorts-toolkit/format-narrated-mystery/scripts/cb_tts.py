import sys, json, numpy as np, torch, torchaudio as ta
from chatterbox.tts import ChatterboxTTS
ex, cfg, out = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
torch.manual_seed(int(sys.argv[4]) if len(sys.argv)>4 else 7)
_L = json.load(open(sys.argv[6]))
lines = _L["lines"]
_unused = [
 "This bronze Roman object is covered in mismatched holes... and nobody knows why.",
 "Over a hundred have been found, from Britain to Hungary.",
 "But here's the strange part... almost none were found in Italy.",
 "So who really made them?",
 "In 2023, a near-perfect one turned up in England... small enough to hold in one hand.",
 "A candle holder? Dice? A calendar for sowing wheat?",
 "Every theory breaks somewhere.",
 "And not one Roman text mentions it.",
 "What do you think it was... a tool, or a ritual?",
]
gaps = _L["gaps"]
m = ChatterboxTTS.from_pretrained(device="cpu")
sr = m.sr; audio=[]; t=0.0; segs=[]
for line,g in zip(lines,gaps):
    w = m.generate(line, audio_prompt_path=sys.argv[5] if len(sys.argv)>5 else "/home/user/short-dodeca/cb/ref_george.wav", exaggeration=ex, cfg_weight=cfg).squeeze(0).numpy()
    idx=np.where(np.abs(w)>0.01)[0]; w=w[max(idx[0]-240,0):idx[-1]+600]
    segs.append({"text":line,"start":round(t,3),"end":round(t+len(w)/sr,3)}); audio.append(w); t+=len(w)/sr
    audio.append(np.zeros(int(g*sr),dtype=w.dtype)); t+=g
    print(round(t,1), line[:30], flush=True)
ta.save(out+".wav", torch.from_numpy(np.concatenate(audio)).unsqueeze(0), sr)
json.dump({"duration":t,"segments":segs}, open(out+".json","w"), indent=1)
print("done", round(t,2))
