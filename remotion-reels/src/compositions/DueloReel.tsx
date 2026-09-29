import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Cover } from "../components/Cover";
import { BlurText, ShinyText } from "../components/reactbits";
import { Backdrop, Grain, Masthead } from "../components/ui";
import type { DueloProps } from "../schema";
import { C, COUNTRY_ACCENTS, FONT_SANS, FONT_SERIF, SAFE_TOP } from "../theme";

/**
 * Línea de tiempo (30 fps, 330 frames = 11 s):
 *   0   kicker + "¿Cuál fue mejor?"
 *   45  entra Álbum A (izquierda) + su nombre
 *   105 entra Álbum B (derecha) + su nombre
 *   165 aparece el VS
 *   250 el titular cambia a "Tu turno" + CTA
 */
const T = { a: 45, b: 105, vs: 165, turn: 250 };

const Info: React.FC<{ name: string; artist: string; at: number; align: "left" | "right"; style: React.CSSProperties }> = ({ name, artist, at, align, style }) => (
  <div style={{ position: "absolute", width: 400, textAlign: align, color: C.white, ...style }}>
    <div style={{ fontFamily: FONT_SANS, fontSize: 42, lineHeight: 1.1, textTransform: "uppercase", marginBottom: 10 }}>
      <BlurText text={name} delay={at + 10} stagger={5} />
    </div>
    <div style={{ fontFamily: FONT_SERIF, fontStyle: "italic", fontSize: 30, color: C.gray }}>
      <BlurText text={artist} delay={at + 22} stagger={5} maxBlur={8} />
    </div>
  </div>
);

export const DueloReel: React.FC<DueloProps> = ({ albumA, albumB, kicker, headline, turnHeadline, cta, year }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const accentA = (albumA.country && COUNTRY_ACCENTS[albumA.country]) || C.blue;
  const accentB = (albumB.country && COUNTRY_ACCENTS[albumB.country]) || C.magenta;

  const fadeIn = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  const fadeOut = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  // VS: pop con spring + anillo que se expande
  const vs = spring({ frame: frame - T.vs, fps, config: { damping: 9, stiffness: 140 } });
  const ring = interpolate(frame - T.vs, [0, 22], [0.6, 2.4], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const ringOpacity = interpolate(frame - T.vs, [0, 22], [0.8, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Titular: "¿Cuál fue mejor?" se va y entra "Tu turno"
  const headOut = interpolate(frame, [T.turn - 8, T.turn + 4], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const ctaIn = spring({ frame: frame - (T.turn + 14), fps, config: { damping: 16 } });

  return (
    <AbsoluteFill style={{ background: C.black, opacity: Math.min(fadeIn, fadeOut) }}>
      <Backdrop urlA={albumA.cover_url} urlB={albumB.cover_url} accentA={accentA} accentB={accentB} />
      <Masthead />

      {/* Titulares */}
      <div style={{ position: "absolute", top: SAFE_TOP + 20, left: 0, right: 0, textAlign: "center", opacity: headOut }}>
        <div style={{ fontFamily: FONT_SERIF, fontStyle: "italic", fontSize: 30, letterSpacing: 3, color: C.gray, marginBottom: 14 }}>
          <BlurText text={kicker} by="chars" stagger={1.2} maxBlur={6} />
        </div>
        <div style={{ fontFamily: FONT_SANS, fontSize: 84, lineHeight: 1.05, textTransform: "uppercase", color: C.white, padding: "0 60px" }}>
          <BlurText text={headline} delay={8} stagger={6} />
        </div>
        <div style={{ width: 90, height: 5, background: accentB, margin: "26px auto 0", transform: `scaleX(${spring({ frame: frame - 30, fps })})` }} />
      </div>
      <div style={{ position: "absolute", top: SAFE_TOP + 50, left: 0, right: 0, textAlign: "center" }}>
        <div style={{ fontFamily: FONT_SANS, fontSize: 110, textTransform: "uppercase" }}>
          {frame >= T.turn && <BlurText text={turnHeadline} delay={T.turn + 4} stagger={7} style={{ color: C.white }} />}
        </div>
      </div>

      {/* Álbum A (izquierda) — vinilo asoma por la derecha */}
      <Cover src={albumA.cover_url} tag="ÁLBUM A" accent={accentA} size={500} rotate={-4} enterAt={T.a} from={-1} vinylSide="right" style={{ left: 64, top: 600, zIndex: 10 }} />
      <Info name={albumA.name} artist={albumA.artists.join(", ")} at={T.a} align="left" style={{ left: 620, top: 660, zIndex: 20 }} />

      {/* Álbum B (derecha, encima) — vinilo asoma por la izquierda */}
      <Cover src={albumB.cover_url} tag="ÁLBUM B" accent={accentB} size={500} rotate={3} enterAt={T.b} from={1} vinylSide="left" style={{ left: 516, top: 950, zIndex: 12 }} />
      <Info name={albumB.name} artist={albumB.artists.join(", ")} at={T.b} align="right" style={{ left: 64, top: 1270, zIndex: 20 }} />

      {/* VS */}
      <div style={{ position: "absolute", left: 540 - 60, top: 1040 - 60, width: 120, height: 120, zIndex: 30 }}>
        <div style={{ position: "absolute", inset: 0, borderRadius: "50%", border: `3px solid ${C.blue}`, transform: `scale(${ring})`, opacity: ringOpacity }} />
        <div style={{ position: "absolute", inset: 0, borderRadius: "50%", border: `3px solid ${C.white}`, background: "rgba(5,5,5,0.78)", display: "flex", alignItems: "center", justifyContent: "center", transform: `scale(${vs})`, opacity: vs > 0.01 ? 1 : 0 }}>
          <span style={{ fontFamily: FONT_SERIF, fontStyle: "italic", fontWeight: 500, fontSize: 48, letterSpacing: -2, color: C.white }}>V</span>
          <span style={{ fontFamily: FONT_SERIF, fontStyle: "italic", fontWeight: 500, fontSize: 48, letterSpacing: -2, color: C.blue }}>S</span>
        </div>
      </div>

      {/* CTA final */}
      <div style={{ position: "absolute", left: 0, right: 0, top: 1462, textAlign: "center", zIndex: 30, opacity: ctaIn, transform: `translateY(${(1 - ctaIn) * 30}px)` }}>
        <div style={{ display: "inline-block", border: `2px solid ${C.white}`, padding: "16px 38px", background: "rgba(5,5,5,0.7)", fontFamily: FONT_SANS, fontSize: 30, letterSpacing: 4 }}>
          <ShinyText text={cta} base="#cfcfcb" />
        </div>
      </div>

      {/* Año, discreto, misma altura que el CTA (todo por encima de SAFE_BOTTOM) */}
      <div style={{ position: "absolute", left: 64, top: 1490, zIndex: 30, fontFamily: FONT_SERIF, fontStyle: "italic", fontSize: 26, color: C.gray }}>{year}</div>

      <Grain />
    </AbsoluteFill>
  );
};
