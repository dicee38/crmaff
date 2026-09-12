import type { CSSProperties, ReactNode } from "react";

export interface FilterBarProps {
  children?: ReactNode;
  /** Right-aligned slot (export, add, refresh). */
  action?: ReactNode;
  style?: CSSProperties;
}

const filterBarShell: CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  alignItems: "flex-end",
  gap: "var(--space-5)",
  marginBottom: "var(--space-6)",
};

/** Row of filter fields above a table or report. */
export function FilterBar({ children, action, style, ...rest }: FilterBarProps) {
  return (
    <div style={{ ...filterBarShell, ...style }} {...rest}>
      {children}
      {action ? <div style={{ marginLeft: "auto" }}>{action}</div> : null}
    </div>
  );
}
