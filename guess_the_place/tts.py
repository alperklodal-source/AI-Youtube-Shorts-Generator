"""tts.py OUT.wav "text" "instruct" speed [ref.wav "ref text"] — OmniVoice on CPU."""
import sys
sys.path.insert(0, '/home/user/VoiceStudio')
from omnivoice.cli.infer import main
out, text, instruct, speed = sys.argv[1:5]
args = ['x', '--model', 'k2-fsa/OmniVoice', '--text', text, '--language', 'en', '--output', out, '--device', 'cpu', '--speed', speed]
if len(sys.argv) > 6: args += ['--ref_audio', sys.argv[5], '--ref_text', sys.argv[6]]
else: args += ['--instruct', instruct]
sys.argv = args; main()
