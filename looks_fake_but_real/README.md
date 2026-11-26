# Places That Look Fake But Are Real

~13 s, full-screen, rendered with `../guess_the_place/render_short.py PROJECT`.

Structure: 3-shot teaser hook ("LOOKS FAKE?" → "IT'S REAL.") while Brian says "These places look fake. But they're real."
→ orchestral drop lands on place 1 → 3 places × 2 shots, each with "N · COUNTRY" label and one short, verified line
→ "WHICH ONE WOULD YOU VISIT? 1, 2 OR 3?" over the opening shot (seamless loop), music swells after the voice.

Pick places whose footage actually shows the "fake-looking" thing (e.g. Uyuni stock clips were dry, no mirror → swapped
for Moraine Lake). Verify every line (UNESCO: Wulingyuan >3,000 pillars; Moraine Lake colour = glacial rock flour).
Find the music drop with librosa onsets/RMS and set `music.start` so it hits the first place.
