# REAL or AI? – play → freeze → answer + the tell (3 rounds, ~24 s)

Ground truth: Pixabay uploaders tag AI clips "ai generated" (search e.g. "ai generated animal"); for REAL use old
uploads (low ids, pre-2023) — ideally ones that *look* AI (glowing jellyfish). Pick AI clips that look real and
find a tell you can SHOW: sample frames every 0.5 s with timestamps, look for morphing ears, objects/limbs/tattoos
appearing, people/animals spawning. Never claim a tell you can't point at.

Segments: `play` (optionally `full: true` = whole frame over a blurred fill so the tell isn't cropped away,
`speed` < 1 for slow-mo), `freeze` (slow push-in), `split` (two zoomed stills, e.g. 0.3 s vs 2.5 s).
Texts: ROUND n/3 tag, "REAL or AI?" on the freeze, tilted AI/REAL stamp, the tell, end "how many did you get?".
Don't play the part containing the tell before the freeze. Render: `render_roa.py PROJECT`.

Thinking time: user feedback "answers come too fast" → freezes are 3.2 s with a draining bar (`timers`).

## Which one is AI? (split screen) — `render_whichai.py`
A (top) / B (bottom): same subject, one real (old Pixabay upload) and one AI (tagged). Rounds: play → freeze
"WHICH ONE IS AI?" + 3.2 s draining bar → reveal (AI half replays its tell, optionally slowed via `tell_start`/
`tell_speed`) with corner stamps AI / REAL and a one-line tell; ends on round-1 footage for the loop. A truly
identical-scene AI twin would need a video generator, which this toolset doesn't include.

## v2 (preferred by the user over the split-screen variant) — `examples/real_or_ai_02.spec.json`
Breathing room between rounds: 0.9 s "ROUND n" card on the next clip's first frame. Landscape clips: `full: true`
plus a `crop` around the subject (tight crop on the tell for the reveal). Per-segment `vf` (e.g. brighten dark aurora).
Synthesized SFX (no licensing): clock ticks every 0.5 s during thinking time, low hit + chime on each stamp;
limiter + headroom → ≈ −15 LUFS, −1.7 dBTP.
Self-check rubric (aim ≥ 90): hook 15 · thinking time 10 · tell visibility 20 · accuracy 15 · pacing 10 ·
visual quality 10 · ending/CTA/loop 10 · audio 10.

## v3 feedback (wild animals) — `examples/real_or_ai_03_wild.spec.json`
User: AI clips were too obvious; drop "ROUND n" labels/cards. Now: recent (id > 290 000) photoreal AI clips only,
one theme per video (wild animals / faces / nature / city-tech), no round labels — a 0.45 s fade-in between rounds,
reveal crop zoomed onto the tell (shark fin → spear, two polar bears → one head), REAL round = an old 4K clip that
looks "too perfect".

## Near-identical twins (user: "side by side, so close it's hard to tell") — `examples/which_one_is_ai_02_twins.spec.json`
Take one frame of a real clip (at the clip's start time) and turn it into video with DepthFlow's depth model
(`df_drift.py`: slow push-in + gentle drift; `DF_STRENGTH` 0.3 for static shots, 1.0 for drone shots), rendered at
1080×958 so it lines up with the real half. Both halves start on the same frame → near-identical.
Tell = nothing in the scene is alive (balloons don't drift, water sparkle frozen, fog doesn't move).
`render_whichai.py`: `round_tags: false`, fade between rounds, tick/hit SFX, boxed tell text. Description states
honestly that the AI half was generated from a single frame.
