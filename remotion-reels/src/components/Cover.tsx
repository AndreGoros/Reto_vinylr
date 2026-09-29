import React from "react";
import { Img, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT_SANS } from "../theme";
import { Vinyl } from "./ui";

type CoverProps = {
  src: string;
  tag: string;
  accent: string;
  size: number;
  /** rotación final en grados */
  rotate: number;
  /** frame en el que entra */
  enterAt: number;
  /** -1 entra desde la izquierda, 1 desde la derecha */
  from: 1 | -1;
  /** lado por el que asoma el vinilo */
  vinylSide: "left" | "right";
  style?: React.CSSProperties;
};

/** Carátula estilo polaroid (siempre completa, object-fit: contain) + vinilo asomando. */
export const Cover: React.FC<CoverProps> = ({ src, tag, accent, size, rotate, enterAt, from, vinylSide, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - enterAt, fps, config: { damping: 14, stiffness: 90, mass: 0.9 } });
  const x = interpolate(p, [0, 1], [from * 1000, 0]);
  const rot = rotate + interpolate(p, [0, 1], [from * 14, 0]);
  const float = frame > enterAt + 30 ? Math.sin((frame - enterAt) / 24) * 5 : 0;
  const vinylSize = size * 0.94;
  const vinylOffset = size * 0.48;
  const spin = Math.max(0, frame - enterAt) * 3.2;

  return (
    <div
      style={{
        position: "absolute",
        width: size,
        height: size,
        transform: `translateX(${x}px) translateY(${float}px) rotate(${rot}deg)`,
        opacity: interpolate(p, [0, 0.15], [0, 1], { extrapolateRight: "clamp" }),
        ...style,
      }}
    >
      {/* vinilo detrás */}
      <div style={{ position: "absolute", top: (size - vinylSize) / 2, [vinylSide]: -vinylOffset, zIndex: 0 }}>
        <Vinyl size={vinylSize} accent={accent} spin={spin} />
      </div>
      {/* marco blanco */}
      <div style={{ position: "absolute", inset: 0, zIndex: 1, background: C.white, padding: 14, boxShadow: "0 30px 60px rgba(0,0,0,0.55), 0 10px 20px rgba(0,0,0,0.4)" }}>
        <Img src={src} style={{ width: "100%", height: "100%", objectFit: "contain", background: C.black, display: "block" }} />
        <span style={{ position: "absolute", top: -18, left: 22, background: accent, color: C.black, fontFamily: FONT_SANS, fontSize: 15, letterSpacing: 3.5, padding: "6px 12px" }}>{tag}</span>
      </div>
    </div>
  );
};
