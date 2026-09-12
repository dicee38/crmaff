import type { CSSProperties } from "react";

export type LeadStatus =
  | "new"
  | "contacted"
  | "qualified"
  | "registered"
  | "kyc_pending"
  | "kyc_approved"
  | "ftd"
  | "active"
  | "churned"
  | "unsubscribed";

export interface StatusBadgeProps {
  status: LeadStatus | string;
  /** Override the rendered text (default is the raw status key). */
  label?: string;
  style?: CSSProperties;
}

const statusMap: Record<string, { bg: string; fg: string }> = {
  new: { bg: "var(--status-neutral-soft)", fg: "var(--graphite-700)" },
  contacted: { bg: "var(--navy-100)", fg: "var(--navy-700)" },
  qualified: { bg: "var(--navy-100)", fg: "var(--navy-700)" },
  registered: { bg: "var(--green-100)", fg: "var(--green-700)" },
  kyc_pending: { bg: "var(--gold-100)", fg: "var(--gold-700)" },
  kyc_approved: { bg: "var(--gold-100)", fg: "var(--gold-700)" },
  ftd: { bg: "var(--green-700)", fg: "var(--text-on-brand)" },
  active: { bg: "var(--green-700)", fg: "var(--text-on-brand)" },
  churned: { bg: "var(--status-critical-soft)", fg: "var(--status-critical)" },
  unsubscribed: { bg: "var(--bone-200)", fg: "var(--graphite-500)" },
};
const statusShell: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  fontFamily: "var(--font-mono)",
  fontSize: "var(--text-micro)",
  fontWeight: "var(--weight-medium)",
  letterSpacing: "var(--tracking-label)",
  textTransform: "uppercase",
  padding: "3px 8px",
  borderRadius: "var(--radius-pill)",
};

/** Lead pipeline state. Colour advances with funnel depth: graphite → green → brass → solid forest. */
export function StatusBadge({ status, label, style, ...rest }: StatusBadgeProps) {
  const tone = statusMap[status] || statusMap.new;
  return (
    <span style={{ ...statusShell, background: tone.bg, color: tone.fg, ...style }} {...rest}>
      {label || status}
    </span>
  );
}
