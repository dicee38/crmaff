import type { CSSProperties } from "react";

export interface KpiTileProps {
  label: string;
  value: string | number;
  /** Suffix rendered smaller and muted, e.g. "%" or "$". */
  unit?: string;
  /** Period-over-period note, e.g. "+12% к прошлой неделе". */
  delta?: string;
  deltaTone?: "positive" | "critical" | "neutral";
  /** `data` renders the tile on the deep-blue ground — for the analytics row. */
  tone?: "default" | "data";
  /** Brass border — the one tile that matters most in the view. */
  accent?: boolean;
  style?: CSSProperties;
}

const kpiShell: CSSProperties = {
  background: "var(--surface-card)",
  border: "var(--border-width) solid var(--border-subtle)",
  borderRadius: "var(--radius-md)",
  padding: "var(--space-5) var(--space-6)",
  display: "flex",
  flexDirection: "column",
  gap: "var(--space-2)",
  minWidth: 0,
};
const kpiValue: CSSProperties = {
  fontFamily: "var(--font-display)",
  fontSize: "var(--text-display-md)",
  fontWeight: "var(--weight-semibold)",
  lineHeight: "var(--lh-display)",
  letterSpacing: "var(--tracking-display)",
  fontVariantNumeric: "tabular-nums",
  color: "var(--text-primary)",
};
const kpiLabel: CSSProperties = {
  fontFamily: "var(--font-body)",
  fontSize: "var(--text-micro)",
  fontWeight: "var(--weight-semibold)",
  letterSpacing: "var(--tracking-eyebrow)",
  textTransform: "uppercase",
  color: "var(--text-muted)",
};
const kpiDelta: CSSProperties = { fontFamily: "var(--font-mono)", fontSize: "var(--text-caption)", letterSpacing: "var(--tracking-mono)" };
const DELTA_TONES: Record<string, string> = { positive: "var(--green-600)", critical: "var(--status-critical)", neutral: "var(--text-muted)" };

/** Single metric tile for dashboard grids. */
export function KpiTile({ label, value, unit, delta, deltaTone = "positive", accent = false, tone = "default", style, ...rest }: KpiTileProps) {
  return (
    <div
      style={{
        ...kpiShell,
        ...(tone === "data" ? { background: "var(--navy-700)", borderColor: "var(--navy-700)" } : null),
        ...(accent ? { borderColor: "var(--gold-500)" } : null),
        ...style,
      }}
      {...rest}
    >
      <span style={{ ...kpiLabel, ...(tone === "data" ? { color: "var(--navy-200)" } : null) }}>{label}</span>
      <span style={{ ...kpiValue, ...(tone === "data" ? { color: "var(--bone-100)" } : null) }}>
        {value}
        {unit ? (
          <span style={{ fontSize: "var(--text-h3)", fontWeight: "var(--weight-medium)", color: "var(--text-muted)", marginLeft: "2px" }}>
            {unit}
          </span>
        ) : null}
      </span>
      {delta ? <span style={{ ...kpiDelta, color: DELTA_TONES[deltaTone] }}>{delta}</span> : null}
    </div>
  );
}
