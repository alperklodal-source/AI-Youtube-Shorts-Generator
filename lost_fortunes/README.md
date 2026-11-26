# Lost fortunes ("he lost millions with this mistake") – 12 s, cloned narrator voice, EN + TR

1. Verify the story (e.g. Howells v Newport City Council [2025] EWHC 22 (Ch): 8,000 BTC drive in landfill, dig refused).
2. Narration in the creator's own cloned voice: `clone.py out.wav "text" en|tr 1.15 ref.wav "ref transcript"`
   (OmniVoice; ref = clean 10–15 s of the creator, transcript verified with Whisper). The reference recording is
   personal data: keep it local, never commit it.
3. `words2.py out.wav en|tr` → `compact.py` (pauses ≤0.22 s) → trim lead silence + atempo ≤1.15 to fit 11.5 s.
4. `render_short.py PROJECT` with `captions_until: 0` (boxed Montserrat overlays instead of word captions),
   `style_override`, `fonts`, music ducked under the voice.
