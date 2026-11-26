# Would You Rather – split-screen travel Shorts

"You can only live in ONE of these places, forever." Top half = A, bottom half = B (real stock video on both).

1. Clips: `../guess_the_place/search.py` + `fetch.py` (Pixabay, Coverr, Mixkit). Pick strong contrast (cold vs tropical, city vs nature). Skip AI-generated or mislabeled footage.
2. Voice: `../guess_the_place/brian.py audio/brian.wav "You can only live in one of these places. Forever. Snowy Norway, or the Maldives?" +6%` then `words.py`.
3. Music: cinematic strings from Pixabay Music (OpenMontage `pixabay_music`). Find the drop with librosa (RMS jump + beat grid) and set `music.start` so the drop lands right after the narration (`drop_at`, ~5 s).
4. Cut both halves together every 2 beats after the drop; end on the opening shots (seamless loop).
5. Render: `render_split.py PROJECT` → 1080×1920, labels "A · …" / "B · …", centre band texts, "A OR B?" CTA.
