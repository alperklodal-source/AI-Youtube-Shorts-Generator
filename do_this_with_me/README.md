# Do This With Me – guided wellness Shorts (~20–25 s)

Niche picked for retention: wellness had the highest average % viewed on Shorts (Q2 2026, EMARKETER / Dash Social).
The viewer *does* the exercise with the video, so they stay to the end and save it.

Each video = a different, evidence-based technique (avoid YouTube's "inauthentic / repetitive" template risk):
physiological sigh (Balban et al. 2023, Cell Reports Medicine), box breathing, 4-7-8, 5-4-3-2-1 grounding, 20-20-20 eyes.

Build:
1. Voice cues, one wav each: `../guess_the_place/brian.py audio/pN.wav "In through your nose." -12%`, then trim silence
   (`ffmpeg -af silenceremove…,areverse,silenceremove…,areverse`) so cues land exactly on phase starts.
2. Calm footage, 1–2 long shots (fade between).
3. `render_breath.py PROJECT` – translucent circle (ASS vector drawing) animates to each phase's `scale`;
   label inside; hook text at the start, "better? / save this…" at the end. Description carries the source + a
   "not medical advice" line.

## v2 (current): text-only + relaxing music — `render_breath2.py`
User feedback on v1: looked amateur and viewers didn't understand it. v2 drops the voice and explains everything on
screen: hook ("feeling anxious?" → "try this 20-second breathing trick") → "HOW IT WORKS" 3-step card →
exercise with big instruction + sub-line, countdown inside the circle, per-phase progress bar, "ROUND 1 OF 2", technique
name at top → "how do you feel now? / save this…". Calm crossfaded footage (sea of fog, ocean), darkened + vignette,
soft piano from Pixabay Music baked in (~30 s total). Example: `examples/physiological_sigh_v2.spec.json`.
