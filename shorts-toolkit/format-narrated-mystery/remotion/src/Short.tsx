import React from "react";
import { AbsoluteFill, Audio, Img, interpolate, spring, staticFile, useCurrentFrame, Easing, Sequence, random } from "remotion";
import narration from "./narration.json";
import words from "./words.json";

// Lycurgus Cup Short. Narration-driven (same format as the dodecahedron Short): real museum photos
// (Wikimedia Commons, CC0 / CC BY), motion graphics for the science, captions, original score.
const fontCss = `
@font-face{font-family:Cinzel;src:url(${staticFile("cinzel.woff2")}) format('woff2');font-weight:900}
@font-face{font-family:Mont;src:url(${staticFile("mont.woff2")}) format('woff2');font-weight:800}`;

const FPS = 30;
const OFF = 0.15;
const t = (s: number) => Math.round((s + OFF) * FPS);
const seg = narration.segments;
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const GOLD = "#e8b765", JADE = "#8fd3a8", RUBY = "#ff5a4a";

// ---------- captions: 1–3 word chunks ----------
type Chunk = { text: string; from: number; to: number; key: boolean };
const PUNCH = 28.13;   // "In the fourth century!"
const KEY = /(colour|look again|again|watch|blood|green|light|red|only|nobody|1990|microscope|gold|silver|thousand|hair|flips|nanoparticles|wild|nanotechnology|fourth|no roman|seen|smaller|wavelength|genius|accident)/i;
const chunks: Chunk[] = [];
// captions from the real word timings (whisper), 1–3 words per chunk, breaking on punctuation
{
  let cur: [number, number, string][] = [];
  const flush = () => { if (!cur.length) return; chunks.push({ text: cur.map((w) => w[2]).join(" ").replace(/\.\.\./g, "…"), from: Math.round(cur[0][0] * FPS), to: Math.round(cur[cur.length - 1][1] * FPS), key: KEY.test(cur.map((w) => w[2]).join(" ")) }); cur = []; };
  (words as [number, number, string][]).forEach((w) => { cur.push(w); if (cur.length === 3 || /[.,?!…]$/.test(w[2])) flush(); });
  flush();
}
const Captions: React.FC = () => {
  const f = useCurrentFrame();
  const c = chunks.find((x) => f >= x.from && f < x.to + 4);
  if (!c) return null;
  const p = spring({ frame: f - c.from, fps: FPS, config: { damping: 14, stiffness: 220 } });
  return (
    <div style={{ position: "absolute", top: 1430, width: "100%", textAlign: "center", padding: "0 90px", boxSizing: "border-box" }}>
      <span style={{ fontFamily: "Mont", fontWeight: 800, fontSize: 84, lineHeight: 1.1, textTransform: "uppercase", color: c.key ? GOLD : "#fff",
        display: "inline-block", transform: `scale(${0.85 + 0.15 * p})`, textShadow: "0 0 18px rgba(0,0,0,.95), 0 6px 0 rgba(0,0,0,.85)", WebkitTextStroke: "3px rgba(0,0,0,.6)" }}>{c.text}</span>
    </div>
  );
};

const Grain: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <svg width="1080" height="1920" style={{ position: "absolute", opacity: 0.08, mixBlendMode: "overlay" }}>
        <filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed={f % 12} /></filter>
        <rect width="100%" height="100%" filter="url(#n)" />
      </svg>
      <AbsoluteFill style={{ boxShadow: "inset 0 0 260px 90px #000" }} />
    </AbsoluteFill>
  );
};
const Flash: React.FC<{ at: number; color?: string; peak?: number }> = ({ at, color = "#fff3dc", peak = 0.55 }) => {
  const f = useCurrentFrame();
  return <AbsoluteFill style={{ background: color, opacity: interpolate(f, [at - 3, at, at + 7], [0, peak, 0], clamp), mixBlendMode: "screen" }} />;
};
const Label: React.FC<{ text: string; at: number; x: number; y: number; size?: number; color?: string }> = ({ text, at, x, y, size = 46, color = GOLD }) => {
  const f = useCurrentFrame();
  const o = interpolate(f, [at, at + 8], [0, 1], clamp);
  return <div style={{ position: "absolute", left: x, top: y, opacity: o, transform: `translateY(${(1 - o) * 20}px)`, fontFamily: "Cinzel", fontWeight: 900, fontSize: size,
    color, letterSpacing: 4, textShadow: `0 0 24px ${color}77, 0 4px 10px #000` }}>{text}</div>;
};
const Tag: React.FC<{ text: string }> = ({ text }) => (
  <div style={{ position: "absolute", top: 190, left: 70, fontFamily: "Mont", fontWeight: 800, fontSize: 28, letterSpacing: 4, color: "#cfc3ad", background: "rgba(0,0,0,.45)", padding: "8px 18px", borderLeft: "5px solid #888" }}>{text}</div>
);

// photo with slow push (colours kept true: the colour IS the story)
const Photo: React.FC<{ src: string; dur: number; from?: number; to?: number; origin?: string; filter?: string; shift?: string }> = ({ src, dur, from = 1.0, to = 1.12, origin = "50% 45%", filter = "contrast(1.08)", shift = "" }) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [0, dur], [0, 1], { ...clamp, easing: Easing.inOut(Easing.sin) });
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#000" }}>
      <Img src={staticFile(src)} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", transformOrigin: origin, transform: `${shift} scale(${from + (to - from) * p})`, filter }} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,.5) 0%, rgba(0,0,0,0) 22%, rgba(0,0,0,0) 58%, rgba(0,0,0,.8) 100%)" }} />
    </AbsoluteFill>
  );
};
// the green photo, shifted so its cup sits exactly on the red photo's cup (same side, two real photos)
const ALIGN = "translate(8px, -92px)";
const GreenImg: React.FC<{ style?: React.CSSProperties }> = ({ style }) => (
  <Img src={staticFile("c5_jade.jpg")} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", transform: ALIGN, ...style }} />
);
const RedImg: React.FC<{ style?: React.CSSProperties }> = ({ style }) => (
  <Img src={staticFile("c9_red.jpg")} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", ...style }} />
);
const Fade: React.FC<{ len: number; children: React.ReactNode }> = ({ len, children }) => {
  const f = useCurrentFrame();
  return <AbsoluteFill style={{ opacity: interpolate(f, [0, len], [0, 1], clamp) }}>{children}</AbsoluteFill>;
};

// hook: green cup; on "light" the light inside snaps on and it is red
const Reveal: React.FC<{ flips: number[]; dur: number }> = ({ flips, dur }) => {
  const f = useCurrentFrame();
  const punch = (p: number) => (f >= p ? 0.07 * Math.exp(-(f - p) / 5) : 0);
  const z = interpolate(f, [0, dur], [1.08, 1.28], clamp) * (1 + punch(0) + punch(flips[0]));
  const passed = flips.filter((x) => f >= x);
  const red = passed.length % 2 === 1 ? 1 : 0;
  const last = passed.length ? passed[passed.length - 1] : -100;
  const bloom = interpolate(f, [last, last + 2, last + 24], [0, 1, 0.3], clamp) * red;
  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden" }}>
      <AbsoluteFill style={{ transform: `scale(${z})`, transformOrigin: "52% 40%" }}>
        {red ? <RedImg /> : <GreenImg />}
        <AbsoluteFill style={{ mixBlendMode: "screen", opacity: bloom, background: "radial-gradient(ellipse at 52% 45%, rgba(255,110,80,.9) 0%, rgba(255,50,30,.45) 32%, rgba(0,0,0,0) 60%)" }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,.55) 0%, rgba(0,0,0,0) 22%, rgba(0,0,0,0) 58%, rgba(0,0,0,.8) 100%)" }} />
    </AbsoluteFill>
  );
};

// 2 → 3: one continuous move from the carved figure into the glass, which becomes a microscope image
const IntoGlass: React.FC<{ s2: number; dur: number }> = ({ s2, dur }) => {
  const f = useCurrentFrame();
  const push = f < s2 ? interpolate(f, [0, s2], [1.7, 1.45], { ...clamp, easing: Easing.inOut(Easing.sin) })
    : interpolate(f, [s2, s2 + 40], [1.45, 9], { ...clamp, easing: Easing.in(Easing.cubic) });
  const tem = interpolate(f, [s2 + 22, s2 + 40], [0, 1], clamp);
  const zt = interpolate(f, [s2 + 22, dur], [1.6, 1.0], { ...clamp, easing: Easing.out(Easing.cubic) });
  const scan = (f * 23) % 1920;
  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden" }}>
      <RedImg style={{ transformOrigin: "50% 36%", transform: `scale(${push})`, filter: "saturate(.85) contrast(1.05)" }} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,.5) 0%, rgba(0,0,0,0) 22%, rgba(0,0,0,0) 58%, rgba(0,0,0,.8) 100%)", opacity: 1 - tem }} />
      <AbsoluteFill style={{ opacity: tem }}>
        <AbsoluteFill style={{ transform: `scale(${zt})` }}><TEM /></AbsoluteFill>
        <div style={{ position: "absolute", left: 0, right: 0, top: scan, height: 3, background: "rgba(255,255,255,.18)" }} />
        <div style={{ position: "absolute", left: 120, top: 1260, width: 220, height: 10, background: "#f2f2ea" }} />
        <div style={{ position: "absolute", left: 120, top: 1205, fontFamily: "Mont", fontWeight: 800, fontSize: 40, color: "#f2f2ea" }}>100 nm</div>
        <Tag text="ILLUSTRATION · ELECTRON MICROSCOPE VIEW" />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
// transmission-electron-microscope look: grey-green field, dark round particles, circular vignette
const TEM: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 45%, #b9c2b4 0%, #8e978a 45%, #2b2f2a 72%, #000 80%)" }}>
      {Array.from({ length: 70 }).map((_, i) => {
        const x = 120 + random(`tx${i}`) * 840, y = 300 + random(`ty${i}`) * 1250, r = 22 + random(`tr${i}`) * 46;
        const dark = random(`tc${i}`) > 0.3;
        return <div key={i} style={{ position: "absolute", left: x + Math.sin(f / 15 + i) * 1.5, top: y, width: r, height: r, borderRadius: "50%",
          background: dark ? "radial-gradient(circle at 40% 40%, #3a3a36, #111 70%)" : "radial-gradient(circle at 40% 40%, #5c5d58, #262624 70%)",
          boxShadow: "0 0 6px rgba(0,0,0,.6)" }} />;
      })}
      <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 45%, rgba(0,0,0,0) 52%, #000 66%)" }} />
    </AbsoluteFill>
  );
};

// scale: real SEM photos of a human hair (CC0 + CSIRO CC BY 3.0), one continuous zoom ×1 → ×1000, ending on one particle
const Scale: React.FC<{ dur: number }> = ({ dur }) => {
  const f = useCurrentFrame();
  const k = interpolate(f, [16, 50], [0, 1], { ...clamp, easing: Easing.inOut(Easing.quad) });
  const Z = Math.pow(1000, k);
  const zA = interpolate(f, [0, 14, 28], [0.92, 1.15, 3.2], { ...clamp, easing: Easing.in(Easing.quad) });
  const aO = interpolate(f, [22, 30], [1, 0], clamp);
  const zB = interpolate(f, [22, 50], [1.3, 4.0], { ...clamp, easing: Easing.in(Easing.cubic) });
  const bO = interpolate(f, [22, 30, 42, 50], [0, 1, 1, 0], clamp);
  const pD = 0.22 * Z;
  return (
    <AbsoluteFill style={{ background: "#060403", overflow: "hidden" }}>
      <Img src={staticFile("hair_b.jpg")} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", opacity: bO, transform: `scale(${zB})`, transformOrigin: "50% 48%", filter: "sepia(.35) brightness(.9) contrast(1.1)" }} />
      <Img src={staticFile("hair_a.jpg")} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", opacity: aO, transform: `scale(${zA})`, transformOrigin: "45% 46%", filter: "sepia(.35) brightness(.95) contrast(1.1)" }} />
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 40%, rgba(0,0,0,.7) 100%)" }} />
      <div style={{ position: "absolute", left: 540 - pD / 2, top: 860 - pD / 2, width: pD, height: pD, borderRadius: "50%",
        background: "radial-gradient(circle at 35% 35%, #fff3c4, #e8b765 45%, #8a5a1a)", boxShadow: `0 0 ${Math.max(4, pD / 3)}px rgba(255,190,90,.9)`, opacity: interpolate(Z, [8, 40], [0, 1], clamp) }} />
      <div style={{ position: "absolute", width: "100%", top: 300, textAlign: "center", fontFamily: "Cinzel", fontWeight: 900, fontSize: 170, color: GOLD,
        textShadow: "0 0 50px rgba(232,183,101,.6), 0 8px 18px #000" }}>×{Math.round(Z).toLocaleString("en-US")}</div>
      <div style={{ position: "absolute", width: "100%", top: 1180, textAlign: "center", opacity: interpolate(f, [0, 4, 22, 28], [0, 1, 1, 0], clamp) }}>
        <span style={{ fontFamily: "Mont", fontWeight: 800, fontSize: 52, color: "#fff", letterSpacing: 4, background: "rgba(0,0,0,.6)", padding: "10px 24px" }}>ONE HUMAN HAIR</span>
      </div>
      <div style={{ position: "absolute", left: 660, top: 830, fontFamily: "Mont", fontWeight: 800, fontSize: 54, color: "#fff", textShadow: "0 3px 10px #000",
        opacity: interpolate(k, [0.8, 1], [0, 1], clamp) }}>≈ 70 NM</div>
      <Tag text={f < 50 ? "ELECTRON MICROSCOPE PHOTOS" : "ILLUSTRATION · PARTICLE"} />
    </AbsoluteFill>
  );
};

// "Gold and silver particles, a thousand times thinner than a human hair": word-synced.
// TEM particles turn gold/silver → push into one → zoom out ×1000 → the hair slides in beside the dot.
const TEM_N = 70;
const temPos = (i: number) => ({ x: 120 + random(`tx${i}`) * 840, y: 300 + random(`ty${i}`) * 1250, r: 22 + random(`tr${i}`) * 46, dark: random(`tc${i}`) > 0.3 });
const HERO = (() => { let best = 0, bd = 1e9; for (let i = 0; i < TEM_N; i++) { const p = temPos(i); const d = Math.hypot(p.x + p.r / 2 - 540, p.y + p.r / 2 - 860) - p.r; if (d < bd) { bd = d; best = i; } } return best; })();
const near = (k: number) => Array.from({ length: TEM_N }, (_, i) => i).filter((i) => i !== HERO).sort((a, b) => {
  const pa = temPos(a), pb = temPos(b); return Math.hypot(pa.x - 540, pa.y - 860) - Math.hypot(pb.x - 540, pb.y - 860); });
const ORDER = near(0);
const GOLDS = [HERO, ORDER[0], ORDER[2]], SILVERS = [ORDER[1], ORDER[3], ORDER[4]];
const ParticlesToHair: React.FC<{ t0: number }> = ({ t0 }) => {
  const f = useCurrentFrame();
  const at = (sec: number) => Math.round((sec - t0) * FPS);        // video seconds → local frame
  // word times (video s) measured with whisper on the narration
  const GOLD_AT = at(16.59), SIL_AT = at(17.23), PUSH = at(17.57), NM = at(18.05), OUT = at(18.63), CNT_END = at(19.89), HAIR_IN = at(19.76), HAIR_FULL = at(20.3), HUMAN = at(20.33), GONE = at(21.27);
  const hp = temPos(HERO); const hx = hp.x + hp.r / 2, hy = hp.y + hp.r / 2;
  // push in: move the hero particle to centre and scale it to 220 px
  const pin = interpolate(f, [PUSH, OUT - 4], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  const S1 = 1 + (220 / hp.r - 1) * pin;
  const tx = (540 - hx) * pin, ty = (860 - hy) * pin;
  const field = interpolate(f, [at(17.69), at(18.19)], [1, 0], clamp);
  // zoom out: particle 220 px → 14 px dot, drifting left; counter ×1 → ×1000
  const zo = interpolate(f, [OUT, HAIR_FULL], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  const dotD = interpolate(zo, [0, 1], [220, 14]);
  const dotX = interpolate(f, [HAIR_IN, HAIR_FULL], [540, 175], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  const kc = interpolate(f, [OUT, CNT_END], [0, 1], { ...clamp, easing: Easing.in(Easing.quad) });
  const Z = Math.pow(1000, kc);
  const hairX = interpolate(f, [HAIR_IN, HAIR_FULL], [1080, 130], { ...clamp, easing: Easing.out(Easing.cubic) });
  const hairZ = interpolate(f, [HAIR_FULL, GONE], [1.0, 1.06], clamp);
  const ring = f >= HUMAN ? interpolate(f - HUMAN, [0, 14], [1, 2.4], clamp) : 1;
  const ringO = f >= OUT ? (f >= HUMAN ? interpolate(f - HUMAN, [0, 14], [1, 0.35], clamp) : 1) : 0;
  const lbl = interpolate(f, [GONE - 2, GONE + 2], [1, 0], clamp);
  const flare = interpolate(f, [GONE, GONE + 2], [0, 1], clamp);
  const heroShown = f >= at(17.89);
  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden" }}>
      {/* TEM field (identical to the previous scene's last frame) */}
      <AbsoluteFill style={{ opacity: field }}>
        <AbsoluteFill style={{ transformOrigin: `${hx}px ${hy}px`, transform: `translate(${tx}px, ${ty}px) scale(${S1})` }}>
          <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 45%, #b9c2b4 0%, #8e978a 45%, #2b2f2a 72%, #000 80%)" }} />
          {Array.from({ length: TEM_N }).map((_, i) => {
            const p = temPos(i);
            const g = GOLDS.indexOf(i), sv = SILVERS.indexOf(i);
            const on = g >= 0 ? f >= GOLD_AT + g * 2 : sv >= 0 ? f >= SIL_AT + sv * 2 : false;
            const since = g >= 0 ? f - (GOLD_AT + g * 2) : f - (SIL_AT + sv * 2);
            const pop = on ? interpolate(since, [0, 2, 4], [1, 1.08, 1.0], clamp) : 1;
            const bg = !on ? (p.dark ? "radial-gradient(circle at 40% 40%, #3a3a36, #111 70%)" : "radial-gradient(circle at 40% 40%, #5c5d58, #262624 70%)")
              : g >= 0 ? "radial-gradient(circle at 35% 35%, #fff3c4, #e8b765 45%, #8a5a1a)" : "radial-gradient(circle at 35% 35%, #ffffff, #c9ccd1 45%, #6b6f75)";
            return <div key={i} style={{ position: "absolute", left: p.x + Math.sin((f + 400) / 15 + i) * 1.5, top: p.y, width: p.r, height: p.r, borderRadius: "50%", background: bg,
              transform: `scale(${pop})`, boxShadow: on ? (g >= 0 ? `0 0 ${p.r * 0.8}px rgba(255,190,90,.9)` : `0 0 0 3px #ffffff, 0 0 ${p.r}px 6px rgba(235,245,255,.95)`) : "0 0 6px rgba(0,0,0,.6)",
              outline: i === HERO && f < GOLD_AT ? "none" : undefined }} />;
          })}
          <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 45%, rgba(0,0,0,0) 52%, #000 66%)" }} />
        </AbsoluteFill>
        <div style={{ position: "absolute", left: 120, top: 1260, width: 220, height: 10, background: "#f2f2ea", opacity: interpolate(f, [PUSH, PUSH + 6], [1, 0], clamp) }} />
        <div style={{ position: "absolute", left: 120, top: 1205, fontFamily: "Mont", fontWeight: 800, fontSize: 40, color: "#f2f2ea", opacity: interpolate(f, [PUSH, PUSH + 6], [1, 0], clamp) }}>100 nm</div>
      </AbsoluteFill>
      {/* the hair slides in from the right */}
      {f >= HAIR_IN && <Img src={staticFile("hair_a.jpg")} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", transformOrigin: "30% 50%",
        transform: `translateX(${hairX}px) scale(${hairZ})`, filter: "sepia(.35) brightness(.95) contrast(1.1)" }} />}
      {/* hero particle → dot with marker ring */}
      {heroShown && <>
        <div style={{ position: "absolute", left: dotX - dotD / 2, top: 860 - dotD / 2, width: dotD, height: dotD, borderRadius: "50%",
          background: "radial-gradient(circle at 35% 35%, #fff3c4, #e8b765 45%, #8a5a1a)", boxShadow: `0 0 ${Math.max(10, dotD / 3)}px rgba(255,190,90,.95)` }} />
        <div style={{ position: "absolute", left: dotX - 40 * ring, top: 860 - 40 * ring, width: 80 * ring, height: 80 * ring, borderRadius: "50%", border: "4px solid #fff3c4", opacity: ringO * (1 - zo < 0.6 ? 1 : 0) * lbl }} />
        <div style={{ position: "absolute", left: dotX + Math.max(30, dotD / 2 + 20), top: 832, opacity: interpolate(f, [NM, NM + 6], [0, 1], clamp) * lbl, whiteSpace: "nowrap" }}>
          <span style={{ fontFamily: "Mont", fontWeight: 800, fontSize: interpolate(zo, [0, 1], [52, 36]), color: "#fff", background: "rgba(0,0,0,.72)", padding: "8px 18px", borderLeft: `6px solid ${GOLD}` }}>≈ 70 NM</span>
        </div>
      </>}
      {/* streak flare into the light-split scene */}
      <AbsoluteFill style={{ opacity: flare, mixBlendMode: "screen", background: `linear-gradient(180deg, rgba(0,0,0,0) 38%, rgba(255,250,235,1) 44.8%, #fff 45%, rgba(255,250,235,1) 45.2%, rgba(0,0,0,0) 52%), linear-gradient(90deg, rgba(255,240,210,.95), rgba(255,240,210,.35))` }} />
      {/* counter, then the hair label (top, clear of the captions) */}
      <div style={{ position: "absolute", width: "100%", top: 300, textAlign: "center", fontFamily: "Cinzel", fontWeight: 900, fontSize: 170, color: GOLD,
        textShadow: "0 0 50px rgba(232,183,101,.6), 0 8px 18px #000", opacity: interpolate(f, [OUT, OUT + 4, at(20.08), at(20.26)], [0, 1, 1, 0], clamp) }}>×{Math.round(Z).toLocaleString("en-US")}</div>
      <div style={{ position: "absolute", width: "100%", top: 320, textAlign: "center", opacity: interpolate(f, [HUMAN, HUMAN + 6], [0, 1], clamp) * lbl }}>
        <span style={{ fontFamily: "Mont", fontWeight: 800, fontSize: 50, color: "#fff", background: "rgba(0,0,0,.72)", padding: "12px 26px", borderLeft: "8px solid #c9a774" }}>ONE HUMAN HAIR ≈ 70,000 NM</span>
      </div>
      <AbsoluteFill style={{ opacity: lbl }}><Tag text={f < at(17.89) ? "ILLUSTRATION · ELECTRON MICROSCOPE VIEW" : f < HAIR_IN ? "ILLUSTRATION" : "HAIR: ELECTRON MICROSCOPE PHOTO"} /></AbsoluteFill>
    </AbsoluteFill>
  );
};

// light hits the particles: front light bounces back green, back light passes through red
const Arrow: React.FC<{ d: string; color: string; p: number }> = ({ d, color, p }) => (
  <path d={d} stroke={color} strokeWidth={14} fill="none" strokeLinecap="round" pathLength={1} strokeDasharray="1" strokeDashoffset={1 - p}
    style={{ filter: `drop-shadow(0 0 14px ${color})` }} />
);
const LightSplit: React.FC<{ dur: number }> = ({ dur }) => {
  const f = useCurrentFrame();
  const half = interpolate(f, [4, 16], [1, 0.5], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  const a1 = interpolate(f, [8, 30], [0, 1], clamp), a2 = interpolate(f, [24, 46], [0, 1], clamp);
  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden" }}>
      <GreenImg />
      <div style={{ position: "absolute", inset: 0, clipPath: `inset(0 0 0 ${half * 100}%)` }}><RedImg /></div>
      <div style={{ position: "absolute", top: 0, bottom: 0, left: `${half * 100}%`, width: 6, marginLeft: -3, background: "#fff", boxShadow: "0 0 40px 14px rgba(255,240,220,.6)" }} />
      <svg width={1080} height={1920} style={{ position: "absolute" }}>
        <Arrow d="M 40 520 L 300 760 L 60 1000" color={JADE} p={a1} />
        <Arrow d="M 1060 560 L 820 760 L 1060 980" color="#fff6e0" p={a2 * 0.5 + (a2 > 0 ? 0 : 0)} />
        <Arrow d="M 780 760 L 1040 760" color={RUBY} p={interpolate(a2, [0.5, 1], [0, 1], clamp)} />
      </svg>
      <div style={{ position: "absolute", left: 40, top: 1100, fontFamily: "Mont", fontWeight: 800, fontSize: 48, color: "#fff", background: "rgba(0,0,0,.72)", borderLeft: `8px solid ${JADE}`, padding: "12px 22px", lineHeight: 1.15, opacity: a1 }}>FRONT LIGHT<br /><span style={{ color: JADE }}>BOUNCES</span></div>
      <div style={{ position: "absolute", right: 40, top: 1250, textAlign: "right", fontFamily: "Mont", fontWeight: 800, fontSize: 48, color: "#fff", background: "rgba(0,0,0,.72)", borderRight: `8px solid ${RUBY}`, padding: "12px 22px", lineHeight: 1.15, opacity: a2 }}>BACK LIGHT<br /><span style={{ color: GOLD }}>PASSES</span></div>
    </AbsoluteFill>
  );
};

// 2013: a drop lands on a chip of nano-"cups" and a colour wave spreads from it
const Sensor: React.FC<{ dur: number; drop: number }> = ({ dur, drop }) => {
  const f = useCurrentFrame();
  const z = interpolate(f, [0, dur], [1.0, 1.15], clamp);
  const dy = interpolate(f, [drop - 14, drop], [-900, 0], { ...clamp, easing: Easing.in(Easing.quad) });
  const R = Math.max(0, (f - drop) * 0.42);           // wave radius in cells
  const ix = 7, iy = 5;
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, #3a0d0a 0%, #0a0302 70%)", overflow: "hidden" }}>
      <div style={{ position: "absolute", left: 140, top: 560, width: 800, height: 800, transform: `perspective(1400px) rotateX(38deg) scale(${z})`, borderRadius: 26,
        background: "linear-gradient(135deg, #1b2422, #0b0f0e)", border: "3px solid #3c4a46", boxShadow: "0 60px 120px #000" }}>
        {Array.from({ length: 12 * 12 }).map((_, i) => {
          const cx = i % 12, cy = Math.floor(i / 12);
          const on = f >= drop && Math.hypot(cx - ix, cy - iy) < R;
          return <div key={i} style={{ position: "absolute", left: 30 + cx * 62, top: 30 + cy * 62, width: 46, height: 46, borderRadius: "50%",
            background: on ? RUBY : JADE, opacity: 0.6 + 0.4 * Math.abs(Math.sin(f / 10 + i)), boxShadow: `0 0 18px ${on ? RUBY : JADE}` }} />;
        })}
      </div>
      {f < drop + 2 && <div style={{ position: "absolute", left: 540 + 60, top: 820 + dy, width: 44, height: 64, borderRadius: "50% 50% 50% 50% / 60% 60% 40% 40%",
        background: "radial-gradient(circle at 40% 35%, #ffffff, #9fd8ff 50%, #3a7fb8)", boxShadow: "0 0 20px rgba(160,215,255,.8)" }} />}
      <AbsoluteFill style={{ opacity: interpolate(f, [dur - 20, dur - 12], [1, 0], clamp) }}><Label text="2013 · DETECTS CHEMICALS" at={drop + 4} x={90} y={300} size={52} /><Tag text="ILLUSTRATION" /></AbsoluteFill>
    </AbsoluteFill>
  );
};

const CenterTitle: React.FC<{ text: string; at: number; top: number; size: number }> = ({ text, at, top, size }) => {
  const f = useCurrentFrame();
  const o = interpolate(f, [at, at + 8], [0, 1], clamp);
  return <div style={{ position: "absolute", width: "100%", top, textAlign: "center", opacity: o, transform: `translateY(${(1 - o) * 20}px) scale(${0.92 + 0.08 * o})`, fontFamily: "Cinzel", fontWeight: 900, fontSize: size, color: GOLD, letterSpacing: 4, textShadow: `0 0 30px ${GOLD}88, 0 4px 10px #000` }}>{text}</div>;
};

// "no Roman could ever have seen them… smaller than a wavelength of light": one light wave vs one particle, to scale
const LightWave: React.FC<{ dur: number; smallerAt: number }> = ({ dur, smallerAt }) => {
  const f = useCurrentFrame();
  const LAM = 700;                                    // 500 nm wavelength on screen
  const P = LAM * 70 / 500;                           // 70 nm particle → 98 px
  const ph = f * 9;
  const pts = Array.from({ length: 121 }).map((_, i) => { const x = -60 + i * 10; return `${x},${960 + Math.sin(((x + ph) / LAM) * 2 * Math.PI) * 170}`; }).join(" ");
  const wO = interpolate(f, [0, 10], [0, 1], clamp);
  const pO = interpolate(f, [smallerAt - 6, smallerAt + 4], [0, 1], clamp);
  const br = interpolate(f, [smallerAt + 4, smallerAt + 16], [0, 1], clamp);
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 50%, #1a1208 0%, #040302 70%)", overflow: "hidden" }}>
      <AbsoluteFill style={{ opacity: 0.18, filter: "blur(10px)" }}><RedImg /></AbsoluteFill>
      <svg width={1080} height={1920} style={{ position: "absolute", opacity: wO }}>
        <defs><linearGradient id="spec" x1="0" x2="1"><stop offset="0" stopColor="#8fd3a8" /><stop offset=".5" stopColor="#fff3c4" /><stop offset="1" stopColor="#ff5a4a" /></linearGradient></defs>
        <polyline points={pts} fill="none" stroke="url(#spec)" strokeWidth={14} strokeLinecap="round" style={{ filter: "drop-shadow(0 0 16px rgba(255,240,200,.8))" }} />
        {/* one wavelength bracket */}
        <g opacity={br}>
          <line x1={190} y1={1210} x2={190 + LAM} y2={1210} stroke="#efe2c8" strokeWidth={5} />
          <line x1={190} y1={1185} x2={190} y2={1235} stroke="#efe2c8" strokeWidth={5} />
          <line x1={190 + LAM} y1={1185} x2={190 + LAM} y2={1235} stroke="#efe2c8" strokeWidth={5} />
        </g>
      </svg>
      <div style={{ position: "absolute", left: 540 - P / 2, top: 960 - P / 2, width: P, height: P, borderRadius: "50%", opacity: pO, transform: `scale(${0.6 + 0.4 * pO})`,
        background: "radial-gradient(circle at 35% 35%, #fff3c4, #e8b765 45%, #8a5a1a)", boxShadow: "0 0 40px rgba(255,190,90,.95)" }} />
      <div style={{ position: "absolute", width: "100%", top: 1250, textAlign: "center", opacity: br }}>
        <span style={{ fontFamily: "Mont", fontWeight: 800, fontSize: 44, color: "#fff", background: "rgba(0,0,0,.72)", padding: "10px 22px", borderLeft: "8px solid #fff3c4" }}>LIGHT WAVE ≈ 500 NM</span>
      </div>
      <div style={{ position: "absolute", left: 600, top: 840, opacity: pO }}>
        <span style={{ fontFamily: "Mont", fontWeight: 800, fontSize: 44, color: "#fff", background: "rgba(0,0,0,.72)", padding: "10px 22px", borderLeft: `8px solid ${GOLD}` }}>PARTICLE ≈ 70 NM</span>
      </div>
      <CenterTitle text="INVISIBLE TO ROME" at={4} top={300} size={74} />
      <Tag text="ILLUSTRATION · TO SCALE" />
    </AbsoluteFill>
  );
};

// outro: same cup, green | red, question on a dark band; last 0.5 s green sweeps back over the red (loops to frame 1)
const Outro: React.FC<{ dur: number }> = ({ dur }) => {
  const f = useCurrentFrame();
  const o = interpolate(f, [0, 12], [0, 1], clamp);
  const back = interpolate(f, [dur - 15, dur - 1], [50, 100], { ...clamp, easing: Easing.in(Easing.cubic) });
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <AbsoluteFill style={{ transform: "scale(1.08)", transformOrigin: "52% 40%" }}>
        <RedImg />
        <div style={{ position: "absolute", inset: 0, clipPath: `inset(0 ${100 - back}% 0 0)` }}><GreenImg /></div>
      </AbsoluteFill>
      <div style={{ position: "absolute", left: `${back}%`, top: 0, width: 6, marginLeft: -3, height: 1920, background: "linear-gradient(#fff0, #fff, #fff0)", opacity: back < 100 ? 1 : 0 }} />
      <div style={{ position: "absolute", left: 0, right: 0, top: 170, height: 470, background: "linear-gradient(180deg, rgba(0,0,0,.85), rgba(0,0,0,.6) 80%, rgba(0,0,0,0))", opacity: o }} />
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", paddingTop: 210, opacity: o }}>
        <div style={{ fontFamily: "Cinzel", fontWeight: 900, fontSize: 108, textAlign: "center", letterSpacing: 3, lineHeight: 1.08 }}>
          <span style={{ color: GOLD, textShadow: "0 0 30px rgba(232,183,101,.6)" }}>GENIUS</span><br />
          <span style={{ color: "#fff", fontSize: 64 }}>OR</span><br />
          <span style={{ color: "#fff", textShadow: "0 0 30px rgba(255,255,255,.35)" }}>ACCIDENT?</span>
        </div>
        <div style={{ marginTop: 30, whiteSpace: "nowrap", fontFamily: "Mont", fontWeight: 800, fontSize: 44, color: "#fff", background: "rgba(192,57,43,.9)", padding: "14px 34px", opacity: interpolate(f, [30, 40], [0, 1], clamp) }}>WHAT DO YOU THINK? COMMENT BELOW</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const Short: React.FC = () => {
  const B = t(seg[2].start - 0.15), C = t(seg[3].start - 0.15), D = t(seg[4].start - 0.1), E = t(seg[5].start - 0.1), F = t(seg[6].start - 0.15),
    G = t(seg[7].start - 0.15), H = t(seg[8].start - 0.15);
  // red right after "Look again." (word time, video s)
  const FLIPS = [3.14].map((x) => Math.round(x * FPS));
  const END = Math.ceil((narration.duration + OFF + 1.0) * FPS);
  const XF = 8;
  const E2 = Math.round(21.4 * FPS);       // "Light" at 17.49 s                             // crossfade frames
  const SMALLER = Math.round(32.01 * FPS) - G;   // "…they're smaller"
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <style>{fontCss}</style>
      <Sequence from={0} durationInFrames={B}>
        <Reveal flips={FLIPS} dur={B} />
        <Label text="LYCURGUS CUP" at={Math.round(3.89 * FPS)} x={110} y={300} size={60} />
        <Label text="4TH CENTURY AD" at={Math.round(4.19 * FPS)} x={110} y={378} size={36} color="#efe2c8" />
      </Sequence>
      {/* figure close-up, then one continuous zoom into the glass → microscope */}
      <Sequence from={B} durationInFrames={D - B}><IntoGlass s2={C - B} dur={D - B} />
        <Sequence from={C - B}><Label text="1990" at={22} x={90} y={300} size={110} color="#f2f2ea" /></Sequence>
      </Sequence>
      <Sequence from={D} durationInFrames={E2 - D}><ParticlesToHair t0={D / FPS} /></Sequence>
      <Sequence from={E2} durationInFrames={F - E2}><LightSplit dur={F - E2} /></Sequence>
      <Sequence from={F} durationInFrames={G - F + XF}>
        <Photo src="c8.jpg" dur={G - F} from={1.0} to={1.22} origin="50% 60%" filter="contrast(1.1) saturate(1.3)" />
        <div style={{ position: "absolute", left: 0, right: 0, top: 165, height: 330, background: "linear-gradient(180deg, rgba(0,0,0,.85), rgba(0,0,0,.55) 75%, rgba(0,0,0,0))" }} />
        <CenterTitle text="NANOTECHNOLOGY" at={t(seg[6].start + 0.9) - F} top={215} size={84} />
      </Sequence>
      <Sequence from={G} durationInFrames={H - G + XF}><Fade len={XF + 4}><LightWave dur={H - G + XF} smallerAt={SMALLER} /></Fade></Sequence>
      <Sequence from={H} durationInFrames={END - H}><Fade len={XF}><Outro dur={END - H} /></Fade></Sequence>

      <Flash at={FLIPS[0]} color="#ffb08a" peak={0.75} />
      <Flash at={Math.round(PUNCH * FPS)} color="#ffd9a0" peak={0.3} />   {/* punch on "In the fourth century!" */}
      <Captions />
      <Grain />
      <Audio src={staticFile("mix.wav")} />
    </AbsoluteFill>
  );
};
