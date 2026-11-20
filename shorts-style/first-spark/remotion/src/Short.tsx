import React from "react";
import { AbsoluteFill, Audio, OffthreadVideo, Sequence, staticFile, interpolate, useCurrentFrame, Easing, random, getInputProps, Img } from "remotion";
import { MathOverlay } from "./MathOverlay";
import { SpaceSparkle } from "./SpaceSparkle";

// Music-only Short. Every cut is placed on the song's own pulse:
// intro hits every 0.745 s, the "rewind" break at 13.56 s, the drop at 14.31 s.
const FPS = 30;
const f = (s: number) => Math.round(s * FPS);
const P = 0.745;               // pulse length (s)
const DROP = 17.34;            // first montage cut: the beat at 0:17
const MUSIC_IN = 13.0;          // song second where the music enters
const PRE = 2.9;                // untouched chimp footage before the music
export const T0 = MUSIC_IN - PRE;
const VOICE1_AT = 0.35;  // video second: "That's one small step for man" over the untouched chimp footage, before the music
const VOICE2_AT = 28.1;  // song second: "One giant leap for mankind" (reverb) while the Earth recedes on the screen
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const CYAN = "#7fe3ff";

// montage: [file, pulses, start offset (s) inside the clip, zoom from, zoom to]
// [file, seconds, clip offset, zoom from, zoom to]; starts at the drop (14.31 s in the song)
const SHOTS: [string, number, number, number, number][] = [
  // war, on the beat (0.745 s), no vocals yet
  ["nuke.mp4", 1.49, 0.8, 1.0, 1.15],
  ["salvo.mp4", 1.49, 0, 1.0, 1.12],
  ["planes.mp4", 0.745, 0, 1.0, 1.1],
  ["tank.mp4", 0.745, 0.6, 1.0, 1.12],
  ["ivymike.mp4", 1.65, 0, 1.0, 1.12],       // Ivy Mike fireball, ends exactly at 23.46 s: the vocal comes in
  // the voice enters: space
  ["moonflag.mp4", 2.04, 0, 1.0, 1.06],     // 23.46: vocal entry, Apollo 14 flag on the Moon (NASA 16mm film, 1971)
  ["artemis.mp4", 1.80, 0, 1.0, 1.12],       // 25.50: vocal word, the rocket rises
  ["END", 6.84, 0, 1, 1],                    // 27.30: Earth (NASA MESSENGER) shrinking inside the robot's monitor; pull back, the hand reaches in
];
const starts: number[] = []; { let s = DROP; for (const sh of SHOTS) { starts.push(s); s += sh[1]; } starts.push(s); }
export const TOTAL_S = starts[starts.length - 1] + 0.4 - T0;

// ---------------- helpers ----------------
const Clip: React.FC<{ src: string; dur: number; zoom: [number, number]; start?: number; filter?: string }> = ({ src, dur, zoom, start = 0, filter }) => {
  const fr = useCurrentFrame();
  const z = interpolate(fr, [0, dur], zoom, clamp);
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#000" }}>
      <OffthreadVideo src={staticFile(src)} startFrom={start} muted style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${z})`, filter }} />
    </AbsoluteFill>
  );
};
const Photo: React.FC<{ src: string; dur: number; from: number; to: number; origin?: string; filter?: string; ease?: (x: number) => number }> = ({ src, dur, from, to, origin = "50% 40%", filter, ease = Easing.inOut(Easing.sin) }) => {
  const fr = useCurrentFrame();
  const p = interpolate(fr, [0, dur], [0, 1], { ...clamp, easing: ease });
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#000" }}>
      <Img src={staticFile(src)} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", transformOrigin: origin, transform: `scale(${from + (to - from) * p})`, filter }} />
    </AbsoluteFill>
  );
};
const Flash: React.FC<{ at: number; color?: string; peak?: number; len?: number }> = ({ at, color = "#fff3dc", peak = 0.5, len = 8 }) => {
  const fr = useCurrentFrame();
  const o = interpolate(fr, [at - 2, at, at + len], [0, peak, 0], clamp);
  return <AbsoluteFill style={{ background: color, opacity: o, mixBlendMode: "screen", pointerEvents: "none" }} />;
};
const Grain: React.FC = () => {
  const fr = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <svg width="1080" height="1920" style={{ position: "absolute", opacity: 0.035, mixBlendMode: "overlay" }}>
        <filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed={fr % 12} /></filter>
        <rect width="100%" height="100%" filter="url(#n)" />
      </svg>
      <AbsoluteFill style={{ boxShadow: "inset 0 0 160px 30px rgba(0,0,0,.8)" }} />
    </AbsoluteFill>
  );
};
const Embers: React.FC<{ n?: number }> = ({ n = 40 }) => {
  const fr = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {Array.from({ length: n }).map((_, i) => {
        const sp = 2 + random(`s${i}`) * 5, x0 = random(`x${i}`) * 1080, ph = random(`p${i}`) * 400;
        const y = 1950 - ((fr * sp + ph) % 2100), x = x0 + Math.sin((fr + ph) / 20) * 40, r = 2 + random(`r${i}`) * 5;
        return <div key={i} style={{ position: "absolute", left: x, top: y, width: r, height: r, borderRadius: "50%", background: "#ffb347", boxShadow: "0 0 12px 4px rgba(255,140,40,.7)" }} />;
      })}
    </AbsoluteFill>
  );
};
const FireLight: React.FC = () => {
  const fr = useCurrentFrame();
  const k = 0.55 + 0.25 * Math.sin(fr / 2.3) + 0.15 * Math.sin(fr / 1.1 + 2) + 0.1 * random(`fl${Math.floor(fr / 2)}`);
  return <AbsoluteFill style={{ background: `radial-gradient(ellipse at 55% 95%, rgba(255,140,40,${0.55 * k}) 0%, rgba(255,90,20,${0.25 * k}) 35%, rgba(0,0,0,0) 70%)`, mixBlendMode: "screen" }} />;
};

// a strike of flint: a burst of hot sparks from one point
const SparkBurst: React.FC<{ at: number; x: number; y: number; seed: string }> = ({ at, x, y, seed }) => {
  const fr = useCurrentFrame();
  const t = (fr - at) / FPS;
  if (t < 0 || t > 1.2) return null;
  return (
    <>
      <div style={{ position: "absolute", left: x - 160, top: y - 160, width: 320, height: 320, borderRadius: "50%",
        background: "radial-gradient(circle, rgba(255,240,200,.95), rgba(255,160,60,.45) 30%, rgba(0,0,0,0) 70%)", opacity: Math.max(0, 1 - t * 5), mixBlendMode: "screen" }} />
      {Array.from({ length: 46 }).map((_, i) => {
        const ang = random(`${seed}a${i}`) * Math.PI * 2, sp = 500 + random(`${seed}v${i}`) * 1300;
        const px = x + Math.cos(ang) * sp * t, py = y + Math.sin(ang) * sp * t + 900 * t * t;
        const life = 0.35 + random(`${seed}l${i}`) * 0.8; if (t > life) return null;
        const a = 1 - t / life; const L = 10 + 28 * a;
        return <div key={i} style={{ position: "absolute", left: px, top: py, width: L, height: 4, borderRadius: 3, background: "#ffd38a",
          boxShadow: "0 0 10px 3px rgba(255,150,50,.85)", opacity: a, transform: `rotate(${(Math.atan2(Math.sin(ang) * sp + 1800 * t, Math.cos(ang) * sp) * 180) / Math.PI}deg)` }} />;
      })}
    </>
  );
};

// ---------------- neuron network (shared by the zoom, the montage backdrop and the AI shot) ----------------
type Branch = { pts: [number, number][] };
const buildNeuron = (cx: number, cy: number, seed: string, scale = 1) => {
  const br: Branch[] = [];
  const grow = (x: number, y: number, ang: number, len: number, depth: number, id: string) => {
    const pts: [number, number][] = [[x, y]]; let a = ang;
    for (let k = 0; k < 6; k++) { a += (random(`${seed}${id}a${k}`) - 0.5) * 0.6; x += (Math.cos(a) * len) / 6; y += (Math.sin(a) * len) / 6; pts.push([x, y]); }
    br.push({ pts });
    if (depth > 0) for (let j = 0; j < 2; j++) grow(x, y, a + (j ? 0.5 : -0.5) + (random(`${seed}${id}b${j}`) - 0.5) * 0.4, len * 0.68, depth - 1, id + j);
  };
  for (let i = 0; i < 8; i++) grow(cx, cy, (i / 8) * Math.PI * 2 + random(`${seed}r${i}`) * 0.5, 230 * scale * (0.8 + random(`${seed}l${i}`) * 0.5), i === 2 ? 4 : 3, `d${i}`);
  return br;
};
const MAIN = buildNeuron(540, 880, "m");
const BG = [[180, 420, "a"], [900, 380, "b"], [150, 1350, "c"], [930, 1400, "d"], [560, 1650, "e"], [520, 250, "f"]].map(([x, y, s]) => buildNeuron(x as number, y as number, s as string, 0.55));
const pathD = (b: Branch) => b.pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ");
const along = (b: Branch, u: number) => { const n = b.pts.length - 1; const x = Math.min(n - 1e-6, Math.max(0, u * n)); const i = Math.floor(x); const r = x - i;
  return [b.pts[i][0] + (b.pts[i + 1][0] - b.pts[i][0]) * r, b.pts[i][1] + (b.pts[i + 1][1] - b.pts[i][1]) * r]; };
const Network: React.FC<{ fire?: number; pulseSpeed?: number; tint?: string }> = ({ fire = 0, pulseSpeed = 30, tint = CYAN }) => {
  const fr = useCurrentFrame();
  return (
    <svg width={1080} height={1920}>
      <defs>
        <filter id="glow"><feGaussianBlur stdDeviation="6" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
        <radialGradient id="soma"><stop offset="0" stopColor="#fff" /><stop offset=".35" stopColor={tint} /><stop offset="1" stopColor="rgba(127,227,255,0)" /></radialGradient>
      </defs>
      {BG.map((net, j) => net.map((b, i) => <path key={`bg${j}${i}`} d={pathD(b)} stroke="rgba(127,227,255,.22)" strokeWidth={2.5} fill="none" />))}
      <g filter="url(#glow)">
        {MAIN.map((b, i) => <path key={i} d={pathD(b)} stroke={tint} strokeOpacity={0.55 + 0.45 * fire} strokeWidth={5 - Math.min(3, i % 5)} fill="none" strokeLinecap="round" />)}
        {MAIN.map((b, i) => { const u = 1 - (((fr + i * 7) % pulseSpeed) / pulseSpeed); const [x, y] = along(b, u); return <circle key={`p${i}`} cx={x} cy={y} r={7} fill="#e9fbff" />; })}
      </g>
      <circle cx={540} cy={880} r={60 + 300 * fire} fill="url(#soma)" opacity={0.7 + 0.3 * fire} />
    </svg>
  );
};

// the rewind: crash into the head, the neuron lights, then everything snaps forward on the drop
const NeuronZoom: React.FC<{ dur: number }> = ({ dur }) => {
  const fr = useCurrentFrame();
  const head = interpolate(fr, [0, dur * 0.5], [1.4, 9], { ...clamp, easing: Easing.in(Easing.cubic) });
  const headO = interpolate(fr, [dur * 0.3, dur * 0.55], [1, 0], clamp);
  const netO = interpolate(fr, [dur * 0.3, dur * 0.55], [0, 1], clamp);
  const netS = interpolate(fr, [dur * 0.3, dur], [0.3, 1.35], { ...clamp, easing: Easing.out(Easing.quad) });
  const fire = interpolate(fr, [dur - 8, dur - 1], [0, 1], clamp);
  // tape-rewind wobble on the break
  const wob = Math.sin(fr * 2.2) * 14 * (1 - fr / dur);
  return (
    <AbsoluteFill style={{ background: "#02060a", transform: `translateX(${wob}px)` }}>
      <AbsoluteFill style={{ opacity: headO }}>
        <Photo src="chimp_face.jpg" dur={dur} from={head} to={head} origin="50% 38%" filter="brightness(.7) contrast(1.15)" />
        <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 45%, rgba(127,227,255,.45), rgba(0,0,0,0) 55%)", mixBlendMode: "screen" }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ opacity: netO, transform: `scale(${netS})`, transformOrigin: "540px 880px" }}><Network fire={fire} pulseSpeed={12} /></AbsoluteFill>
    </AbsoluteFill>
  );
};

// AI shot: the organic neuron straightens into a green circuit, a rain of mathematical symbols falls,
// and the machine types its question. Readable without narration.
const snap = (v: number) => Math.round(v / 48) * 48;
const RAIN = "0123456789+-×÷=πΣ∫√∞Δ±≈∂λΩ".split("");
const GREEN = "#3dff7a";
const DigitalRain: React.FC<{ o: number }> = ({ o }) => {
  const fr = useCurrentFrame();
  const cols = 22, rows = 34, cw = 1080 / cols, rh = 1920 / rows;
  return (
    <AbsoluteFill style={{ opacity: o }}>
      {Array.from({ length: cols }).map((_, c) => {
        const speed = 0.5 + random(`rs${c}`) * 0.9, off = random(`ro${c}`) * rows;
        const head = (fr * speed + off) % (rows + 12);
        return Array.from({ length: rows }).map((__, r) => {
          const d = head - r; if (d < 0 || d > 12) return null;
          const ch = RAIN[Math.floor(random(`rc${c}_${r}_${Math.floor(fr / 3)}`) * RAIN.length)];
          return <div key={`${c}_${r}`} style={{ position: "absolute", left: c * cw, top: r * rh, width: cw, textAlign: "center",
            fontFamily: "DejaVu Sans Mono, monospace", fontSize: 40, color: d < 1 ? "#d9ffe6" : GREEN, opacity: Math.max(0, 1 - d / 12),
            textShadow: `0 0 10px ${GREEN}` }}>{ch}</div>;
        });
      })}
    </AbsoluteFill>
  );
};
const AIShot: React.FC<{ dur: number }> = ({ dur }) => {
  const fr = useCurrentFrame();
  const m = interpolate(fr, [2, dur * 0.3], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  const col = (k: number) => `rgb(${Math.round(127 + (61 - 127) * k)},${Math.round(227 + (255 - 227) * k)},${Math.round(255 + (122 - 255) * k)})`;
  const P = (x: number, y: number): [number, number] => [x + (snap(x) - x) * m, y + (snap(y) - y) * m];
  const pathM = (b: Branch) => b.pts.map((p, i) => { const [x, y] = P(p[0], p[1]); return `${i ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`; }).join(" ");
  const T = "WHO MADE IT?";
  const tq = dur * 0.38;
  const n = Math.max(0, Math.min(T.length, Math.floor((fr - tq) / 2)));
  const cursor = Math.floor(fr / 7) % 2 === 0;
  const netO = interpolate(fr, [dur * 0.32, dur * 0.48], [1, 0.25], clamp);
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, #03140a 0%, #000 80%)" }}>
      <DigitalRain o={interpolate(fr, [dur * 0.15, dur * 0.35], [0, 0.85], clamp)} />
      <AbsoluteFill style={{ opacity: netO }}>
        <svg width={1080} height={1920}>
          <defs><filter id="aig"><feGaussianBlur stdDeviation="5" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter></defs>
          <g filter="url(#aig)">
            {MAIN.map((b, i) => <path key={i} d={pathM(b)} stroke={col(m)} strokeWidth={4} fill="none" />)}
            {MAIN.map((b, i) => { const u = 1 - (((fr + i * 5) % 18) / 18); const [x0, y0] = along(b, u); const [x, y] = P(x0, y0);
              return <circle key={`p${i}`} cx={x} cy={y} r={6} fill="#eaffef" />; })}
          </g>
          <circle cx={540} cy={880} r={34} fill={col(m)} />
        </svg>
      </AbsoluteFill>
      <div style={{ position: "absolute", top: 860, width: "100%", textAlign: "center", fontFamily: "DejaVu Sans Mono, monospace", fontWeight: 700,
        fontSize: 104, letterSpacing: 6, color: GREEN, textShadow: `0 0 24px ${GREEN}, 0 0 60px rgba(61,255,122,.5)`,
        background: n > 0 ? "rgba(0,0,0,.55)" : "transparent", padding: "24px 0" }}>
        {T.slice(0, n)}{n > 0 && cursor ? "█" : ""}
      </div>
    </AbsoluteFill>
  );
};
// ending: pull back to reveal the question was on a monitor; an (original-design) robot hand presses the
// power button and the screen dies like an old CRT: squeeze to a line, then a dot, then black.
const RobotHand: React.FC<{ x: number; y: number; press: number }> = ({ x, y, press }) => (
  <svg width={1080} height={1920} style={{ position: "absolute", left: 0, top: 0 }}>
    <defs>
      <linearGradient id="metal" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stopColor="#d9dde3" /><stop offset=".45" stopColor="#8a929c" /><stop offset=".7" stopColor="#c3c8cf" /><stop offset="1" stopColor="#5d646d" />
      </linearGradient>
      <filter id="led"><feGaussianBlur stdDeviation="3" /></filter>
    </defs>
    <g transform={`translate(${x},${y}) rotate(-28)`}>
      {/* forearm */}
      <rect x={60} y={-46} width={560} height={92} rx={34} fill="url(#metal)" stroke="#3b4148" strokeWidth={3} />
      {[160, 280, 400, 520].map((px) => <line key={px} x1={px} y1={-40} x2={px} y2={40} stroke="#4a5058" strokeWidth={3} />)}
      {/* palm */}
      <rect x={-70} y={-70} width={150} height={140} rx={30} fill="url(#metal)" stroke="#3b4148" strokeWidth={3} />
      {/* curled fingers */}
      {[-40, -5, 30].map((py, i) => <rect key={i} x={-110} y={py} width={60} height={30} rx={14} fill="url(#metal)" stroke="#3b4148" strokeWidth={3} />)}
      {/* index finger: 3 segments with glowing joints */}
      <g transform={`translate(${-70 - 8 * press},-62)`}>
        <rect x={-74} y={-14} width={78} height={28} rx={13} fill="url(#metal)" stroke="#3b4148" strokeWidth={3} />
        <rect x={-138} y={-12} width={66} height={24} rx={12} fill="url(#metal)" stroke="#3b4148" strokeWidth={3} />
        <rect x={-186} y={-11} width={50} height={22} rx={11} fill="url(#metal)" stroke="#3b4148" strokeWidth={3} />
        {[-74, -138].map((jx) => <circle key={jx} cx={jx} cy={0} r={8} fill="#5fd0ff" filter="url(#led)" />)}
      </g>
      <circle cx={0} cy={0} r={10} fill="#5fd0ff" filter="url(#led)" />
      <circle cx={300} cy={0} r={9} fill="#5fd0ff" filter="url(#led)" />
    </g>
  </svg>
);
const EndShot: React.FC<{ dur: number }> = ({ dur }) => {
  // Starts on the screen (Earth filling the frame), pulls back to reveal the computer; at the end the screen visibly switches off (CRT).
  const fr = useCurrentFrame();
  const z = interpolate(fr, [0, f(2.6)], [2.9, 1.0], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  const OFF = dur - f(1.5);
  const t = fr - OFF;
  const sy = t < 0 ? 1 : interpolate(t, [0, 6], [1, 0.006], { ...clamp, easing: Easing.in(Easing.quad) });
  const sx = t < 6 ? 1 : interpolate(t, [6, 11], [1, 0.004], { ...clamp, easing: Easing.in(Easing.quad) });
  const bright = t < 0 ? 1 : interpolate(t, [0, 6, 11], [1, 3.5, 5], clamp);
  const dot = t < 11 ? 0 : interpolate(t, [11, 13, 24], [1, 1, 0], clamp);
  const ledOff = interpolate(t, [4, 8], [0, 1], clamp);
  const end = interpolate(fr, [dur - 8, dur - 2], [0, 1], clamp);
  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden" }}>
      <AbsoluteFill style={{ transformOrigin: "672px 1188px", transform: `scale(${z})` }}>
        <Img src={staticFile("monitor_off.png")} style={{ position: "absolute", width: 1080, height: 1920 }} />
        <div style={{ position: "absolute", left: 358, top: 1010, width: 630, height: 358, overflow: "hidden" }}>
          {t < 11 && <div style={{ position: "absolute", inset: 0, transform: `scale(${sx}, ${sy})`, filter: `brightness(${bright})`, background: "#000" }}>
            <OffthreadVideo src={staticFile("screen_earth.mp4")} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            <div style={{ position: "absolute", inset: 0, background: "repeating-linear-gradient(0deg, rgba(0,0,0,.18) 0px, rgba(0,0,0,.18) 2px, rgba(0,0,0,0) 2px, rgba(0,0,0,0) 4px)" }} />
          </div>}
          {dot > 0 && <div style={{ position: "absolute", left: 315 - 14, top: 179 - 14, width: 28, height: 28, borderRadius: "50%", opacity: dot,
            background: "radial-gradient(circle, #fff 0%, rgba(200,240,255,.8) 35%, rgba(0,0,0,0) 70%)" }} />}
        </div>
        {/* glass glow while on */}
        <div style={{ position: "absolute", left: 300, top: 960, width: 750, height: 460, opacity: (t < 6 ? 1 : 0) * 0.35,
          background: "radial-gradient(ellipse, rgba(140,200,255,.35) 0%, rgba(0,0,0,0) 65%)", mixBlendMode: "screen" }} />
        {/* power LED goes dark */}
        <div style={{ position: "absolute", left: 300, top: 1418, width: 100, height: 36, background: "#03080a", opacity: ledOff, filter: "blur(3px)" }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "#000", opacity: end }} />
    </AbsoluteFill>
  );
};

// The same spark, carried through history: a small glowing point held at screen centre that
// flares on every cut, so each new shot reads as the spark becoming something bigger.
const SparkThread: React.FC<{ cuts: number[] }> = ({ cuts }) => {
  const fr = useCurrentFrame();
  const last = cuts.filter((c) => c <= fr).pop() ?? 0;
  const since = fr - last;
  const flare = interpolate(since, [0, 3, 12], [1, 0.7, 0.22], clamp);
  const r = 10 + 70 * flare;
  return (
    <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "screen" }}>
      <div style={{ position: "absolute", left: 540 - r * 3, top: 880 - r * 3, width: r * 6, height: r * 6, borderRadius: "50%",
        background: `radial-gradient(circle, rgba(255,250,235,${0.95 * flare}) 0%, rgba(255,190,90,${0.5 * flare}) 18%, rgba(255,140,40,0) 60%)` }} />
    </AbsoluteFill>
  );
};

// Realistic flint sparks: a dozen tiny white-hot particles with short streaks, gravity, gone in < 0.5 s.
const RealSpark: React.FC<{ at: number; x: number; y: number; seed: string }> = ({ at, x, y, seed }) => {
  const fr = useCurrentFrame();
  const t = (fr - at) / FPS;
  if (t < 0 || t > 0.6) return null;
  return (
    <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "screen" }}>
      <div style={{ position: "absolute", left: x - 40, top: y - 40, width: 80, height: 80, borderRadius: "50%",
        background: "radial-gradient(circle, rgba(255,250,230,.9), rgba(255,170,70,.35) 35%, rgba(0,0,0,0) 70%)", opacity: Math.max(0, 1 - t * 12) }} />
      {Array.from({ length: 14 }).map((_, i) => {
        const ang = -Math.PI / 2 + (random(`${seed}a${i}`) - 0.5) * 2.6, sp = 380 + random(`${seed}v${i}`) * 700;
        const life = 0.15 + random(`${seed}l${i}`) * 0.35; if (t > life) return null;
        const px = x + Math.cos(ang) * sp * t, py = y + Math.sin(ang) * sp * t + 1400 * t * t;
        const vx = Math.cos(ang) * sp, vy = Math.sin(ang) * sp + 2800 * t;
        const a = 1 - t / life;
        return <div key={i} style={{ position: "absolute", left: px, top: py, width: 6 + 16 * a, height: 2.5, borderRadius: 2,
          background: a > 0.6 ? "#fffbe8" : "#ffc266", boxShadow: "0 0 6px 2px rgba(255,170,60,.8)", opacity: a,
          transformOrigin: "0 50%", transform: `rotate(${(Math.atan2(-vy, -vx) * 180) / Math.PI}deg)` }} />;
      })}
    </AbsoluteFill>
  );
};

// Visions of the future flickering inside the chimp's head while the song builds ("as if remembering").
const VISIONS = ["nuke.mp4", "silo.jpg", "planes.mp4", "ivymike.mp4", "moonflag.mp4", "nuke.mp4", "silo.jpg"];
const Vision: React.FC<{ src: string; len: number }> = ({ src, len }) => {
  const fr = useCurrentFrame();
  const o = interpolate(fr, [0, 2, len - 2, len], [0, 0.9, 0.9, 0], clamp);
  return (
    <AbsoluteFill style={{ opacity: o }}>
      <div style={{ position: "absolute", left: 140, top: 330, width: 800, height: 800, borderRadius: "50%", overflow: "hidden",
        WebkitMaskImage: "radial-gradient(circle, #000 35%, transparent 70%)", maskImage: "radial-gradient(circle, #000 35%, transparent 70%)" }}>
        {src.endsWith(".jpg") ? <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          : <OffthreadVideo src={staticFile(src)} muted style={{ width: "100%", height: "100%", objectFit: "cover", filter: "saturate(1.3) contrast(1.2)" }} />}
      </div>
    </AbsoluteFill>
  );
};
const Remembering: React.FC<{ dur: number }> = ({ dur }) => {
  // visions get more frequent as the song rises
  const times = [0.12, 0.3, 0.45, 0.58, 0.7, 0.8, 0.9].map((x) => Math.round(x * dur));
  return <>{times.map((t, i) => <Sequence key={i} from={t} durationInFrames={Math.max(5, Math.round(10 - i))}><Vision src={VISIONS[i % VISIONS.length]} len={Math.max(5, Math.round(10 - i))} /></Sequence>)}</>;
};
// Each flash of light in the dive throws a ring of equations out of the brain.
const BURST_EQ = ["E = mc²", "π", "∑", "∫ f(x) dx", "a² + b² = c²", "F = ma", "√2", "e^{iπ} + 1 = 0", "∞", "Δx · Δp ≥ ħ/2", "∇ × B", "λ = h / p"];
const LightBurst: React.FC<{ at: number; seed: string; strength?: number; cx?: number; cy?: number }> = ({ at, seed, strength = 1, cx = 540, cy = 760 }) => {
  const fr = useCurrentFrame();
  const age = fr - at;
  if (age < 0 || age > 18) return null;
  const glow = interpolate(age, [0, 2, 14], [0, 1, 0], clamp) * strength;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <AbsoluteFill style={{ mixBlendMode: "screen", background: `radial-gradient(circle at ${cx}px ${cy}px, rgba(255,250,230,${glow}) 0%, rgba(255,200,110,${0.6 * glow}) 22%, rgba(255,160,60,${0.15 * glow}) 45%, rgba(0,0,0,0) 70%)` }} />
      {BURST_EQ.map((eq, i) => {
        const ang = (i / BURST_EQ.length) * Math.PI * 2 + random(`${seed}a${i}`) * 0.4;
        const dist = interpolate(age, [0, 16], [40, 520 + random(`${seed}d${i}`) * 260], { ...clamp, easing: Easing.out(Easing.cubic) });
        const o = interpolate(age, [0, 2, 12, 18], [0, 1, 0.9, 0], clamp);
        const sz = 34 + random(`${seed}s${i}`) * 40;
        return <div key={i} style={{ position: "absolute", left: cx + Math.cos(ang) * dist, top: cy + Math.sin(ang) * dist, transform: `translate(-50%,-50%) scale(${0.6 + age / 30})`,
          fontFamily: "DejaVu Serif, serif", fontStyle: "italic", fontWeight: 700, fontSize: sz, color: "#fff1cf", opacity: o, whiteSpace: "nowrap",
          textShadow: "0 0 18px rgba(255,200,110,.9), 0 2px 8px #000" }}>{eq}</div>;
      })}
    </AbsoluteFill>
  );
};

// The rewind at 0:14: dive into the head while the visions race backwards between streams of maths, then the neuron fires.
const RUSH = ["artemis.mp4", "moonflag.mp4", "ivymike.mp4", "nuke.mp4"];
const BrainRewind: React.FC<{ dur: number }> = ({ dur }) => {
  const fr = useCurrentFrame();
  const head = interpolate(fr, [0, dur * 0.45], [1.4, 8], { ...clamp, easing: Easing.in(Easing.cubic) });
  const headO = interpolate(fr, [dur * 0.25, dur * 0.5], [1, 0], clamp);
  const k = Math.min(RUSH.length - 1, Math.floor(fr / Math.max(1, (dur * 0.8) / RUSH.length)));
  const rushO = fr < dur * 0.85 ? interpolate(fr, [0, 3], [0, 0.85], clamp) : 0;
  const skew = Math.sin(fr * 3.3) * 8, shift = Math.sin(fr * 2.1) * 40;
  const fire = interpolate(fr, [dur - 7, dur - 1], [0, 1], clamp);
  const src = RUSH[k];
  return (
    <AbsoluteFill style={{ background: "#02060a" }}>
      <AbsoluteFill style={{ opacity: rushO, transform: `translateX(${shift}px) skewX(${skew}deg) scale(1.1)`, filter: "contrast(1.3) saturate(1.3) hue-rotate(-15deg)" }}>
        {src.endsWith(".jpg") ? <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          : <OffthreadVideo src={staticFile(src)} startFrom={f(1.2)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />}
      </AbsoluteFill>
      <AbsoluteFill style={{ opacity: headO, mixBlendMode: "screen" }}>
        <Photo src="chimp_snow_face.jpg" dur={dur} from={head} to={head} origin="47% 29%" filter="brightness(.8) contrast(1.15)" />
      </AbsoluteFill>
      {[0, Math.round(dur * 0.33), Math.round(dur * 0.66)].map((t, i) => <LightBurst key={i} at={t} seed={`lb${i}`} strength={0.75 + 0.15 * i} />)}
      {Array.from({ length: 7 }).map((_, i) => (
        <div key={i} style={{ position: "absolute", left: 0, right: 0, top: ((fr * 131 + i * 277) % 1920), height: 5 + (i % 3) * 9, background: "rgba(255,255,255,.2)" }} />
      ))}
      <AbsoluteFill style={{ opacity: fire, transform: `scale(${0.6 + 0.8 * fire})`, transformOrigin: "540px 880px" }}><Network fire={fire} pulseSpeed={8} /></AbsoluteFill>
    </AbsoluteFill>
  );
};

const HITS = [3.11, 3.86, 4.6, 5.35, 6.1, 6.85];
const StrikeSlow: React.FC<{ dur: number }> = ({ dur }) => {
  const fr = useCurrentFrame();
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#000" }}>
      <OffthreadVideo src={staticFile("strike.mp4")} playbackRate={0.4} muted style={{ width: "100%", height: "100%", objectFit: "cover",
        transform: `scale(${interpolate(fr, [0, dur], [1.0, 1.12], clamp)})`, transformOrigin: "55% 75%" }} />
    </AbsoluteFill>
  );
};

const StrikeCut: React.FC<{ dur: number }> = ({ dur }) => {
  const fr = useCurrentFrame();
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#000" }}>
      <OffthreadVideo src={staticFile("strike.mp4")} startFrom={f(0.25)} muted style={{ width: "100%", height: "100%", objectFit: "cover",
        transform: `scale(${interpolate(fr, [0, dur], [1.05, 1.15], clamp)})`, transformOrigin: "70% 70%" }} />
    </AbsoluteFill>
  );
};

// One big equation on every beat of the song's intro, so music and maths land together from frame one.
const BEATS = [14.37, 15.12, 15.85, 16.6];
const BEAT_EQ = ["a² + b² = c²", "F = ma", "e^{iπ} + 1 = 0", "∫ f(x) dx", "Σ", "∇ × B"];
const BeatMath: React.FC = () => {
  const fr = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {BEATS.map((b, i) => {
        const age = fr - f(b); if (age < 0 || age > 20) return null;
        const pop = interpolate(age, [0, 3, 20], [0.6, 1.08, 1.0], clamp), o = interpolate(age, [0, 2, 14, 20], [0, 1, 1, 0], clamp);
        const x = [540, 300, 760, 420, 640, 360, 700, 540][i], y = [520, 700, 600, 1250, 420, 980, 1150, 800][i];
        return <div key={i} style={{ position: "absolute", left: x, top: y, transform: `translate(-50%,-50%) scale(${pop})`, opacity: o,
          fontFamily: "DejaVu Serif, serif", fontStyle: "italic", fontWeight: 700, fontSize: i % 3 === 1 ? 170 : 96, color: "#ffe2a6", whiteSpace: "nowrap",
          textShadow: "0 0 30px rgba(255,190,90,.8), 0 4px 12px #000" }}>{BEAT_EQ[i]}</div>;
      })}
    </AbsoluteFill>
  );
};

// Centuries of one skyline: the same city from across the water, 1876 → 2020, each era dissolving into the next.
const ERAS: [string, number, string][] = [["ny_1908.jpg", 1340, "none"], ["ny_1920.jpg", 1340, "contrast(.8) sepia(.55) blur(.6px) brightness(1.08)"], ["ny_1940.jpg", 1340, "none"], ["ny_2020.jpg", 1340, "none"]];
const CityEras: React.FC<{ dur: number }> = ({ dur }) => {
  const fr = useCurrentFrame();
  const seg = dur / ERAS.length;
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {ERAS.map(([src, h, flt], i) => {
        const a = i * seg, o = interpolate(fr, [a - 5, a + 2, a + seg - 2, a + seg + 5], [0, 1, 1, i === ERAS.length - 1 ? 1 : 0], clamp);
        if (o <= 0) return null;
        const z = interpolate(fr, [a, a + seg], [1.0, 1.06], clamp);
        return (
          <AbsoluteFill key={src} style={{ opacity: o }}>
            <Img src={staticFile(src)} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", filter: "blur(28px) brightness(.45) saturate(1.1)", transform: "scale(1.2)" }} />
            <div style={{ position: "absolute", left: 0, right: 0, top: 860 - h / 2, height: h, overflow: "hidden", boxShadow: "0 0 60px rgba(0,0,0,.8)" }}>
              <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${z})`, filter: flt }} />
            </div>
          </AbsoluteFill>
        );
      })}
    </AbsoluteFill>
  );
};

const AstroToAI: React.FC<{ dur: number }> = ({ dur }) => {
  const fr = useCurrentFrame();
  const z = interpolate(fr, [0, dur], [1.0, 2.6], { ...clamp, easing: Easing.in(Easing.cubic) });
  const glint = interpolate(fr, [dur * 0.55, dur], [0, 1], clamp);
  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden" }}>
      <Img src={staticFile("mccandless.jpg")} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover",
        transformOrigin: "52% 33%", transform: `scale(${z})` }} />
      <SpaceSparkle intensity={0.6} />
      <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 46%, rgba(220,250,255,${glint}) 0%, rgba(127,227,255,${0.7 * glint}) 18%, rgba(0,0,0,${0.85 * glint}) 60%)` }} />
    </AbsoluteFill>
  );
};

const EarthShrink: React.FC<{ dur: number }> = ({ dur }) => {
  const fr = useCurrentFrame();
  const sc = interpolate(fr, [0, dur], [1.25, 0.012], { ...clamp, easing: Easing.in(Easing.cubic) });
  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden" }}>
      <SpaceSparkle intensity={interpolate(fr, [0, dur], [0.2, 1], clamp)} />
      <div style={{ position: "absolute", left: 540 - 540, top: 860 - 540, width: 1080, height: 1080, borderRadius: "50%", overflow: "hidden",
        transform: `scale(${sc})`, boxShadow: "0 0 80px rgba(120,180,255,.5)" }}>
        <Img src={staticFile("bluemarble.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover", transform: "scale(1.03)" }} />
      </div>
    </AbsoluteFill>
  );
};

const FadeIn: React.FC<{ frames: number; children: React.ReactNode }> = ({ frames, children }) => {
  const fr = useCurrentFrame();
  return <AbsoluteFill style={{ opacity: interpolate(fr, [0, frames], [0, 1], clamp) }}>{children}</AbsoluteFill>;
};
// the end of the strike shot (the surprised face), slowed down with a slow push-in
const SlowFace: React.FC<{ dur: number }> = ({ dur }) => {
  const fr = useCurrentFrame();
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#000" }}>
      <OffthreadVideo src={staticFile("face.mp4")} startFrom={f(0.9)} playbackRate={0.72} muted style={{ width: "100%", height: "100%", objectFit: "cover",
        transform: `scale(${interpolate(fr, [0, dur], [1.1, 1.7], { ...clamp, easing: Easing.in(Easing.quad) })})`, transformOrigin: "50% 30%" }} />
    </AbsoluteFill>
  );
};

// The snowy night: the chimp rubs two flints, sparks by accident (0:13.6), freezes, eyes light up (0:14.4); slow push into the eyes.
const EYES = "508px 559px";
const SnowChimp: React.FC<{ surprise: number; dur: number }> = ({ surprise, dur }) => {
  const fr = useCurrentFrame();
  const z = fr < surprise ? interpolate(fr, [f(PRE), surprise], [1.0, 1.06], clamp)
    : interpolate(fr, [surprise, dur], [1.06, 2.7], { ...clamp, easing: Easing.in(Easing.cubic) });
  const fogX = Math.sin(fr / 40) * 60;
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#000" }}>
      <OffthreadVideo src={staticFile("chimp_full.mp4")} muted style={{ width: "100%", height: "100%", objectFit: "cover", transformOrigin: EYES, transform: `scale(${z})` }} />
      {/* light drifting mist */}
      <AbsoluteFill style={{ opacity: interpolate(fr, [surprise, dur], [0.55, 0.15], clamp), transform: `translateX(${fogX}px)`,
        background: "radial-gradient(ellipse at 20% 80%, rgba(170,190,210,.35) 0%, rgba(0,0,0,0) 45%), radial-gradient(ellipse at 85% 65%, rgba(170,190,210,.28) 0%, rgba(0,0,0,0) 40%), linear-gradient(to top, rgba(160,180,200,.25), rgba(0,0,0,0) 45%)" }} />
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 40%, rgba(0,0,0,0) 40%, rgba(0,0,0,.6) 100%)" }} />
    </AbsoluteFill>
  );
};

export const Short: React.FC = () => {
  const withMusic = (getInputProps() as any).music !== false;
  const START = T0, SPARK = 13.6, FACE = 14.37, ZOOM = 16.56;   // song beats: start, flint spark, eyes light up (the rise), dive
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <Sequence from={-f(T0)}>
      {/* one shot: the chimp in the snow, flints, the accidental spark, the surprise, slow push into the eyes */}
      <Sequence from={f(START)} durationInFrames={f(ZOOM) - f(START)}>
        <SnowChimp surprise={f(FACE) - f(START)} dur={f(ZOOM) - f(START)} />
      </Sequence>
      <Flash at={f(SPARK)} color="#ffcf8a" peak={0.22} len={6} />
      {/* he starts to think: maths comes alive from the moment his eyes light up */}
      <Sequence from={f(FACE)} durationInFrames={f(ZOOM) - f(FACE)}>
        <Remembering dur={f(ZOOM) - f(FACE)} />
        <MathOverlay from={2} every={2} life={26} opacity={0.8} />
      </Sequence>
      {/* the dive: through the eyes into the brain */}
      <Sequence from={f(ZOOM)} durationInFrames={f(DROP) - f(ZOOM)}><BrainRewind dur={f(DROP) - f(ZOOM)} /></Sequence>
      <BeatMath />
      <LightBurst at={f(FACE)} seed="face" strength={0.9} cx={508} cy={559} />
      {/* drop: everything humanity built */}
      {SHOTS.map(([src, , off, z0, z1], k) => {
        const a = f(starts[k]), d = f(starts[k + 1]) - a;
        return (
          <Sequence key={k} from={a} durationInFrames={d}>
            {src === "AI" ? <AIShot dur={d} /> : src === "EARTH" ? <EarthShrink dur={d} /> : src === "ASTRO" ? <AstroToAI dur={d} /> : src === "CITY" ? <CityEras dur={d} /> : src === "END" ? <EndShot dur={d} /> : src.endsWith(".jpg") ? <><Photo src={src} dur={d} from={z0} to={z1} origin="50% 46%" ease={Easing.out(Easing.cubic)} />{src.startsWith("jwst") && <SpaceSparkle />}</> : <Clip src={src} dur={d} zoom={[z0, z1]} start={f(off)} filter="contrast(1.1) saturate(1.05)" />}
            {["rocket.mp4", "apollo.mp4", "moon.mp4", "earth.mp4"].includes(src) && <SpaceSparkle intensity={0.8} />}
            {src !== "AI" && src !== "END" && src !== "ASTRO" && src !== "EARTH" && src !== "artemis.mp4" && src !== "messenger.mp4" && src !== "moonflag.mp4" && !src.endsWith(".jpg") && <AbsoluteFill style={{ opacity: 0.16, mixBlendMode: "screen" }}><Network fire={0.3} pulseSpeed={20} /></AbsoluteFill>}
          </Sequence>
        );
      })}
      <Sequence from={f(starts[SHOTS.findIndex((x) => x[0] === "nuke.mp4")])} durationInFrames={f(starts[SHOTS.findIndex((x) => x[0] === "moonflag.mp4")]) - f(starts[SHOTS.findIndex((x) => x[0] === "nuke.mp4")]) - 4}><MathOverlay from={0} every={4} life={30} opacity={0.5} color="#cfe8ff" /></Sequence>
      {/* hits */}
      <Flash at={f(FACE)} peak={0.35} />
      <Flash at={f(DROP)} color="#e9fbff" peak={1} len={10} />
      {starts.slice(1, -2).map((s) => <Flash key={s} at={f(s)} peak={0.3} len={5} />)}
      </Sequence>
      <Grain />
      {withMusic && <Sequence from={f(PRE)}><Audio src={staticFile("song.wav")} startFrom={f(MUSIC_IN)} endAt={f(T0 + TOTAL_S)}
        volume={(fr) => interpolate(MUSIC_IN + fr / FPS, [VOICE2_AT - 0.3, VOICE2_AT, VOICE2_AT + 3.4, VOICE2_AT + 4.4], [1, 0.45, 0.45, 0.85], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} /></Sequence>}
      {/* Armstrong (Apollo 11, NASA, public domain): first half on the chimp, second half, echoing, as the screen dies */}
      <Sequence from={f(VOICE1_AT)}><Audio src={staticFile("armstrong_p1.wav")} /></Sequence>
      <Sequence from={f(VOICE2_AT - T0)}><Audio src={staticFile(withMusic ? "armstrong_p2.wav" : "armstrong_p2_loud.wav")} volume={(fr) => interpolate(fr, [f(T0 + TOTAL_S - VOICE2_AT) - 20, f(T0 + TOTAL_S - VOICE2_AT)], [1, 0], clamp)} /></Sequence>
    </AbsoluteFill>
  );
};
