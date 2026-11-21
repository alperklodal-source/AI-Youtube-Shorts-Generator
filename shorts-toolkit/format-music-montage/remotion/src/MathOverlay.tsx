import React from "react";
import { AbsoluteFill, interpolate, random, useCurrentFrame } from "remotion";

// Famous equations of human discovery, drifting in behind the picture.
const EQS = [
  "a² + b² = c²", "π ≈ 3.14159", "E = mc²", "F = ma", "e^{iπ} + 1 = 0", "∇ · E = ρ / ε₀", "iħ ∂ψ/∂t = Ĥψ",
  "∫ f(x) dx", "F = G m₁m₂ / r²", "∇ × B = μ₀J + μ₀ε₀ ∂E/∂t", "Δx · Δp ≥ ħ/2", "S = k log W", "1 + 1 = 2",
  "f(x) = Σ aₙ xⁿ", "λ = h / p", "V = IR", "σ(z) = 1 / (1 + e⁻ᶻ)", "∂L/∂w", "c = 299 792 458 m/s", "0, 1, 1, 2, 3, 5, 8, 13",
];

// `from` = frame (relative to this overlay) where the first equation appears; density ramps up with time.
export const MathOverlay: React.FC<{ from?: number; every?: number; life?: number; color?: string; opacity?: number }> = ({
  from = 0, every = 6, life = 48, color = "#f2d7a0", opacity = 0.75,
}) => {
  const f = useCurrentFrame();
  const items = [] as React.ReactNode[];
  for (let k = 0; k * every + from <= f; k++) {
    const born = from + k * every, age = f - born;
    if (age > life) continue;
    const x = 60 + random(`mx${k}`) * 780, y = 140 + random(`my${k}`) * 1500;
    const size = 34 + random(`ms${k}`) * 46;
    const fi = Math.min(8, life / 4), fo = Math.min(12, life / 3);
    const o = interpolate(age, [0, fi, life - fo, life], [0, 1, 1, 0]) * opacity;
    const drift = age * (0.6 + random(`md${k}`) * 1.2);
    items.push(
      <div key={k} style={{ position: "absolute", left: x, top: y - drift, fontFamily: "DejaVu Serif, serif", fontStyle: "italic", fontSize: size,
        color, opacity: o, whiteSpace: "nowrap", textShadow: `0 0 18px ${color}99` }}>{EQS[k % EQS.length]}</div>
    );
  }
  return <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "screen" }}>{items}</AbsoluteFill>;
};
