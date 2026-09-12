import type { CSSProperties, ReactNode } from "react";

import { Logo } from "../brand/Logo";

export interface AppHeaderProps {
  /** NavLink elements. */
  nav?: ReactNode;
  /** Identity text, e.g. "Карим Х. · affiliate_manager". */
  user?: ReactNode;
  /** Trailing control slot (sign out). */
  action?: ReactNode;
  /** Text next to the mark - override for products other than Verdance itself. */
  logoWordmark?: string;
  style?: CSSProperties;
}

const headerShell: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "var(--space-7)",
  height: "var(--header-height)",
  padding: "0 var(--layout-gutter)",
  background: "var(--surface-card)",
  borderBottom: "var(--border-width) solid var(--border-subtle)",
};
const headerNav: CSSProperties = { display: "flex", alignItems: "center", gap: "var(--space-1)", flex: "1 1 auto", minWidth: 0, overflowX: "auto", overflowY: "hidden", scrollbarWidth: "none" };
const headerUser: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "var(--space-4)",
  fontFamily: "var(--font-body)",
  fontSize: "var(--text-caption)",
  color: "var(--text-muted)",
  whiteSpace: "nowrap",
  minWidth: 0,
  flex: "0 1 auto",
  overflow: "hidden",
  textOverflow: "ellipsis",
};

/** CRM top bar: lockup, nav slot, identity, sign-out action. */
export function AppHeader({ nav, user, action, logoWordmark, style, ...rest }: AppHeaderProps) {
  return (
    <header style={{ ...headerShell, ...style }} {...rest}>
      <Logo size={26} wordmark={logoWordmark} style={{ flex: "0 0 auto" }} />
      <nav style={headerNav}>{nav}</nav>
      {user ? <span style={headerUser}>{user}</span> : null}
      <span style={{ flex: "0 0 auto", display: "flex", alignItems: "center" }}>{action}</span>
    </header>
  );
}
