import { useState } from "react";
import type { CSSProperties, InputHTMLAttributes } from "react";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  invalid?: boolean;
  /** Use the mono face — for IDs, click_id, amounts. */
  mono?: boolean;
  style?: CSSProperties;
}

const inputBase: CSSProperties = {
  fontFamily: "var(--font-body)",
  fontSize: "var(--text-body-sm)",
  color: "var(--text-primary)",
  background: "var(--surface-card)",
  border: "var(--border-width) solid var(--border-default)",
  borderRadius: "var(--radius-sm)",
  height: "var(--control-height-md)",
  padding: "0 var(--space-4)",
  outline: "none",
  width: "100%",
  transition: "border-color var(--duration-fast) var(--ease-out),box-shadow var(--duration-fast) var(--ease-out)",
};

/** Single-line text input. Focus = forest border + soft green ring, never a blue glow. */
export function Input({ invalid = false, mono = false, disabled = false, style, onFocus, onBlur, ...rest }: InputProps) {
  const [focus, setFocus] = useState(false);
  return (
    <input
      disabled={disabled}
      onFocus={(e) => {
        setFocus(true);
        onFocus?.(e);
      }}
      onBlur={(e) => {
        setFocus(false);
        onBlur?.(e);
      }}
      style={{
        ...inputBase,
        ...(mono ? { fontFamily: "var(--font-mono)", letterSpacing: "var(--tracking-mono)" } : null),
        ...(invalid ? { borderColor: "var(--status-critical)" } : null),
        ...(focus ? { borderColor: "var(--green-600)", boxShadow: "0 0 0 3px var(--green-100)" } : null),
        ...(disabled ? { background: "var(--bone-200)", color: "var(--text-muted)" } : null),
        ...style,
      }}
      {...rest}
    />
  );
}
