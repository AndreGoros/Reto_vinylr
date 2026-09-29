import React from "react";
import { AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT_SANS, FONT_SERIF, SAFE_TOP } from "../theme";

/** Grano analógico: cambia el seed cada 2 frames => "film grain" real, determinista. */
export const Grain: React.FC<{ opacity?: number }> = ({ opacity = 0.07 }) => {
  const frame = useCurrentFrame();
  const seed = Math.floor(frame / 2) % 12;
  return (
    <AbsoluteFill style={{ opacity, mixBlendMode: "overlay", pointerEvents: "none" }}>
      <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
        <filter id="vinylr-noise">
          <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves={3} seed={seed} stitchTiles="stitch" />
          <feColorMatrix type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.5 0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#vinylr-noise)" />
      </svg>
    </AbsoluteFill>
  );
};

/** Fondo: carátulas desenfocadas (color real del artwork) + bloques diagonales de acento. */
export const Backdrop: React.FC<{
  urlA: string;
  urlB?: string;
  accentA: string;
  accentB: string;
}> = ({ urlA, urlB, accentA, accentB }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const zoom = interpolate(frame, [0, durationInFrames], [1.05, 1.28]);
  const blob: React.CSSProperties = {
    position: "absolute",
    width: 1100,
    height: 1100,
    borderRadius: "50%",
    objectFit: "cover",
    filter: "blur(120px) saturate(1.3) brightness(0.42)",
    transform: `scale(${zoom})`,
  };
  return (
    <AbsoluteFill style={{ background: C.black, overflow: "hidden" }}>
      <Img src={urlA} style={{ ...blob, top: 700, left: -420 }} />
      <Img src={urlB ?? urlA} style={{ ...blob, top: -300, right: -420 }} />
      <div style={{ position: "absolute", width: 1700, height: 460, top: 60, left: -360, background: accentA, opacity: 0.14, transform: "rotate(-16deg)" }} />
      <div style={{ position: "absolute", width: 1700, height: 460, bottom: 120, right: -360, background: accentB, opacity: 0.12, transform: "rotate(-16deg)" }} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(5,5,5,0.5) 0%, rgba(5,5,5,0.2) 30%, rgba(5,5,5,0.3) 60%, rgba(5,5,5,0.9) 100%)" }} />
    </AbsoluteFill>
  );
};

export const Masthead: React.FC = () => (
  <div style={{ position: "absolute", top: SAFE_TOP - 90, left: 64, right: 64, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
    <div style={{ fontFamily: FONT_SANS, fontSize: 24, letterSpacing: 6, color: C.white }}>VINYLR</div>
    <div style={{ width: 44, height: 44, border: `2px solid ${C.white}`, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: FONT_SANS, fontSize: 20, color: C.white }}>V</div>
  </div>
);

/** Vinilo giratorio. `spin` en grados. */
export const Vinyl: React.FC<{ size: number; accent: string; spin: number }> = ({ size, accent, spin }) => (
  <div
    style={{
      width: size,
      height: size,
      borderRadius: "50%",
      background: "radial-gradient(circle at 50% 50%, #101010 0 8%, #050505 8% 100%)",
      boxShadow: "0 30px 60px rgba(0,0,0,0.6)",
      transform: `rotate(${spin}deg)`,
      position: "relative",
    }}
  >
    <div style={{ position: "absolute", inset: 0, borderRadius: "50%", background: "repeating-radial-gradient(circle at 50% 50%, rgba(255,255,255,0.09) 0px, rgba(255,255,255,0.09) 1px, transparent 1px, transparent 7px)" }} />
    {/* brillo para que se note la rotación */}
    <div style={{ position: "absolute", inset: 0, borderRadius: "50%", background: "conic-gradient(from 0deg, transparent 0 20%, rgba(255,255,255,0.10) 25%, transparent 30% 70%, rgba(255,255,255,0.10) 75%, transparent 80%)" }} />
    <div style={{ position: "absolute", top: "50%", left: "50%", width: size * 0.26, height: size * 0.26, borderRadius: "50%", transform: "translate(-50%,-50%)", background: accent }} />
    <div style={{ position: "absolute", top: "50%", left: "50%", width: 16, height: 16, borderRadius: "50%", transform: "translate(-50%,-50%)", background: C.black }} />
  </div>
);

export { FONT_SANS, FONT_SERIF };
