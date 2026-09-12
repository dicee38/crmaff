import { useState } from "react";
import type { CSSProperties, ReactNode } from "react";

export interface NavLinkProps {
  active?: boolean;
  href?: string;
  onClick?: () => void;
  children?: ReactNode;
  style?: CSSProperties;
}

const navLinkBase: CSSProperties = {
  fontFamily: "var(--font-body)",
  fontSize: "var(--text-body-sm)",
  fontWeight: "var(--weight-medium)",
  letterSpacing: "0.01em",
  color: "var(--text-secondary)",
  textDecoration: "none",
  padding: "var(--space-3) var(--space-4)",
  borderRadius: "var(--radius-sm)",
  cursor: "pointer",
  background: "transparent",
  border: "none",
  transition: "background var(--duration-fast) var(--ease-out),color var(--duration-fast) var(--ease-out)",
  whiteSpace: "nowrap",
  flex: "0 0 auto",
};

/** Top-bar navigation item. Active state = soft green wash, forest text. */
export function NavLink({ active = false, onClick, href, children, style, ...rest }: NavLinkProps) {
  const [hover, setHover] = useState(false);
  const sharedStyle: CSSProperties = {
    ...navLinkBase,
    ...(hover && !active ? { color: "var(--text-primary)", background: "var(--bone-200)" } : null),
    ...(active ? { background: "var(--navy-100)", color: "var(--navy-700)", fontWeight: "var(--weight-semibold)" } : null),
    ...style,
  };
  if (href) {
    return (
      <a href={href} onClick={onClick} onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)} style={sharedStyle} {...rest}>
        {children}
      </a>
    );
  }
  return (
    <button onClick={onClick} onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)} style={sharedStyle} {...rest}>
      {children}
    </button>
  );
}
