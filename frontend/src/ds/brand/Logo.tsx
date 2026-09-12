import type { CSSProperties } from "react";

export interface LogoProps {
  /** Mark edge length in px; the wordmark scales from it. */
  size?: number;
  tone?: "forest" | "graphite" | "reverse" | "mono";
  showWordmark?: boolean;
  /** Text next to the mark. Defaults to "Verdance". */
  wordmark?: string;
  style?: CSSProperties;
}

const lockup: CSSProperties = { display: "inline-flex", alignItems: "center", gap: "var(--space-4)", textDecoration: "none" };
const wordmarkStyle: CSSProperties = {
  fontFamily: "var(--font-display)",
  fontWeight: "var(--weight-semibold)",
  textTransform: "uppercase",
  lineHeight: 1,
  letterSpacing: "0.1em",
};
const markPath = "M17 15 L32 45 L47 11";

const MARK_FILLS: Record<string, { box: string; stroke: string; outline: string }> = {
  forest: { box: "#1B4332", stroke: "#F5F3EE", outline: "none" },
  graphite: { box: "#1A1A1A", stroke: "#F5F3EE", outline: "none" },
  reverse: { box: "none", stroke: "#F5F3EE", outline: "#F5F3EE" },
  mono: { box: "none", stroke: "#1A1A1A", outline: "#1A1A1A" },
};

function Mark({ size, tone }: { size: number; tone: string }) {
  const t = MARK_FILLS[tone] || MARK_FILLS.forest;
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true" style={{ display: "block", flex: "0 0 auto" }}>
      {t.box !== "none" ? (
        <rect width="64" height="64" rx="4" fill={t.box} />
      ) : (
        <rect x="0.75" y="0.75" width="62.5" height="62.5" rx="4" fill="none" stroke={t.outline} strokeWidth="1.5" />
      )}
      <path d={markPath} fill="none" stroke={t.stroke} strokeWidth="8" strokeLinecap="square" strokeLinejoin="miter" />
    </svg>
  );
}

/** Monogram rising inside a monolithic square, plus the tracked wordmark. */
export function Logo({ size = 32, tone = "forest", showWordmark = true, wordmark: wordmarkText = "Verdance", style, ...rest }: LogoProps) {
  const light = tone === "reverse";
  return (
    <span style={{ ...lockup, ...style }} {...rest}>
      <Mark size={size} tone={tone} />
      {showWordmark ? (
        <span style={{ ...wordmarkStyle, fontSize: Math.round(size * 0.56), color: light ? "var(--bone-100)" : "var(--text-primary)" }}>
          {wordmarkText}
        </span>
      ) : null}
    </span>
  );
}
