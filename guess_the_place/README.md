# Guess the Place – 9–10 s Shorts pipeline

Global English channel. Every shot is a real stock video clip (no stills).

| Step | Script | Tool |
|---|---|---|
| 1. Find clips | `search.py "faroe islands"` | OpenMontage stock sources: Pixabay, Coverr, Mixkit (NASA/Wikimedia optional) |
| 2. Download chosen ids | `fetch.py PROJECT/clips "query" ID...` | writes `credits.json` |
| 3. Narration | `tts.py out.wav "text" "male, middle-aged, low pitch, american accent" 1.1 [ref.wav "ref text"]` | OmniVoice (VoiceStudio) – voice design or cloning |
| 4. Word timings | `words.py audio/v1.wav` | faster-whisper `small.en` |
| 5. Render | `render_short.py PROJECT` (reads `PROJECT/spec.json`) | ffmpeg + libass, 1080×1920 30 fps, -14 LUFS |

Format: hook (0–2.5 s) → hint → silent 3-2-1 countdown → reveal title → one verified fact. See `examples/`.

Setup (paths assumed by the scripts): OpenMontage at `/home/user/tools/OpenMontage` (`make setup`, keys in its git-ignored `.env`:
`PIXABAY_API_KEY`, `COVERR_API_KEY`), VoiceStudio at `/home/user/VoiceStudio`, a venv at `/home/user/tools/voice-env`
with `torch torchaudio transformers>=5.10 accelerate pydub soundfile psutil huggingface_hub faster-whisper`.
Never commit API keys.
