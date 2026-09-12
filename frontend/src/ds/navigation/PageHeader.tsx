import type { CSSProperties, ReactNode } from "react";

export interface PageHeaderProps {
  eyebrow?: string;
  title: ReactNode;
  action?: ReactNode;
  style?: CSSProperties;
}

const pageHeadShell: CSSProperties = { display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: "var(--space-6)", marginBottom: "var(--space-6)" };
const eyebrowStyle: CSSProperties = {
  display: "block",
  fontFamily: "var(--font-body)",
  fontSize: "var(--text-micro)",
  fontWeight: "var(--weight-semibold)",
  letterSpacing: "var(--tracking-eyebrow)",
  textTransform: "uppercase",
  color: "var(--navy-600)",
  marginBottom: "var(--space-3)",
};
const titleStyle: CSSProperties = {
  margin: 0,
  fontFamily: "var(--font-display)",
  fontSize: "var(--text-h1)",
  fontWeight: "var(--weight-semibold)",
  letterSpacing: "var(--tracking-heading)",
  lineHeight: "var(--lh-heading)",
  color: "var(--text-primary)",
};

/** Page title block: optional uppercase eyebrow, Archivo h1, right-aligned action. */
export function PageHeader({ eyebrow, title, action, style, ...rest }: PageHeaderProps) {
  return (
    <div style={{ ...pageHeadShell, ...style }} {...rest}>
      <div style={{ minWidth: 0 }}>
        {eyebrow ? <span style={eyebrowStyle}>{eyebrow}</span> : null}
        <h1 style={titleStyle}>{title}</h1>
      </div>
      {action}
    </div>
  );
}
