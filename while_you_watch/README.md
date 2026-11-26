# While You Watch This – live counters tied to the viewer's watch time

Every number = rate × seconds since the video started (updated 10×/s), plus a "YOU'VE BEEN WATCHING 00:07.4s" HUD,
so the video measures the viewer. Ends with all totals still ticking: "and it's still happening." (seamless rewatch).
Rates used (verify per video): lightning ~44 flashes/s (NASA/NOAA), births ~4.2/s (UN WPP 2024), Earth orbit 29.8 km/s,
Sun ~4 Mt mass→energy/s (NASA), resting heart ~1.2 beats/s. Series ideas: "…in the ocean", "…in your body", "…online".
NASA clips: apply ../../tools/patches/openmontage-nasa-https.patch temporarily, cut the needed seconds, delete the
multi-GB originals. Render: `render_live.py PROJECT`.
