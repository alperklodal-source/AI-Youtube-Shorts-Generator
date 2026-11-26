"""brian.py OUT.wav "text" [rate] [voice] — Microsoft edge-tts (channel voice: en-US-BrianNeural)."""
import sys, ssl, asyncio, subprocess, os
import edge_tts.communicate as c
ca = '/root/.ccr/ca-bundle.crt'
if os.path.exists(ca):  # sandbox proxy CA (no-op elsewhere)
    c._SSL_CTX = ssl.create_default_context(cafile=ca)
out, text = sys.argv[1], sys.argv[2]
rate = sys.argv[3] if len(sys.argv) > 3 else '+8%'
voice = sys.argv[4] if len(sys.argv) > 4 else 'en-US-BrianNeural'
mp3 = out.rsplit('.', 1)[0] + '.mp3'
asyncio.run(c.Communicate(text, voice, rate=rate).save(mp3))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', mp3, '-ar', '24000', '-ac', '1', out], check=True)
print('saved', out)
