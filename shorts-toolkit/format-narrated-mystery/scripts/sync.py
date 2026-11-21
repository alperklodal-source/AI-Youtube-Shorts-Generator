# Re-sync word-locked beats in Short.tsx to the narration (whisper word timestamps).
import numpy as np, soundfile as sf, json, re
from faster_whisper import WhisperModel
y,sr=sf.read('audio/nar.wav'); y=y if y.ndim==1 else y.mean(1)
y16=np.interp(np.arange(0,len(y),sr/16000),np.arange(len(y)),y).astype(np.float32)
m=WhisperModel('small',device='cpu',compute_type='int8')
segs,_=m.transcribe(y16,language='en',word_timestamps=True)
W=[(w.start+0.15,w.end+0.15,re.sub(r'[^a-z]','',w.word.lower())) for s in segs for w in s.words]
def find(word, after=0):
    for a,b,w in W:
        if w==word and a>after: return a,b
    raise SystemExit('missing '+word)
gold=find('gold')[0]; silver=find('silver')[0]; part=find('particles',gold); thou=find('thousand',gold)[0]
a_t=[a for a,b,w in W if w=='a' and part[1]<a<thou][-1]
thinner=find('thinner',gold)[0]; than=find('than',thinner)[0]; human=find('human',gold)[0]
light=find('light',human)[0]; smaller=find('smaller',light)[0]
V=dict(GOLD=gold,SIL=silver,PUSH=part[0],NM=part[1]-0.1,OUT=a_t,CNT_END=than-0.1,HAIR_IN=than-0.23,HAIR_FULL=human-0.03,HUMAN=human,GONE=light-0.18,
       FIELD_A=part[0]+0.12,FIELD_B=part[0]+0.62,HERO=part[0]+0.32,CNTF_A=human-0.25,CNTF_B=human-0.07,E2=light-0.05,SMALLER=smaller)
V={k:round(float(v),2) for k,v in V.items()}; print(V)
p='video/src/Short.tsx'; s=open(p).read()
s=re.sub(r"const GOLD_AT = at\([^;]*;", f"const GOLD_AT = at({V['GOLD']}), SIL_AT = at({V['SIL']}), PUSH = at({V['PUSH']}), NM = at({V['NM']}), OUT = at({V['OUT']}), CNT_END = at({V['CNT_END']}), HAIR_IN = at({V['HAIR_IN']}), HAIR_FULL = at({V['HAIR_FULL']}), HUMAN = at({V['HUMAN']}), GONE = at({V['GONE']});", s)
s=re.sub(r"const field = interpolate\(f, \[at\([0-9.]+\), at\([0-9.]+\)\]", f"const field = interpolate(f, [at({V['FIELD_A']}), at({V['FIELD_B']})]", s)
s=re.sub(r"const heroShown = f >= at\([0-9.]+\);", f"const heroShown = f >= at({V['HERO']});", s)
s=re.sub(r"\[OUT, OUT \+ 4, at\([0-9.]+\), at\([0-9.]+\)\]", f"[OUT, OUT + 4, at({V['CNTF_A']}), at({V['CNTF_B']})]", s)
s=re.sub(r"<Tag text=\{f < at\([0-9.]+\) \?", f"<Tag text={{f < at({V['HERO']}) ?", s)
s=re.sub(r"const E2 = Math.round\([0-9.]+ \* FPS\);", f"const E2 = Math.round({V['E2']} * FPS);", s)
s=re.sub(r"const SMALLER = Math.round\([0-9.]+ \* FPS\) - G;", f"const SMALLER = Math.round({V['SMALLER']} * FPS) - G;", s)
open(p,'w').write(s)
