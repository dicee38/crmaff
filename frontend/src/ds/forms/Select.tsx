import { useState } from "react";
import type { CSSProperties, SelectHTMLAttributes } from "react";

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  options?: SelectOption[];
  /** Empty-value first option, e.g. "Все". */
  placeholder?: string;
  style?: CSSProperties;
}

const selectBase: CSSProperties = {
  fontFamily: "var(--font-body)",
  fontSize: "var(--text-body-sm)",
  color: "var(--text-primary)",
  background: "var(--surface-card)",
  border: "var(--border-width) solid var(--border-default)",
  borderRadius: "var(--radius-sm)",
  height: "var(--control-height-md)",
  padding: "0 var(--space-7) 0 var(--space-4)",
  outline: "none",
  width: "100%",
  appearance: "none",
  cursor: "pointer",
  backgroundImage:
    "linear-gradient(45deg,transparent 50%,var(--graphite-600) 50%),linear-gradient(135deg,var(--graphite-600) 50%,transparent 50%)",
  backgroundPosition: "calc(100% - 15px) 16px,calc(100% - 11px) 16px",
  backgroundSize: "4px 4px,4px 4px",
  backgroundRepeat: "no-repeat",
};

/** Native select with the brand's chevron and forest focus ring. */
export function Select({ options = [], placeholder, disabled = false, style, onFocus, onBlur, children, ...rest }: SelectProps) {
  const [focus, setFocus] = useState(false);
  return (
    <select
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
        ...selectBase,
        ...(focus ? { borderColor: "var(--green-600)", boxShadow: "0 0 0 3px var(--green-100)" } : null),
        ...(disabled ? { background: "var(--bone-200)", cursor: "not-allowed" } : null),
        ...style,
      }}
      {...rest}
    >
      {placeholder ? <option value="">{placeholder}</option> : null}
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
      {children}
    </select>
  );
}
