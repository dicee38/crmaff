import { useEffect, useState } from "react";

import { api, ApiError } from "../api/client";
import type { CashflowReport } from "../types";

export function CashflowReportPage() {
  const [report, setReport] = useState<CashflowReport | null>(null);
  const [groupBy, setGroupBy] = useState<"manager" | "channel">("manager");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .get<CashflowReport>(`/reports/mop-cashflow?group_by=${groupBy}`)
      .then(setReport)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Не удалось загрузить отчёт"))
      .finally(() => setLoading(false));
  }, [groupBy]);

  return (
    <div className="page">
      <h1>Cashflow-отчёт по МОП</h1>

      <div className="filters">
        <label>
          Группировка
          <select value={groupBy} onChange={(e) => setGroupBy(e.target.value as "manager" | "channel")}>
            <option value="manager">По менеджеру</option>
            <option value="channel">По каналу</option>
          </select>
        </label>
      </div>

      {error && <p className="form-error">{error}</p>}
      {loading && <p>Загрузка...</p>}

      {report && (
        <table className="cashflow-table">
          <thead>
            <tr>
              <th></th>
              <th>REG</th>
              <th>FD (шт / сумма)</th>
              <th>RD (шт / сумма)</th>
              <th>Касса</th>
              <th>Lead→Reg</th>
              <th>Reg→FD</th>
            </tr>
          </thead>
          <tbody>
            <tr className="cashflow-total-row">
              <td>Общий итог</td>
              <td>{report.total.reg}</td>
              <td>
                {report.total.fd_count} / {report.total.fd_sum}
              </td>
              <td>
                {report.total.rd_count} / {report.total.rd_sum}
              </td>
              <td>{report.total.cashflow}</td>
              <td>{report.total.lead2reg_pct != null ? `${report.total.lead2reg_pct}%` : "—"}</td>
              <td>{report.total.reg2fd_pct}%</td>
            </tr>
            {report.groups.map((row) => (
              <tr key={row.key}>
                <td className="cashflow-group-label">{row.label}</td>
                <td>{row.reg}</td>
                <td>
                  {row.fd_count} / {row.fd_sum}
                </td>
                <td>
                  {row.rd_count} / {row.rd_sum}
                </td>
                <td>{row.cashflow}</td>
                <td>{row.lead2reg_pct != null ? `${row.lead2reg_pct}%` : "—"}</td>
                <td>{row.reg2fd_pct}%</td>
              </tr>
            ))}
            {report.groups.length === 0 && (
              <tr>
                <td colSpan={7}>Нет данных для разбивки (или доступны только свои данные)</td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}
