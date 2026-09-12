import type { CSSProperties } from "react";

export interface FunnelRowProps {
  label: string;
  value: string | number;
  /** Bar width as a percentage of the largest stage. */
  percent?: number;
  tone?: "brand" | "soft" | "data" | "accent";
  style?: CSSProperties;
}

const funnelRowShell: CSSProperties = { display: "grid", gridTemplateColumns: "160px 1fr 64px", alignItems: "center", gap: "var(--space-4)" };
const funnelLabel: CSSProperties = { fontFamily: "var(--font-body)", fontSize: "var(--text-caption)", color: "var(--text-secondary)" };
const funnelTrack: CSSProperties = { background: "var(--bone-200)", borderRadius: "var(--radius-xs)", height: "18px", overflow: "hidden" };
const funnelValue: CSSProperties = { fontFamily: "var(--font-mono)", fontSize: "var(--text-caption)", fontWeight: "var(--weight-medium)", textAlign: "right", fontVariantNumeric: "tabular-nums" };
const FILLS: Record<string, string> = { brand: "var(--green-700)", soft: "var(--green-500)", data: "var(--navy-700)", accent: "var(--gold-500)" };

/** One stage of the acquisition funnel: label, proportional bar, count. */
export function FunnelRow({ label, value, percent = 0, tone = "brand", style, ...rest }: FunnelRowProps) {
  return (
    <div style={{ ...funnelRowShell, ...style }} {...rest}>
      <span style={funnelLabel}>{label}</span>
      <div style={funnelTrack}>
        <div
          style={{
            width: Math.max(percent, 2) + "%",
            height: "100%",
            background: FILLS[tone],
            borderRadius: "var(--radius-xs)",
            transition: "width var(--duration-slow) var(--ease-out)",
          }}
        />
      </div>
      <span style={funnelValue}>{value}</span>
    </div>
  );
}
