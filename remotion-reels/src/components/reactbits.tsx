/**
 * Portes "frame-driven" de efectos al estilo ReactBits (BlurText, ShinyText).
 *
 * Por qué NO se copian tal cual desde reactbits.dev: casi todos usan GSAP, framer-motion,
 * requestAnimationFrame o IntersectionObserver. Remotion renderiza cada frame por separado
 * (y en paralelo), así que cualquier animación basada en tiempo real "parpadea" o sale vacía.
 * Aquí el estado sale SOLO de useCurrentFrame() => render 100% determinista.
 */
import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

type BlurTextProps = {
  text: string;
  /** frame (local) en el que empieza el primer token */
  delay?: number;
  /** frames entre token y token */
  stagger?: number;
  by?: "words" | "chars";
  style?: React.CSSProperties;
  maxBlur?: number;
};

export const BlurText: React.FC<BlurTextProps> = ({
  text,
  delay = 0,
  stagger = 4,
  by = "words",
  style,
  maxBlur = 16,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tokens = by === "words" ? text.split(" ") : text.split("");

  return (
    <span style={{ display: "inline-block", ...style }}>
      {tokens.map((tok, i) => {
        const p = spring({
          frame: frame - delay - i * stagger,
          fps,
          config: { damping: 20, stiffness: 120, mass: 0.8 },
        });
        return (
          <span
            key={`${tok}-${i}`}
            style={{
              display: "inline-block",
              whiteSpace: "pre",
              opacity: p,
              filter: `blur(${(1 - p) * maxBlur}px)`,
              transform: `translateY(${(1 - p) * 34}px)`,
              marginRight: by === "words" && i < tokens.length - 1 ? "0.28em" : 0,
            }}
          >
            {tok}
          </span>
        );
      })}
    </span>
  );
};

type ShinyTextProps = {
  text: string;
  base?: string;
  shine?: string;
  /** frames que tarda el brillo en cruzar el texto */
  period?: number;
  style?: React.CSSProperties;
};

export const ShinyText: React.FC<ShinyTextProps> = ({
  text,
  base = "#9a9a98",
  shine = "#ffffff",
  period = 60,
  style,
}) => {
  const frame = useCurrentFrame();
  const pos = interpolate((frame % period) / period, [0, 1], [160, -60]);
  return (
    <span
      style={{
        display: "inline-block",
        backgroundImage: `linear-gradient(110deg, ${base} 35%, ${shine} 50%, ${base} 65%)`,
        backgroundSize: "250% 100%",
        backgroundPosition: `${pos}% 0`,
        WebkitBackgroundClip: "text",
        backgroundClip: "text",
        color: "transparent",
        ...style,
      }}
    >
      {text}
    </span>
  );
};
