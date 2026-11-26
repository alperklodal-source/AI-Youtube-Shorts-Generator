# Guess the Place – 9–10 s Shorts pipeline

Global English channel. Every shot is a real stock video clip (no stills).

| Step | Script | Tool |
|---|---|---|
| 1. Find clips | `search.py "faroe islands"` | OpenMontage stock sources: Pixabay, Coverr, Mixkit (NASA/Wikimedia optional) |
| 2. Download chosen ids | `fetch.py PROJECT/clips "query" ID...` | writes `credits.json` |
| 3. Narration | `brian.py audio/brian.wav "text"` (channel voice: edge-tts `en-US-BrianNeural`, rate +8%) | alt: `tts.py` = OmniVoice (VoiceStudio) voice design / cloning |
| 4. Word timings | `words.py audio/brian.wav` then `compact.py audio/brian.wav audio/brianc.wav 0.28` (cut long pauses) | faster-whisper `small.en` |
| 5. Render | `render_short.py PROJECT` (reads `PROJECT/spec.json`) | ffmpeg + libass, 1080×1920 30 fps, -14 LUFS |

Format (retention-first): ~0.8 s landscape intro + ambient music (Pixabay Music via OpenMontage `pixabay_music`,
ducked under the voice) with "GUESS THE PLACE" on screen from frame 0 → hook ("Only one percent can guess this place")
→ three clues, hardest to easiest, no "hint" word, no countdown → ANSWER LAST (pop title) → ends on the opening
shot so the loop is seamless. Cut every ~1–1.5 s, pauses ≤0.3 s, total ≤10 s. See `examples/`.

Setup (paths assumed by the scripts): OpenMontage at `/home/user/tools/OpenMontage` (`make setup`, keys in its git-ignored `.env`:
`PIXABAY_API_KEY`, `COVERR_API_KEY`), VoiceStudio at `/home/user/VoiceStudio`, a venv at `/home/user/tools/voice-env`
with `torch torchaudio transformers>=5.10 accelerate pydub soundfile psutil huggingface_hub faster-whisper edge-tts`
(edge-tts needs `speech.platform.bing.com`).
Never commit API keys.
