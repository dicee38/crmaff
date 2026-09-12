import type { CSSProperties, ReactNode } from "react";

export interface BadgeProps {
  tone?: "neutral" | "positive" | "attention" | "critical" | "brand" | "outline";
  /** Use a 3px radius instead of a pill. */
  square?: boolean;
  children?: ReactNode;
  style?: CSSProperties;
}

const badgeBase: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: "var(--space-2)",
  fontFamily: "var(--font-body)",
  fontSize: "var(--text-micro)",
  fontWeight: "var(--weight-semibold)",
  letterSpacing: "var(--tracking-label)",
  textTransform: "uppercase",
  padding: "3px 8px",
  borderRadius: "var(--radius-pill)",
  border: "var(--border-width) solid transparent",
  whiteSpace: "nowrap",
};
const badgeTones: Record<string, CSSProperties> = {
  neutral: { background: "var(--status-neutral-soft)", color: "var(--graphite-700)" },
  positive: { background: "var(--status-positive-soft)", color: "var(--green-700)" },
  attention: { background: "var(--status-attention-soft)", color: "var(--gold-700)" },
  critical: { background: "var(--status-critical-soft)", color: "var(--status-critical)" },
  brand: { background: "var(--green-700)", color: "var(--text-on-brand)" },
  outline: { background: "transparent", color: "var(--graphite-700)", borderColor: "var(--border-default)" },
};

/** Small uppercase pill for counts, flags and validation warnings. */
export function Badge({ tone = "neutral", square = false, children, style, ...rest }: BadgeProps) {
  return (
    <span
      style={{ ...badgeBase, ...badgeTones[tone], ...(square ? { borderRadius: "var(--radius-xs)" } : null), ...style }}
      {...rest}
    >
      {children}
    </span>
  );
}
