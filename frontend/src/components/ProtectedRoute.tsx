import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import type { UserRole } from "../types";

export function ProtectedRoute({
  children,
  roles,
}: {
  children: ReactNode;
  /** Если указано - доступ только этим ролям, иначе Navigate на /leads. */
  roles?: UserRole[];
}) {
  const { user, isLoading } = useAuth();

  if (isLoading) return <div className="page">Загрузка...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/leads" replace />;

  return <>{children}</>;
}
