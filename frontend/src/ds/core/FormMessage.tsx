import type { CSSProperties, ReactNode } from "react";

export interface FormMessageProps {
  tone?: "error" | "success" | "hint";
  children?: ReactNode;
  style?: CSSProperties;
}

const messageBase: CSSProperties = {
  margin: 0,
  fontFamily: "var(--font-body)",
  fontSize: "var(--text-caption)",
  lineHeight: "var(--lh-tight)",
  display: "flex",
  gap: "var(--space-3)",
  alignItems: "baseline",
};
const messageTones: Record<string, CSSProperties> = {
  error: { color: "var(--status-critical)" },
  success: { color: "var(--green-600)" },
  hint: { color: "var(--text-muted)" },
};
const messageRule: CSSProperties = { width: "2px", alignSelf: "stretch", borderRadius: "1px", flex: "0 0 auto" };

/** Inline form feedback: error, success or hint. */
export function FormMessage({ tone = "hint", children, style, ...rest }: FormMessageProps) {
  return (
    <p style={{ ...messageBase, ...messageTones[tone], ...style }} {...rest}>
      <span style={{ ...messageRule, background: "currentColor", opacity: tone === "hint" ? 0.3 : 1 }} />
      {children}
    </p>
  );
}
