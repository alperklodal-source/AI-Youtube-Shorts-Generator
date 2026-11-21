# So The Story Goes — Shorts production playbook (for Claude)

Channel: **So The Story Goes** (history / mystery, English). Owner speaks Turkish: talk to them in Turkish,
write video scripts/titles in English. Ask before producing anything big; show options with honest scores.

## Quality bar (always)
- Have a "Short maker" reviewer (a sub-agent you brief with the virality criteria below) score every
  script, hook, scene cut and cover. Script/overall **> 86**, visuals and cover **≥ 90**. Iterate until met.
- Virality criteria: hook (payoff visible within ~1.5 s), retention (no dead seconds, word-synced visuals),
  payoff/revelation, comment bait (end on a two-sided question), factual safety (hedge anything uncertain).
- Never claim a score that wasn't given; never fake numbers.

## Format A — narrated mystery object (Roman dodecahedron, Lycurgus Cup) → `format-narrated-mystery/`
1. Topic: a real ancient object/technology with a visual "wow" and an open question.
2. Script: 8–10 short TTS-friendly lines, ~30–38 s. Numbers that TTS misreads → words ("sixteen hundred").
   Hook pattern that worked: question + instant visual contradiction ("What colour is this cup? Green? Look again." → snaps red).
3. Visuals: real photos/footage from Wikimedia Commons (prefer CC0/PD; record credits), labelled
   "ILLUSTRATION" motion graphics for science beats (Remotion). Captions 1–3 words, gold keywords, y≈1430.
4. Voice: Chatterbox TTS voice clone of the channel reference (`scripts/cb_tts.py ex cfg out seed ref lines.json`).
   - Calm/serious, stable accent: `exaggeration 0.4–0.45, cfg 0.5–0.55`. Energetic hook: `0.6, 0.4`.
   - Generate 3 seeds, transcribe with faster-whisper (`scripts/check.py`), keep the take with an exact transcript.
   - Do NOT speed up with atempo (sounds robotic). Resample with `scipy.signal.resample_poly` (linear interp crackles).
   - Re-record single lines and splice; emphasise a phrase by generating it alone with higher exaggeration.
5. Sync: `scripts/sync.py` reads whisper word times and rewrites the word-locked beat constants in `Short.tsx`;
   captions come from `src/words.json` (whisper word timestamps). Fix mis-heard caption words by hand.
6. Music (under narration, sidechain-ducked ~ -10 dB, music ~ -6 dB below voice; final -14 LUFS, TP -1.5):
   original procedural score (`music.py`), original dark ambient with hits on key words (`music_dark.py`),
   or public-domain recordings (Musopen on Commons: Beethoven Moonlight Sonata / Paul Pitman, Chopin Nocturne 20 /
   Frank Lévy, Mendelssohn 3 Adagio). Start the cut exactly on the first note (detect onsets with librosa).
7. Cover: `src/Cover.tsx` — same object split green|red (photos feature-aligned with OpenCV SIFT + homography),
   2–4 huge words, text kept in the middle 80% and above the feed's title overlay.

## Format B — music montage (First Spark) → `format-music-montage/` (see STYLE.md there)
No narration; Wan 2.1 opening scene (Kaggle T4) → maths/light burst → beat-cut archive montage → symbolic ending.

## Tooling notes
- Remotion 4.0.484: `npx remotion render src/index.ts Short out/x.mp4 --gl=angle` (+ `--browser-executable` if needed).
- Wan 2.1 T2V 1.3B on Kaggle free GPU: notebooks in `format-music-montage/wan/`; 480×832, 81 frames ≈ 39 min/seed on T4.
  `kaggle_cli_wrapper.py` was for a proxy environment — in a normal setup use the regular Kaggle CLI with your own token.
- Wikimedia: use standard thumb sizes (1280/1920); transcoded video/audio URLs (`/transcoded/.../File.720p.vp9.webm`, `.mp3`)
  dodge rate limits; back off on HTTP 429.

## YouTube lessons
- Shorts app music: only tracks under **"Official music"** are licensed. "Slowed"/user remixes → worldwide Content ID block.
  The Shorts editor can't start a song mid-video; if you need a silent pre-roll, embed royalty-free/PD music yourself.
- Public-domain classical recordings can still get false Content ID matches → dispute with the Musopen/Commons source link.
- Category: Education. Disclose AI-generated realistic scenes ("Altered or synthetic content").
- Title/description translations: YouTube Studio (desktop) → Subtitles → Add language → Title & description.
