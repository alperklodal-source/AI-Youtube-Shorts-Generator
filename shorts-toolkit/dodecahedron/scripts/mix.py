import json, numpy as np, soundfile as sf
sr=48000; OFF=0.15
nar,nsr=sf.read('/home/user/short-dodeca/audio/cb_a.wav')
meta=json.load(open('/home/user/short-dodeca/audio/cb_a.json'))
# resample narration 24k->48k (linear is fine for speech at this ratio)
nar=np.interp(np.arange(0,len(nar)*sr/nsr)/ (sr/nsr), np.arange(len(nar)), nar)
dur=meta['duration']+OFF+1.0; N=int(dur*sr); tt=np.arange(N)/sr
rng=np.random.default_rng(7)
def lp(x,a):  # one-pole lowpass
    y=np.empty_like(x); acc=0.0
    for i in range(len(x)): acc+=a*(x[i]-acc); y[i]=acc
    return y
# drone: A1 + E2 + A2 with slow beating, plus low wind
drone=sum(np.sin(2*np.pi*f*tt+p)*a for f,a,p in [(55,.5,0),(55.4,.35,1),(82.4,.22,2),(110,.12,.5),(164.8,.05,1.3)])
drone*=0.6+0.4*np.sin(2*np.pi*tt/9.0)**2
wind=lp(rng.standard_normal(N),0.02); wind/=np.abs(wind).max()
wind*=0.5+0.5*np.sin(2*np.pi*tt/6.5+1)
bed=0.13*drone/np.abs(drone).max()+0.09*wind
bed*=np.clip(tt/1.2,0,1)*np.clip((dur-tt)/1.5,0,1)
fx=np.zeros(N)
def add(at,sig):
    i=int(at*sr); fx[i:i+len(sig)]+=sig[:max(0,N-i)]
def boom(L=2.5,f0=48):
    x=np.arange(int(L*sr))/sr; f=f0*np.exp(-x*1.2)
    return np.sin(2*np.pi*np.cumsum(f)/sr)*np.exp(-x*2.2)*0.55
def whoosh(L=0.8):
    x=np.arange(int(L*sr))/sr; n=lp(rng.standard_normal(len(x)),0.12)
    env=np.sin(np.pi*x/L)**2; return n/np.abs(n).max()*env*0.18
def ting(f=1800):  # coin glint
    x=np.arange(int(0.6*sr))/sr
    return (np.sin(2*np.pi*f*x)+0.5*np.sin(2*np.pi*f*2.76*x))*np.exp(-x*9)*0.08
S=meta['segments']
add(0.0,boom())
for k in [1,3,4,5,7,8]: add(S[k]['start']+OFF-0.6, whoosh())
add(S[2]['end']+OFF-1.4, boom(2.0,60))
add(S[6]['start']+OFF, boom(2.0,55))
add(S[8]['start']+OFF, boom(3.0,42))
voice=np.zeros(N); i=int(OFF*sr); voice[i:i+len(nar)]=nar[:N-i]
voice=voice/np.abs(voice).max()*0.85
# duck bed under speech
env=lp(np.abs(voice),0.0008); env/=env.max()
mix=voice+bed*(1-0.45*env)+fx
mix/=max(1.0,np.abs(mix).max()/0.97)
sf.write('/home/user/short-dodeca/audio/mix_raw.wav',mix,sr)
print('ok',round(dur,2))
