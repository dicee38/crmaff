import type { CSSProperties, ReactNode } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import { AppHeader, Button, NavLink } from "../ds";
import type { UserRole } from "../types";

interface NavItem {
  to: string;
  label: string;
  roles?: UserRole[]; // не указано - видно всем аутентифицированным
}

const NAV_ITEMS: NavItem[] = [
  { to: "/leads", label: "Лиды" },
  { to: "/tasks", label: "Задачи" },
  {
    to: "/actions",
    label: "Действия",
    roles: ["admin", "affiliate_manager", "mop_lead", "sales_manager", "analyst"],
  },
  {
    to: "/dashboard",
    label: "Dashboard",
    roles: ["admin", "affiliate_manager", "mop_lead", "compliance", "analyst"],
  },
  {
    to: "/reports/mop-cashflow",
    label: "Cashflow",
    roles: ["admin", "affiliate_manager", "mop_lead", "sales_manager", "analyst"],
  },
  { to: "/leaderboard", label: "Лидерборд" },
  { to: "/admin", label: "Админ-панель", roles: ["admin"] },
];

const shell: CSSProperties = { minHeight: "100vh", background: "var(--bone-100)" };
const page: CSSProperties = { maxWidth: "var(--layout-max)", margin: "0 auto", padding: "var(--space-8) var(--layout-gutter)" };

const ROLE_LABELS: Record<string, string> = {
  admin: "администратор",
  tech_lead: "тех. руководитель",
  compliance: "compliance",
  affiliate_manager: "affiliate-менеджер",
  mop_lead: "рук. группы МОП",
  sales_manager: "МОП",
  smm_manager: "SMM-менеджер",
  analyst: "аналитик",
};

export function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const visibleItems = NAV_ITEMS.filter((item) => !item.roles || (user && item.roles.includes(user.role)));
  const isActive = (to: string) => location.pathname.startsWith(to);

  return (
    <div style={shell}>
      <AppHeader
        nav={
          user
            ? visibleItems.map((item) => (
                <NavLink key={item.to} active={isActive(item.to)} onClick={() => navigate(item.to)}>
                  {item.label}
                </NavLink>
              ))
            : null
        }
        user={
          user ? (
            <button
              onClick={() => navigate("/profile")}
              style={{ background: "none", border: "none", padding: 0, font: "inherit", color: "inherit", cursor: "pointer" }}
            >
              {user.full_name} · {ROLE_LABELS[user.role] ?? user.role}
            </button>
          ) : null
        }
        action={
          user ? (
            <Button size="sm" variant="secondary" onClick={logout}>
              Выйти
            </Button>
          ) : null
        }
      />
      <main style={page}>{children}</main>
    </div>
  );
}
