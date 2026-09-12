import type { CSSProperties } from "react";

export interface LeaderboardRowProps {
  rank: number;
  label: string;
  value: string | number;
  /** Highlights the viewer's own row in forest on soft green. */
  isCurrentUser?: boolean;
  style?: CSSProperties;
}

const lbShell: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "56px 1fr auto",
  alignItems: "center",
  gap: "var(--space-4)",
  background: "var(--surface-card)",
  border: "var(--border-width) solid var(--border-subtle)",
  borderRadius: "var(--radius-sm)",
  padding: "var(--space-4) var(--space-5)",
};
const lbRank: CSSProperties = { fontFamily: "var(--font-display)", fontSize: "var(--text-h2)", fontWeight: "var(--weight-semibold)", textAlign: "center", color: "var(--graphite-500)", fontVariantNumeric: "tabular-nums" };
const lbName: CSSProperties = { fontFamily: "var(--font-body)", fontSize: "var(--text-body-sm)", fontWeight: "var(--weight-medium)", color: "var(--text-primary)" };
const lbMe: CSSProperties = { fontFamily: "var(--font-body)", fontSize: "var(--text-micro)", letterSpacing: "var(--tracking-label)", textTransform: "uppercase", color: "var(--green-600)", marginLeft: "var(--space-3)" };
const lbValue: CSSProperties = { fontFamily: "var(--font-mono)", fontSize: "var(--text-body-sm)", fontWeight: "var(--weight-medium)", fontVariantNumeric: "tabular-nums" };

/** Manager standing row. Top three ranks are numbered in brass — no medal emoji. */
export function LeaderboardRow({ rank, label, value, isCurrentUser = false, style, ...rest }: LeaderboardRowProps) {
  const top = rank <= 3;
  return (
    <div style={{ ...lbShell, ...(isCurrentUser ? { borderColor: "var(--green-700)", background: "var(--green-100)" } : null), ...style }} {...rest}>
      <span style={{ ...lbRank, ...(top ? { color: "var(--gold-600)" } : null) }}>{rank}</span>
      <span style={lbName}>
        {label}
        {isCurrentUser ? <span style={lbMe}>Вы</span> : null}
      </span>
      <span style={lbValue}>{value}</span>
    </div>
  );
}
