import React from "react";
import { AbsoluteFill, interpolate, random, useCurrentFrame } from "remotion";

// Decoration for the space shots: twinkling stars, drifting star dust and a soft light leak.
export const SpaceSparkle: React.FC<{ intensity?: number }> = ({ intensity = 1 }) => {
  const f = useCurrentFrame();
  const stars = Array.from({ length: 90 }).map((_, i) => {
    const x = random(`sx${i}`) * 1080, y = random(`sy${i}`) * 1920;
    const r = 1 + random(`sr${i}`) * 2.6;
    const tw = 0.35 + 0.65 * Math.abs(Math.sin(f / (6 + random(`st${i}`) * 10) + i));
    return <circle key={i} cx={x} cy={y - f * (0.3 + random(`sv${i}`) * 0.8)} r={r} fill="#ffffff" opacity={tw * intensity} />;
  });
  const flares = [0, 1, 2].map((k) => {
    const x = 160 + random(`fx${k}`) * 760, y = 300 + random(`fy${k}`) * 1300;
    const s = 0.6 + 0.4 * Math.abs(Math.sin(f / 9 + k * 2));
    return (
      <g key={k} transform={`translate(${x},${y}) rotate(${f * 0.6 + k * 30}) scale(${s})`} opacity={0.8 * intensity}>
        <line x1={-70} y1={0} x2={70} y2={0} stroke="#dff6ff" strokeWidth={2} />
        <line x1={0} y1={-70} x2={0} y2={70} stroke="#dff6ff" strokeWidth={2} />
        <circle r={7} fill="#ffffff" />
      </g>
    );
  });
  const leak = interpolate(Math.sin(f / 14), [-1, 1], [0.12, 0.3]) * intensity;
  return (
    <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "screen" }}>
      <svg width={1080} height={1920}>
        <defs><filter id="sg"><feGaussianBlur stdDeviation="2.2" /></filter></defs>
        <g filter="url(#sg)">{stars}</g>
        {flares}
      </svg>
      <AbsoluteFill style={{ background: `radial-gradient(ellipse at 85% 10%, rgba(140,190,255,${leak}) 0%, rgba(0,0,0,0) 55%)` }} />
    </AbsoluteFill>
  );
};
