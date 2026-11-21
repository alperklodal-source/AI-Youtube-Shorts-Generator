import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
const fontCss = `
@font-face{font-family:Cinzel;src:url(${staticFile("cinzel.woff2")}) format('woff2');font-weight:900}
@font-face{font-family:Mont;src:url(${staticFile("mont.woff2")}) format('woff2');font-weight:800}`;
const GOLD = "#e8b765", JADE = "#8fd3a8", RUBY = "#ff5a4a";
const ALIGN = "translate(8px, -92px)";
const Split: React.FC<{ z?: number; boost?: boolean }> = ({ z = 1.12, boost }) => (
  <AbsoluteFill style={{ transform: `scale(${z})`, transformOrigin: "52% 42%" }}>
    <Img src={staticFile("c9_red.jpg")} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", filter: boost ? "saturate(1.45) contrast(1.15) brightness(1.08)" : "saturate(1.25) contrast(1.12)" }} />
    {boost && <AbsoluteFill style={{ mixBlendMode: "screen", background: "radial-gradient(ellipse at 70% 52%, rgba(255,90,60,.45) 0%, rgba(0,0,0,0) 55%)" }} />}
    <div style={{ position: "absolute", inset: 0, clipPath: "inset(0 50% 0 0)" }}>
      <Img src={staticFile("c5_jade.jpg")} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", transform: ALIGN, filter: boost ? "saturate(1.45) contrast(1.12) brightness(1.15)" : "saturate(1.3) contrast(1.1) brightness(1.05)" }} />
    </div>
    <div style={{ position: "absolute", left: "50%", top: 0, bottom: 0, width: boost ? 4 : 8, marginLeft: boost ? -2 : -4, background: "#fff", boxShadow: boost ? "0 0 22px 6px rgba(255,245,225,.85)" : "0 0 50px 18px rgba(255,245,225,.75)" }} />
  </AbsoluteFill>
);
const Shade: React.FC = () => <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,.75) 0%, rgba(0,0,0,0) 30%, rgba(0,0,0,0) 62%, rgba(0,0,0,.8) 100%)" }} />;
const big = (c: string, size: number): React.CSSProperties => ({ fontFamily: "Mont", fontWeight: 800, fontSize: size, color: c, lineHeight: 0.95, letterSpacing: -1,
  textShadow: "0 8px 0 rgba(0,0,0,.85), 0 0 40px rgba(0,0,0,.9)", WebkitTextStroke: "4px #000", textTransform: "uppercase" });
const outline = (w: number, c = "#000") => [-w, 0, w].flatMap((x) => [-w, 0, w].map((y) => `${x}px ${y}px 0 ${c}`)).join(", ");
const clean = (c: string, size: number, glow: string): React.CSSProperties => ({ fontFamily: "Mont", fontWeight: 800, fontSize: size, color: c, lineHeight: 1, textTransform: "uppercase",
  textShadow: `${outline(4)}, ${outline(7, "rgba(0,0,0,.85)")}, 0 0 40px ${glow}, 0 10px 24px rgba(0,0,0,.9)` });
export const Cover: React.FC<{ v: "a" | "a2" | "b" | "c" }> = ({ v }) => (
  <AbsoluteFill style={{ background: "#000" }}>
    <style>{fontCss}</style>
    {v === "a" && <>
      <Split /><Shade />
      <div style={{ position: "absolute", top: 150, width: "100%", textAlign: "center" }}><span style={big("#fff", 120)}>Same cup.</span></div>
      <div style={{ position: "absolute", top: 1440, left: 60, textAlign: "left" }}><span style={big(JADE, 150)}>Green</span></div>
      <div style={{ position: "absolute", top: 1440, right: 60, textAlign: "right" }}><span style={big(RUBY, 150)}>Red</span></div>
      <div style={{ position: "absolute", top: 1620, width: "100%", textAlign: "center", fontFamily: "Cinzel", fontWeight: 900, fontSize: 56, color: GOLD, letterSpacing: 6, textShadow: "0 4px 12px #000" }}>1,600 YEARS OLD</div>
    </>}
    {v === "a2" && <>
      <AbsoluteFill style={{ transform: "translateY(95px) scale(1.16)", transformOrigin: "50% 30%" }}>
        <Img src={staticFile("c9_cover_red.jpg")} style={{ position: "absolute", width: "100%", height: "100%", filter: "saturate(1.2) contrast(1.1) brightness(1.06)" }} />
        <AbsoluteFill style={{ mixBlendMode: "screen", background: "radial-gradient(ellipse at 68% 50%, rgba(255,90,60,.45) 0%, rgba(0,0,0,0) 55%)" }} />
        <div style={{ position: "absolute", inset: 0, clipPath: "inset(0 50% 0 0)" }}>
          <Img src={staticFile("c5_cover_jade.jpg")} style={{ position: "absolute", width: "100%", height: "100%", filter: "saturate(1.15) contrast(1.08)" }} />
        </div>
        <div style={{ position: "absolute", left: "50%", top: 0, bottom: 0, width: 4, marginLeft: -2, background: "#fff", boxShadow: "0 0 22px 6px rgba(255,245,225,.85)" }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,.62) 0%, rgba(0,0,0,.4) 22%, rgba(0,0,0,0) 34%, rgba(0,0,0,0) 72%, rgba(0,0,0,.55) 100%)" }} />
      <div style={{ position: "absolute", top: 170, width: "100%", textAlign: "center" }}><span style={clean("#fff", 156, "rgba(0,0,0,.6)")}>Same cup.</span></div>
      <div style={{ position: "absolute", top: 1170, left: 100, width: 440, textAlign: "center" }}><span style={clean("#3DDC97", 112, "rgba(61,220,151,.75)")}>Green</span></div>
      <div style={{ position: "absolute", top: 1170, right: 100, width: 440, textAlign: "center" }}><span style={clean(RUBY, 112, "rgba(255,90,74,.75)")}>Red</span></div>
      <div style={{ position: "absolute", top: 1370, width: "100%", textAlign: "center" }}><span style={{ fontFamily: "Mont", fontWeight: 800, fontSize: 54, color: "#fff", letterSpacing: 3, background: "rgba(0,0,0,.72)", padding: "12px 30px", borderRadius: 40 }}>1,600 YEARS OLD</span></div>
    </>}
    {v === "b" && <>
      <Img src={staticFile("c9_red.jpg")} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", transform: "scale(1.18)", transformOrigin: "52% 45%", filter: "saturate(1.35) contrast(1.15)" }} />
      <AbsoluteFill style={{ mixBlendMode: "screen", background: "radial-gradient(ellipse at 52% 52%, rgba(255,110,80,.65) 0%, rgba(255,50,30,.25) 30%, rgba(0,0,0,0) 60%)" }} />
      <Shade />
      <div style={{ position: "absolute", top: 140, width: "100%", textAlign: "center" }}><span style={big(GOLD, 136)}>Roman<br />nanotech?</span></div>
      <div style={{ position: "absolute", top: 1560, width: "100%", textAlign: "center" }}><span style={{ fontFamily: "Mont", fontWeight: 800, fontSize: 60, color: "#fff", background: "rgba(0,0,0,.7)", padding: "14px 30px" }}>1,600 YEARS AGO</span></div>
    </>}
    {v === "c" && <>
      <Split z={1.18} /><Shade />
      <div style={{ position: "absolute", top: 150, width: "100%", textAlign: "center" }}><span style={big("#fff", 128)}>What colour<br />is this?</span></div>
      <div style={{ position: "absolute", top: 1560, width: "100%", textAlign: "center" }}><span style={{ fontFamily: "Mont", fontWeight: 800, fontSize: 58, color: "#fff", background: "rgba(192,57,43,.92)", padding: "14px 30px" }}>ROMAN · 1,600 YEARS OLD</span></div>
    </>}
  </AbsoluteFill>
);
