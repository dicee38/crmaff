import { useEffect, useState } from "react";

import { api, ApiError } from "../api/client";
import { DataTable, Field, FilterBar, FormMessage, PageHeader, Select } from "../ds";
import type { CashflowReport, CashflowRow } from "../types";

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

  const rows: (CashflowRow & { isTotal?: boolean })[] = report ? [{ ...report.total, label: "Общий итог", isTotal: true }, ...report.groups] : [];

  return (
    <div>
      <PageHeader eyebrow="Эффективность" title="Cashflow-отчёт по МОП" />

      <FilterBar>
        <Field label="Группировка" style={{ width: 220 }}>
          <Select
            value={groupBy}
            onChange={(e) => setGroupBy(e.target.value as "manager" | "channel")}
            options={[
              { value: "manager", label: "По менеджеру" },
              { value: "channel", label: "По каналу" },
            ]}
          />
        </Field>
      </FilterBar>

      {error ? <FormMessage tone="error">{error}</FormMessage> : null}
      {loading ? <p>Загрузка...</p> : null}

      {report ? (
        <DataTable
          rows={rows}
          rowKey={(r) => r.key ?? "total"}
          emptyLabel="Нет данных для разбивки (или доступны только свои данные)"
          columns={[
            {
              key: "label",
              header: "",
              render: (r) => <span style={r.isTotal ? { fontWeight: "var(--weight-semibold)" } : { color: "var(--text-muted)" }}>{r.label}</span>,
            },
            { key: "reg", header: "REG", align: "right", numeric: true },
            { key: "fd", header: "FD (шт / сумма)", align: "right", render: (r) => `${r.fd_count} / ${r.fd_sum}` },
            { key: "rd", header: "RD (шт / сумма)", align: "right", render: (r) => `${r.rd_count} / ${r.rd_sum}` },
            { key: "cashflow", header: "Касса", align: "right", numeric: true },
            { key: "lead2reg_pct", header: "Lead→Reg", align: "right", render: (r) => (r.lead2reg_pct != null ? `${r.lead2reg_pct}%` : "—") },
            { key: "reg2fd_pct", header: "Reg→FTD", align: "right", render: (r) => `${r.reg2fd_pct}%` },
          ]}
        />
      ) : null}
    </div>
  );
}
