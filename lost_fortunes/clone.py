"""clone.py OUT.wav "text" lang speed ref.wav "ref text" — OmniVoice voice cloning (CPU)."""
import sys
sys.path.insert(0, '/home/user/VoiceStudio')
from omnivoice.cli.infer import main
out, text, lang, speed, ref, reft = sys.argv[1:7]
sys.argv = ['x', '--model', 'k2-fsa/OmniVoice', '--text', text, '--language', lang, '--output', out,
            '--device', 'cpu', '--speed', speed, '--ref_audio', ref, '--ref_text', reft]
main()
