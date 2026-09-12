import type { CSSProperties, ReactNode } from "react";

export interface CardProps {
  /** Uppercase eyebrow title in the card header. */
  title?: string;
  /** Right-aligned header slot (link, filter, button). */
  action?: ReactNode;
  padding?: "sm" | "md" | "lg";
  tone?: "default" | "sunken" | "brand" | "navy" | "graphite";
  children?: ReactNode;
  style?: CSSProperties;
}

const cardShell: CSSProperties = {
  background: "var(--surface-card)",
  border: "var(--border-width) solid var(--border-subtle)",
  borderRadius: "var(--radius-md)",
};
const cardTitle: CSSProperties = {
  margin: 0,
  fontFamily: "var(--font-body)",
  fontSize: "var(--text-micro)",
  fontWeight: "var(--weight-semibold)",
  letterSpacing: "var(--tracking-eyebrow)",
  textTransform: "uppercase",
  color: "var(--text-muted)",
};
const cardHead: CSSProperties = {
  display: "flex",
  alignItems: "baseline",
  justifyContent: "space-between",
  gap: "var(--space-4)",
  padding: "var(--space-5) var(--space-6)",
  borderBottom: "var(--border-width) solid var(--border-subtle)",
};
const cardPads: Record<string, string> = { sm: "var(--space-5)", md: "var(--space-6)", lg: "var(--space-7)" };

const TONES: Record<string, CSSProperties | null> = {
  default: null,
  navy: { background: "var(--navy-700)", borderColor: "var(--navy-700)", color: "var(--text-on-dark)" },
  sunken: { background: "var(--surface-sunken)", borderColor: "var(--border-subtle)" },
  brand: { background: "var(--green-700)", borderColor: "var(--green-700)", color: "var(--text-on-brand)" },
  graphite: { background: "var(--graphite-900)", borderColor: "var(--graphite-900)", color: "var(--text-on-dark)" },
};

/** Bordered content block. Structure comes from the hairline border, not shadow. */
export function Card({ title, action, padding = "md", tone = "default", children, style, ...rest }: CardProps) {
  const dark = tone === "brand" || tone === "graphite" || tone === "navy";
  return (
    <section style={{ ...cardShell, ...TONES[tone], ...style }} {...rest}>
      {title ? (
        <header
          style={{
            ...cardHead,
            borderBottomColor: dark ? "rgba(245,243,238,0.16)" : "var(--border-subtle)",
          }}
        >
          <h2
            style={{
              ...cardTitle,
              color: dark ? (tone === "navy" ? "var(--navy-200)" : "var(--green-200)") : "var(--text-muted)",
            }}
          >
            {title}
          </h2>
          {action}
        </header>
      ) : null}
      <div style={{ padding: cardPads[padding] }}>{children}</div>
    </section>
  );
}
