import React from "react";
import { AbsoluteFill, Img, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { BlurText, ShinyText } from "../components/reactbits";
import { Backdrop, Grain, Masthead } from "../components/ui";
import type { Top10Props } from "../schema";
import { C, FONT_SANS, FONT_SERIF, SAFE_TOP } from "../theme";

export const TOP10_INTRO = 45; // frames antes del primer reveal
export const TOP10_OUTRO = 75; // frames de CTA después del #1

const LIST_TOP = 700;
const ROW_H = 80;

/**
 * Cuenta regresiva: se revela primero el último lugar y al final el #1.
 * El panel de arriba a la derecha muestra el número que se está revelando
 * y, al llegar al #1, se convierte en la carátula.
 */
export const Top10Reel: React.FC<Top10Props> = ({ countryName, accentPrimary, accentSecondary, featuredCoverUrl, items, secondsPerItem, cta, year }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const sorted = [...items].sort((a, b) => a.rank - b.rank);
  const n = sorted.length;
  const per = Math.round(secondsPerItem * fps);
  const startOf = (idx: number) => TOP10_INTRO + (n - 1 - idx) * per;

  const activeIdx = Math.max(0, Math.min(n - 1, n - 1 - Math.floor((frame - TOP10_INTRO) / per)));
  const started = frame >= TOP10_INTRO;
  const finalStart = startOf(0);
  const isFinal = frame >= finalStart;

  const coverP = spring({ frame: frame - finalStart, fps, config: { damping: 15, stiffness: 80 } });
  const numPop = spring({ frame: (frame - TOP10_INTRO) % per, fps, config: { damping: 10, stiffness: 160 } });
  const ctaIn = spring({ frame: frame - (finalStart + per + 6), fps, config: { damping: 16 } });
  const fadeOut = interpolate(frame, [durationInFrames - 10, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  return (
    <AbsoluteFill style={{ background: C.black, opacity: fadeOut }}>
      <Backdrop urlA={featuredCoverUrl} accentA={accentPrimary} accentB={accentSecondary} />
      <Masthead />

      {/* Encabezado */}
      <div style={{ position: "absolute", left: 64, top: SAFE_TOP + 20, width: 560 }}>
        <div style={{ fontFamily: FONT_SERIF, fontStyle: "italic", fontSize: 30, letterSpacing: 3, color: C.gray }}>
          <BlurText text="Lo más escuchado" by="chars" stagger={1.2} maxBlur={6} />
        </div>
        <div style={{ fontFamily: FONT_SANS, fontSize: 150, lineHeight: 1, color: C.white, marginTop: 6 }}>
          <BlurText text="TOP 10" delay={6} stagger={8} />
        </div>
        <div style={{ fontFamily: FONT_SANS, fontSize: 64, textTransform: "uppercase", marginTop: 8, color: accentPrimary }}>
          <BlurText text={countryName} delay={16} stagger={6} />
        </div>
      </div>

      {/* Panel: número en cuenta regresiva -> carátula del #1 */}
      <div style={{ position: "absolute", left: 660, top: SAFE_TOP + 10, width: 350, height: 350, transform: "rotate(3deg)", background: C.white, padding: 12, boxShadow: "0 30px 60px rgba(0,0,0,0.55)" }}>
        <div style={{ position: "relative", width: "100%", height: "100%", background: C.black, overflow: "hidden" }}>
          {!isFinal && (
            <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: FONT_SANS, fontSize: 200, color: C.white, transform: `scale(${started ? 0.7 + 0.3 * numPop : 1})` }}>
              {started ? sorted[activeIdx].rank : "?"}
            </div>
          )}
          {isFinal && featuredCoverUrl && (
            <Img src={featuredCoverUrl} style={{ width: "100%", height: "100%", objectFit: "contain", filter: `blur(${(1 - coverP) * 30}px)`, transform: `scale(${1.15 - 0.15 * coverP})` }} />
          )}
        </div>
      </div>

      {/* Lista */}
      {sorted.map((it, idx) => {
        const s = startOf(idx);
        const p = spring({ frame: frame - s, fps, config: { damping: 15, stiffness: 110 } });
        const isActive = frame >= s && frame < s + per;
        const shown = frame >= s;
        const dim = idx === 0 && isFinal ? 1 : isActive ? 1 : 0.55;
        return (
          <div
            key={it.rank}
            style={{
              position: "absolute",
              left: 64,
              right: 64,
              top: LIST_TOP + idx * ROW_H,
              height: ROW_H - 8,
              display: "flex",
              alignItems: "center",
              gap: 26,
              opacity: shown ? p * dim : 0,
              transform: `translateX(${(1 - p) * 140}px)`,
              borderLeft: `6px solid ${isActive || (idx === 0 && isFinal) ? accentPrimary : "transparent"}`,
              paddingLeft: 18,
              background: isActive ? "rgba(245,245,243,0.06)" : "transparent",
              color: C.white,
            }}
          >
            <div style={{ width: 84, fontFamily: FONT_SANS, fontSize: 46, color: idx === 0 ? accentPrimary : C.white }}>{String(it.rank).padStart(2, "0")}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontFamily: FONT_SANS, fontSize: 30, textTransform: "uppercase", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{it.title}</div>
              <div style={{ fontFamily: FONT_SERIF, fontStyle: "italic", fontSize: 24, color: C.gray, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{it.artist}</div>
            </div>
          </div>
        );
      })}

      {/* CTA final (sobre la lista, dentro de la zona segura) */}
      <div style={{ position: "absolute", left: 0, right: 0, top: 1462, textAlign: "center", zIndex: 30, opacity: ctaIn, transform: `translateY(${(1 - ctaIn) * 30}px)` }}>
        <div style={{ display: "inline-block", border: `2px solid ${C.white}`, padding: "16px 38px", background: "rgba(5,5,5,0.8)", fontFamily: FONT_SANS, fontSize: 30, letterSpacing: 4 }}>
          <ShinyText text={cta} base="#cfcfcb" />
        </div>
      </div>
      <div style={{ position: "absolute", left: 64, top: 1490, zIndex: 31, fontFamily: FONT_SERIF, fontStyle: "italic", fontSize: 26, color: C.gray, opacity: ctaIn }}>{year}</div>

      <Grain />
    </AbsoluteFill>
  );
};
