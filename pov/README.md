# POV aesthetic Shorts

One line of lowercase text ("pov: you left everything / for a cabin in the snow"), then 8–10 real stock clips
(~1.3–2.2 s each) that tell a tiny story (walk into the forest → snowy cabin → fireplace & hot drink → northern lights).
No narration, no music: silent track, the user adds a trending sound (e.g. "Snowfall") in the YouTube Shorts editor.
Render with `../guess_the_place/render_short.py PROJECT`.

Footage QA: reject illustrations, CGI renders and AI-looking "cozy ambience" loops (many recent ~50 s Pixabay
uploads), and clips whose vertical centre-crop loses the subject.

Contrast variant (`examples/pov_left_the_city.spec.json`): 6 fast city shots (0.6–0.8 s, desaturated/cool via per-shot
`vf`) → 5 slow nature shots (~2 s, warm). Text in the lower third so it never covers faces.
Music via the YouTube Shorts library is licensed: no claim, video stays monetised; YouTube routes half of that Short's
creator-pool revenue (one track) to music partners, the creator's 45 % share is unchanged.
