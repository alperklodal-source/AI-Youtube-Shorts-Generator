import sys, json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
voice, speed, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
lines = [
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
gaps = [0.3,0.25,0.2,0.3,0.25,0.15,0.3,0.35,0.0]
k = Kokoro("/home/user/short-dodeca/models/kokoro-v1.0.onnx","/home/user/short-dodeca/models/voices-v1.0.bin")
audio=[]; t=0.0; segs=[]; sr=24000
for line,g in zip(lines,gaps):
    s,sr = k.create(line, voice=voice, speed=speed, lang="en-us" if voice.startswith("a") else "en-gb")
    # trim leading/trailing silence
    idx=np.where(np.abs(s)>0.01)[0]; s=s[max(idx[0]-240,0):idx[-1]+480]
    segs.append({"text":line,"start":round(t,3),"end":round(t+len(s)/sr,3)})
    audio.append(s); t+=len(s)/sr
    audio.append(np.zeros(int(g*sr),dtype=s.dtype)); t+=g
sf.write(out+".wav", np.concatenate(audio), sr)
json.dump({"duration":t,"segments":segs}, open(out+".json","w"), indent=1)
print(voice, round(t,2))
