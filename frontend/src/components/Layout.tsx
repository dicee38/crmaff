import type { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
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

export function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const location = useLocation();

  const visibleItems = NAV_ITEMS.filter((item) => !item.roles || (user && item.roles.includes(user.role)));

  return (
    <div className="app-shell">
      <header className="app-header">
        <Link to="/leads" className="app-logo">
          Binolla CRM
        </Link>
        {user && (
          <nav className="app-nav">
            {visibleItems.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className={location.pathname.startsWith(item.to) ? "app-nav-link active" : "app-nav-link"}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        )}
        {user && (
          <div className="app-user">
            <Link to="/profile" className="app-user-link">
              {user.full_name} · {user.role}
            </Link>
            <button onClick={logout}>Выйти</button>
          </div>
        )}
      </header>
      <main>{children}</main>
    </div>
  );
}
