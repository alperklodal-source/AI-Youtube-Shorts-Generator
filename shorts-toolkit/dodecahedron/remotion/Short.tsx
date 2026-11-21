import React from "react";
import { AbsoluteFill, Audio, OffthreadVideo, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig, Easing, Sequence } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { geoMercator, geoPath } from "d3-geo";
import { feature } from "topojson-client";
import world from "world-atlas/countries-50m.json";
import narration from "./narration.json";
import { DodecaMesh } from "./Dodeca";

const fontCss = `
@font-face{font-family:Cinzel;src:url(${staticFile("cinzel.woff2")}) format('woff2');font-weight:900}
@font-face{font-family:Mont;src:url(${staticFile("mont.woff2")}) format('woff2');font-weight:800}`;

const FPS = 30;
const AUDIO_OFFSET = 0.15; // seconds of silence before the first word
const t = (s: number) => Math.round((s + AUDIO_OFFSET) * FPS);
const seg = narration.segments;
const S = {
  a: 0, b: t(seg[1].start - 0.2), c: t(seg[4].start - 0.2), d: t(seg[5].start - 0.2),
  nobody: t(seg[6].start), e: t(seg[7].start - 0.25), end: t(seg[8].start),
};
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const GOLD = "#e8b765";

// ---------- captions: 1–3 word chunks timed by character share ----------
type Chunk = { text: string; from: number; to: number; key: boolean };
const KEY = /(holes|why|hundred|britain|hungary|strange|italy|who|2023|england|one hand|breaks|not one|ritual|tool)/i;
const chunks: Chunk[] = [];
seg.forEach((s) => {
  const words = s.text.replace(/\.\.\./g, "…").split(" ");
  const groups: string[] = [];
  let cur: string[] = [];
  words.forEach((w) => {
    cur.push(w);
    if (cur.length === 3 || /[…?.,]$/.test(w)) { groups.push(cur.join(" ")); cur = []; }
  });
  if (cur.length) groups.push(cur.join(" "));
  const total = groups.reduce((n, g) => n + g.length, 0);
  let at = s.start;
  groups.forEach((g) => {
    const d = ((s.end - s.start) * g.length) / total;
    chunks.push({ text: g, from: t(at), to: t(at + d), key: KEY.test(g) });
    at += d;
  });
});

const Captions: React.FC = () => {
  const f = useCurrentFrame();
  const c = chunks.find((x) => f >= x.from && f < x.to + 4);
  if (!c) return null;
  const p = spring({ frame: f - c.from, fps: FPS, config: { damping: 14, stiffness: 220 } });
  return (
    <div style={{ position: "absolute", top: 1430, width: "100%", textAlign: "center", padding: "0 90px", boxSizing: "border-box" }}>
      <span style={{
        fontFamily: "Mont", fontWeight: 800, fontSize: 84, lineHeight: 1.1, textTransform: "uppercase",
        color: c.key ? GOLD : "#fff", display: "inline-block", transform: `scale(${0.85 + 0.15 * p})`,
        textShadow: "0 0 18px rgba(0,0,0,.95), 0 6px 0 rgba(0,0,0,.85)", WebkitTextStroke: "3px rgba(0,0,0,.6)",
      }}>{c.text.replace(/…$/, "…")}</span>
    </div>
  );
};

// ---------- atmosphere ----------
const Backdrop: React.FC<{ tint?: string }> = ({ tint = "#2a1a0c" }) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 42%, ${tint} 0%, #0b0705 55%, #000 100%)` }}>
      {[0, 1, 2].map((i) => (
        <div key={i} style={{
          position: "absolute", width: 1400, height: 700, left: -200 + Math.sin(f / (90 + i * 30) + i) * 160, top: 500 + i * 380,
          background: "radial-gradient(ellipse, rgba(200,170,130,.07) 0%, rgba(0,0,0,0) 70%)", filter: "blur(20px)",
        }} />
      ))}
    </AbsoluteFill>
  );
};

const Grain: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <svg width="1080" height="1920" style={{ position: "absolute", opacity: 0.09, mixBlendMode: "overlay" }}>
        <filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed={f % 12} /></filter>
        <rect width="100%" height="100%" filter="url(#n)" />
      </svg>
      <AbsoluteFill style={{ boxShadow: "inset 0 0 260px 90px #000" }} />
    </AbsoluteFill>
  );
};

const Label: React.FC<{ text: string; at: number; x: number; y: number; size?: number }> = ({ text, at, x, y, size = 46 }) => {
  const f = useCurrentFrame();
  const o = interpolate(f, [at, at + 8], [0, 1], clamp);
  return (
    <div style={{ position: "absolute", left: x, top: y, opacity: o, transform: `translateY(${(1 - o) * 20}px)`,
      fontFamily: "Cinzel", fontWeight: 900, fontSize: size, color: GOLD, letterSpacing: 4,
      textShadow: "0 0 24px rgba(232,183,101,.45), 0 4px 10px #000" }}>{text}</div>
  );
};

// ---------- the object (scenes A, B, E) ----------
const ObjectScene: React.FC<{ from: number; mode: "reveal" | "detail" | "outro" }> = ({ from, mode }) => {
  const f = useCurrentFrame();
  const g = f + from; // global frame for continuous rotation
  const intro = mode === "reveal" ? interpolate(f, [0, 40], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) }) : 1;
  const scale = mode === "detail" ? interpolate(f, [0, 240], [1.0, 1.15], clamp) : mode === "outro" ? interpolate(f, [0, 150], [0.95, 0.8], clamp) : 0.75 + 0.1 * intro;
  const y = mode === "reveal" ? interpolate(intro, [0, 1], [-1.6, 0.2]) : mode === "detail" ? 0.25 : 0.0;
  const glow = mode === "outro" ? interpolate(f, [0, 60], [0, 1], clamp) : 0.3;
  return (
    <AbsoluteFill style={{ opacity: mode === "reveal" ? intro : 1 }}>
      <ThreeCanvas linear width={1080} height={1920} camera={{ fov: 32, position: [0, 0, 9] }} gl={{ antialias: true, preserveDrawingBuffer: true }}>
        <ambientLight intensity={0.15} />
        <spotLight position={[3, 6, 5]} angle={0.5} penumbra={0.8} intensity={260} color="#ffd9a0" />
        <pointLight position={[-4, -2, 3]} intensity={30} color="#5a7bff" />
        <group position={[0, y, 0]}>
          <DodecaMesh rotY={g * 0.012} rotX={0.35 + Math.sin(g / 70) * 0.15} scale={scale} glow={glow} />
        </group>
      </ThreeCanvas>
    </AbsoluteFill>
  );
};

const Counter: React.FC = () => {
  const f = useCurrentFrame();
  const n = Math.round(interpolate(f, [t(seg[1].start + 1.6), t(seg[1].end - 0.3)], [0, 100], { ...clamp, easing: Easing.out(Easing.quad) }));
  const o = interpolate(f, [t(seg[1].start + 1.5), t(seg[1].start + 1.7), t(seg[2].start - 0.25), t(seg[2].start - 0.05)], [0, 1, 1, 0], clamp);
  return (
    <div style={{ position: "absolute", top: 1010, width: "100%", textAlign: "center", opacity: o }}>
      <div style={{ fontFamily: "Cinzel", fontWeight: 900, fontSize: 170, color: GOLD, textShadow: "0 0 40px rgba(232,183,101,.5)" }}>{n}{n === 100 ? "+" : ""}</div>
      <div style={{ fontFamily: "Mont", fontWeight: 800, fontSize: 40, color: "#d9cbb5", letterSpacing: 10 }}>FOUND ACROSS EUROPE</div>
    </div>
  );
};


// ---------- real museum photos (Wikimedia Commons, CC licensed) ----------
const Photo: React.FC<{ src: string; dur: number; from?: number; to?: number; fx?: [number, number]; tx?: [number, number]; place?: string; card?: boolean; fadeIn?: number }> = ({ src, dur, from = 1.0, to = 1.18, fx = [50, 50], tx = [50, 50], place, card, fadeIn = 5 }) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [0, dur], [0, 1], { ...clamp, easing: Easing.inOut(Easing.sin) });
  const sc = from + (to - from) * p;
  const ox = fx[0] + (tx[0] - fx[0]) * p, oy = fx[1] + (tx[1] - fx[1]) * p;
  const o = fadeIn ? interpolate(f, [0, fadeIn], [0, 1], clamp) : 1;
  return (
    <AbsoluteFill style={{ opacity: o }}>
      {card ? (
        <div style={{ position: "absolute", left: 90, right: 90, top: 560, height: 660, transform: `rotate(-2deg) scale(${sc})`, border: "14px solid #efe6d6",
          boxShadow: "0 30px 80px #000", overflow: "hidden", background: "#fff" }}>
          <img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "sepia(.25) contrast(1.05)" }} />
        </div>
      ) : (
        <>
          <img src={staticFile(src)} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", transformOrigin: `${ox}% ${oy}%`,
            transform: `scale(${sc})`, filter: "contrast(1.12) saturate(.85) sepia(.18) brightness(.9)" }} />
          <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,.55) 0%, rgba(0,0,0,0) 25%, rgba(0,0,0,0) 55%, rgba(0,0,0,.75) 100%)" }} />
        </>
      )}
      {place && (
        <div style={{ position: "absolute", top: 190, left: 70, fontFamily: "Mont", fontWeight: 800, fontSize: 30, letterSpacing: 4, color: "#efe2c8",
          background: "rgba(0,0,0,.45)", padding: "8px 18px", borderLeft: `5px solid ${GOLD}` }}>{place}</div>
      )}
    </AbsoluteFill>
  );
};

// ---------- map (scene C) ----------
const countries = (feature(world as any, (world as any).objects.countries) as any).features;
const projection = geoMercator().center([9, 49.5]).scale(2350).translate([540, 760]);
const path = geoPath(projection);
const SITES: [number, number][] = [
  [-1.5, 52.6], [-2.4, 51.4], [0.2, 52.3], [-1.1, 53.9], [1.0, 51.3], [2.3, 48.9], [4.8, 45.8], [6.2, 48.7], [3.1, 50.6],
  [4.4, 50.8], [5.6, 50.6], [5.9, 51.8], [6.1, 49.6], [6.9, 50.9], [7.6, 49.9], [8.7, 49.4], [7.4, 46.9], [8.5, 47.4],
  [11.4, 47.3], [14.3, 48.3], [16.4, 48.2], [17.6, 47.7], [19.0, 47.5], [18.2, 46.1],
];

const MapScene: React.FC<{ italyAt: number }> = ({ italyAt }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const zoom = interpolate(f, [0, 170], [1.08, 1.0], clamp);
  return (
    <AbsoluteFill style={{ opacity: interpolate(f, [0, 10], [0, 1], clamp) }}>
      <svg width={1080} height={1920} style={{ transform: `scale(${zoom})` }}>
        <defs>
          <radialGradient id="dot"><stop offset="0" stopColor="#ffe2a8" /><stop offset=".4" stopColor={GOLD} /><stop offset="1" stopColor="rgba(232,183,101,0)" /></radialGradient>
        </defs>
        {countries.map((c: any, i: number) => (
          <path key={i} d={path(c) || ""} fill="#2b2017" stroke="#6b5236" strokeWidth={1.4} />
        ))}
        {SITES.map(([lon, lat], i) => {
          const [x, y] = projection([lon, lat])!;
          const order = (lon + 3) / 23; // west → east reveal
          const s = spring({ frame: f - 6 - order * 60, fps, config: { damping: 10 } });
          return <circle key={i} cx={x} cy={y} r={34 * s} fill="url(#dot)" />;
        })}
      </svg>
      <Label text="BRITAIN" at={8} x={110} y={480} size={50} />
      <Label text="HUNGARY" at={62} x={700} y={1000} size={50} />
      {(() => {
        const it = countries.find((c: any) => String(c.id) === "380");
        const k = interpolate(f, [italyAt, italyAt + 10], [0, 1], clamp);
        const pulse = 0.55 + 0.45 * Math.abs(Math.sin((f - italyAt) / 7));
        return k > 0 ? (
          <svg width={1080} height={1920} style={{ position: "absolute", transform: `scale(${zoom})` }}>
            <path d={path(it) || ""} fill={`rgba(200,40,30,${0.35 * k * pulse})`} stroke="#ff5a44" strokeWidth={4} opacity={k} />
          </svg>
        ) : null;
      })()}
      <Label text="ITALY: ALMOST NONE" at={italyAt + 6} x={250} y={1330} size={50} />
    </AbsoluteFill>
  );
};

// ---------- theories (scene D) ----------
const THEORIES = ["CANDLE HOLDER?", "DICE?", "SOWING CALENDAR?"];
const Theories: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const starts = [4, t(seg[5].start + 1.15) - S.d, t(seg[5].start + 1.75) - S.d];
  const nob = S.nobody - S.d;
  const stamp = spring({ frame: f - nob, fps, config: { damping: 9, stiffness: 180 } });
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: 120, width: "100%", textAlign: "center", fontFamily: "Cinzel", fontWeight: 900, fontSize: 340, color: "rgba(232,183,101,.12)" }}>?</div>
      {THEORIES.map((th, i) => {
        const s = spring({ frame: f - starts[i], fps, config: { damping: 13 } });
        const strike = interpolate(f, [nob - 4 + i * 2, nob + 6 + i * 2], [0, 100], clamp);
        return (
          <div key={i} style={{ position: "absolute", left: 120, right: 120, top: 330 + i * 200, height: 150, opacity: s * interpolate(f, [nob, nob + 8], [1, 0.35], clamp),
            transform: `translateX(${(1 - s) * (i % 2 ? 300 : -300)}px)`, border: `3px solid ${GOLD}`, background: "rgba(20,12,6,.75)",
            display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "Mont", fontWeight: 800, fontSize: 62, color: "#f3e6cf" }}>
            {th}
            <div style={{ position: "absolute", left: 30, top: 72, height: 8, width: `${strike * 0.9}%`, background: "#c0392b" }} />
          </div>
        );
      })}
      <div style={{ position: "absolute", top: 960, width: "100%", textAlign: "center", opacity: stamp,
        transform: `rotate(-8deg) scale(${2.2 - 1.2 * stamp})`, fontFamily: "Cinzel", fontWeight: 900, fontSize: 120, color: "#e0412f",
        textShadow: "0 0 30px rgba(224,65,47,.5), 0 6px 12px #000" }}>EVERY THEORY<br />BREAKS</div>
    </AbsoluteFill>
  );
};

const EndCard: React.FC = () => {
  const f = useCurrentFrame();
  const o = interpolate(f, [0, 12], [0, 1], clamp);
  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", paddingTop: 230, opacity: o }}>
      <div style={{ fontFamily: "Cinzel", fontWeight: 900, fontSize: 110, color: GOLD, textAlign: "center", letterSpacing: 3, textShadow: "0 0 36px rgba(232,183,101,.55)" }}>TOOL OR<br />RITUAL?</div>
      <div style={{ marginTop: 34, whiteSpace: "nowrap", fontFamily: "Mont", fontWeight: 800, fontSize: 44, color: "#fff", background: "rgba(192,57,43,.9)", padding: "14px 34px", opacity: interpolate(f, [30, 40], [0, 1], clamp) }}>WHAT DO YOU THINK? COMMENT BELOW</div>
    </AbsoluteFill>
  );
};

const Flash: React.FC<{ at: number }> = ({ at }) => {
  const f = useCurrentFrame();
  const o = interpolate(f, [at - 3, at, at + 7], [0, 0.55, 0], clamp);
  return <AbsoluteFill style={{ background: "#fff3dc", opacity: o, mixBlendMode: "screen" }} />;
};

const Clip: React.FC<{ src: string; place?: string; start?: number }> = ({ src, place, start = 0 }) => (
  <AbsoluteFill>
    <OffthreadVideo src={staticFile(src)} startFrom={start} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
    <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,.5) 0%, rgba(0,0,0,0) 25%, rgba(0,0,0,0) 55%, rgba(0,0,0,.8) 100%)" }} />
    {place && <div style={{ position: "absolute", top: 190, left: 70, fontFamily: "Mont", fontWeight: 800, fontSize: 30, letterSpacing: 4, color: "#efe2c8", background: "rgba(0,0,0,.45)", padding: "8px 18px", borderLeft: `5px solid ${GOLD}` }}>{place}</div>}
  </AbsoluteFill>
);

const Tag: React.FC<{ text: string }> = ({ text }) => (
  <div style={{ position: "absolute", top: 190, left: 70, fontFamily: "Mont", fontWeight: 800, fontSize: 28, letterSpacing: 4, color: "#cfc3ad", background: "rgba(0,0,0,.45)", padding: "8px 18px", borderLeft: "5px solid #888" }}>{text}</div>
);

export const Short: React.FC = () => {
  const T2 = t(2.0), MAP = t(seg[1].start + 1.5), DIG = S.b, IT = t(seg[2].end - 1.4);
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <style>{fontCss}</style>
      <Backdrop />
      {/* HOOK: real close-ups */}
      <Sequence from={0} durationInFrames={T2}><Photo src="p30.jpg" dur={T2} from={1.18} to={1.0} fx={[55, 55]} tx={[55, 55]} fadeIn={0} /></Sequence>
      <Sequence from={T2} durationInFrames={DIG - T2}><Photo src="p25.jpg" dur={DIG - T2} from={1.1} to={1.55} fx={[50, 52]} tx={[48, 55]} place="TONGEREN, BELGIUM" /></Sequence>
      <Sequence from={0} durationInFrames={t(seg[0].end - 0.4)}><Label text="ROMAN DODECAHEDRON" at={-8} x={110} y={300} size={50} /></Sequence>
      <Sequence from={0} durationInFrames={T2}>
        <div style={{ position: "absolute", top: 380, width: "100%", textAlign: "center", fontFamily: "Cinzel", fontWeight: 900, fontSize: 230, color: GOLD,
          textShadow: "0 0 50px rgba(232,183,101,.6), 0 8px 18px #000" }}>WHY?</div>
      </Sequence>
      {/* found: excavation then map */}
      <Sequence from={DIG} durationInFrames={MAP - DIG}><Clip src="dig.mp4" place="EXCAVATION · PERGE" /></Sequence>
      <Sequence from={MAP} durationInFrames={S.c - MAP}><Backdrop tint="#1d140c" /><MapScene italyAt={IT - MAP} /></Sequence>
      <Sequence from={t(seg[3].start)} durationInFrames={t(seg[3].end + 0.3) - t(seg[3].start)}>
        <AbsoluteFill style={{ background: "rgba(0,0,0,.55)" }} />
        <div style={{ position: "absolute", top: 560, width: "100%", textAlign: "center", fontFamily: "Cinzel", fontWeight: 900, fontSize: 380, color: GOLD, textShadow: "0 0 60px rgba(232,183,101,.6)" }}>?</div>
      </Sequence>
      {/* 2023 find: 3D illustration */}
      <Sequence from={S.c} durationInFrames={S.d - S.c}>
        <ObjectScene from={S.c} mode="detail" />
        <Tag text="3D ILLUSTRATION" />
        <Label text="ENGLAND · 2023" at={8} x={90} y={300} size={56} />
        <Label text="NEAR-PERFECT" at={t(seg[4].start + 2.2) - S.c} x={600} y={1260} />
        <Label text="FITS IN ONE HAND" at={t(seg[4].start + 3.9) - S.c} x={90} y={1320} />
      </Sequence>
      {/* theories */}
      <Sequence from={S.d} durationInFrames={S.e - S.d}><Backdrop tint="#2a0f0a" /><AbsoluteFill style={{ opacity: 0.22, filter: "blur(6px)" }}><Photo src="p30.jpg" dur={S.e - S.d} from={1.1} to={1.25} /></AbsoluteFill><Theories /></Sequence>
      {/* no texts: ruins */}
      <Sequence from={S.e} durationInFrames={S.end - S.e}><Clip src="ruins.mp4" place="ROMAN RUINS · PERGE" />
        <Label text="ROMAN TEXTS THAT MENTION IT: 0" at={10} x={70} y={1300} size={44} /></Sequence>
      {/* outro */}
      <Sequence from={S.end}><Backdrop tint="#2e1d0b" /><ObjectScene from={S.end} mode="outro" /><EndCard /></Sequence>

      <Counter />
      {[T2, DIG, MAP, t(seg[3].start), S.c, S.d, S.e, S.end].map((a) => <Flash key={a} at={a} />)}
      <Captions />
      <Grain />
      <Audio src={staticFile("mix.wav")} />
    </AbsoluteFill>
  );
};
