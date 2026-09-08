import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

export function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <header className="app-header">
        <Link to="/leads" className="app-logo">
          Binolla CRM
        </Link>
        {user && (
          <div className="app-user">
            <span>
              {user.full_name} · {user.role}
            </span>
            <button onClick={logout}>Выйти</button>
          </div>
        )}
      </header>
      <main>{children}</main>
    </div>
  );
}
