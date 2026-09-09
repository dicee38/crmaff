import type { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { ActionsPage } from "./pages/ActionsPage";
import { CashflowReportPage } from "./pages/CashflowReportPage";
import { DashboardPage } from "./pages/DashboardPage";
import { LeadCardPage } from "./pages/LeadCardPage";
import { LeadsListPage } from "./pages/LeadsListPage";
import { LeaderboardPage } from "./pages/LeaderboardPage";
import { LoginPage } from "./pages/LoginPage";
import { TasksPage } from "./pages/TasksPage";

function withLayout(children: ReactNode) {
  return (
    <ProtectedRoute>
      <Layout>{children}</Layout>
    </ProtectedRoute>
  );
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/leads" element={withLayout(<LeadsListPage />)} />
      <Route path="/leads/:leadId" element={withLayout(<LeadCardPage />)} />
      <Route path="/dashboard" element={withLayout(<DashboardPage />)} />
      <Route path="/reports/mop-cashflow" element={withLayout(<CashflowReportPage />)} />
      <Route path="/leaderboard" element={withLayout(<LeaderboardPage />)} />
      <Route path="/actions" element={withLayout(<ActionsPage />)} />
      <Route path="/tasks" element={withLayout(<TasksPage />)} />
      <Route path="/" element={<Navigate to="/leads" replace />} />
      <Route path="*" element={<Navigate to="/leads" replace />} />
    </Routes>
  );
}
