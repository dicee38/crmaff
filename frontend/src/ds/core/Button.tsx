import { useState } from "react";
import type { CSSProperties, ReactNode } from "react";

export interface ButtonProps {
  variant?: "primary" | "secondary" | "ghost" | "brass" | "danger";
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
  fullWidth?: boolean;
  as?: "button" | "a";
  href?: string;
  type?: "button" | "submit" | "reset";
  onClick?: () => void;
  children?: ReactNode;
  style?: CSSProperties;
  title?: string;
}

const buttonBase: CSSProperties = {
  fontFamily: "var(--font-body)",
  fontWeight: "var(--weight-semibold)",
  letterSpacing: "0.02em",
  border: "var(--border-width) solid transparent",
  borderRadius: "var(--radius-sm)",
  cursor: "pointer",
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  gap: "var(--space-3)",
  textDecoration: "none",
  transition:
    "background var(--duration-fast) var(--ease-out),color var(--duration-fast) var(--ease-out),border-color var(--duration-fast) var(--ease-out)",
  whiteSpace: "nowrap",
};
const buttonSizes: Record<string, CSSProperties> = {
  sm: { height: "var(--control-height-sm)", padding: "0 var(--space-4)", fontSize: "var(--text-caption)" },
  md: { height: "var(--control-height-md)", padding: "0 var(--space-6)", fontSize: "var(--text-body-sm)" },
  lg: { height: "var(--control-height-lg)", padding: "0 var(--space-7)", fontSize: "var(--text-body)" },
};
const buttonVariants: Record<string, CSSProperties> = {
  primary: { background: "var(--green-700)", color: "var(--text-on-brand)" },
  secondary: { background: "transparent", color: "var(--text-primary)", borderColor: "var(--graphite-900)" },
  ghost: { background: "transparent", color: "var(--text-brand)" },
  brass: { background: "var(--gold-500)", color: "var(--graphite-900)" },
  danger: { background: "transparent", color: "var(--status-critical)", borderColor: "var(--status-critical)" },
};
const buttonHover: Record<string, CSSProperties> = {
  primary: { background: "var(--green-800)" },
  secondary: { background: "var(--graphite-900)", color: "var(--text-on-dark)" },
  ghost: { background: "var(--green-100)" },
  brass: { background: "var(--gold-600)" },
  danger: { background: "var(--status-critical-soft)" },
};

/** Primary action control. Brass variant is the ambition accent — one per view at most. */
export function Button({
  variant = "primary",
  size = "md",
  disabled = false,
  fullWidth = false,
  as = "button",
  href,
  children,
  style,
  ...rest
}: ButtonProps) {
  const [hover, setHover] = useState(false);
  const s: CSSProperties = {
    ...buttonBase,
    ...buttonSizes[size],
    ...buttonVariants[variant],
    ...(hover && !disabled ? buttonHover[variant] : null),
    ...(fullWidth ? { width: "100%" } : null),
    ...(disabled ? { opacity: 0.45, cursor: "not-allowed" } : null),
    ...style,
  };
  if (as === "a") {
    return (
      <a href={href} style={s} onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)} {...rest}>
        {children}
      </a>
    );
  }
  return (
    <button
      disabled={disabled}
      style={s}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      {...rest}
    >
      {children}
    </button>
  );
}
