import type { CSSProperties, ReactNode } from "react";

export interface FieldProps {
  label?: string;
  hint?: string;
  required?: boolean;
  htmlFor?: string;
  children?: ReactNode;
  style?: CSSProperties;
}

const fieldShell: CSSProperties = { display: "flex", flexDirection: "column", gap: "var(--space-2)", fontFamily: "var(--font-body)" };
const fieldLabel: CSSProperties = {
  fontSize: "var(--text-micro)",
  fontWeight: "var(--weight-semibold)",
  letterSpacing: "var(--tracking-label)",
  textTransform: "uppercase",
  color: "var(--text-muted)",
};
const fieldHint: CSSProperties = { margin: 0, fontSize: "var(--text-caption)", color: "var(--text-muted)" };

/** Label + control + hint wrapper. Labels are uppercase, tracked, muted graphite. */
export function Field({ label, hint, required = false, htmlFor, children, style, ...rest }: FieldProps) {
  return (
    <label htmlFor={htmlFor} style={{ ...fieldShell, ...style }} {...rest}>
      {label ? (
        <span style={fieldLabel}>
          {label}
          {required ? <span style={{ color: "var(--status-critical)" }}> *</span> : null}
        </span>
      ) : null}
      {children}
      {hint ? <p style={fieldHint}>{hint}</p> : null}
    </label>
  );
}
