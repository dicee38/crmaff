import { Fragment, useEffect, useState } from "react";
import type { CSSProperties } from "react";

import { api, ApiError } from "../api/client";
import { Field, FilterBar, FormMessage, LeaderboardRow, PageHeader, Select } from "../ds";
import type { LeaderboardData, LeaderboardMetric, LeaderboardPeriod } from "../types";

const METRICS: { value: LeaderboardMetric; label: string }[] = [
  { value: "cashflow", label: "Касса" },
  { value: "fd_revenue_per_lead", label: "Выручка FD на лид" },
  { value: "lead_to_fd", label: "Lead → FD" },
  { value: "fd_to_rd", label: "FD → RD" },
];

const summaryShell: CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  gap: "var(--space-6)",
  background: "var(--surface-card)",
  border: "var(--border-width) solid var(--border-subtle)",
  borderRadius: "var(--radius-md)",
  padding: "var(--space-5) var(--space-6)",
  marginBottom: "var(--space-5)",
  fontFamily: "var(--font-body)",
  fontSize: "var(--text-body-sm)",
};
const hiddenRange: CSSProperties = {
  textAlign: "center",
  fontFamily: "var(--font-mono)",
  fontSize: "var(--text-micro)",
  color: "var(--text-muted)",
  padding: "var(--space-2) 0",
  letterSpacing: "var(--tracking-mono)",
};

export function LeaderboardPage() {
  const [metric, setMetric] = useState<LeaderboardMetric>("cashflow");
  const [period, setPeriod] = useState<LeaderboardPeriod>("week");
  const [data, setData] = useState<LeaderboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .get<LeaderboardData>(`/leaderboard?metric=${metric}&period=${period}`)
      .then(setData)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Не удалось загрузить лидерборд"))
      .finally(() => setLoading(false));
  }, [metric, period]);

  return (
    <div>
      <PageHeader eyebrow="Команда" title="Лидерборд" />

      <FilterBar>
        <Field label="Метрика" style={{ width: 220 }}>
          <Select value={metric} onChange={(e) => setMetric(e.target.value as LeaderboardMetric)} options={METRICS} />
        </Field>
        <Field label="Период" style={{ width: 160 }}>
          <Select
            value={period}
            onChange={(e) => setPeriod(e.target.value as LeaderboardPeriod)}
            options={[
              { value: "week", label: "Неделя" },
              { value: "month", label: "Месяц" },
            ]}
          />
        </Field>
      </FilterBar>

      {error ? <FormMessage tone="error">{error}</FormMessage> : null}
      {loading ? <p>Загрузка...</p> : null}

      {data ? (
        <>
          {data.current_user_rank != null ? (
            <div style={summaryShell}>
              <span>
                Ваша позиция: <strong>#{data.current_user_rank}</strong> из {data.total_participants}
              </span>
              {data.delta_to_rank_above != null ? (
                <span style={{ color: "var(--text-muted)" }}>Не хватает {data.delta_to_rank_above} до следующей позиции</span>
              ) : null}
              {data.delta_over_rank_below != null ? (
                <span style={{ color: "var(--text-muted)" }}>Опережаете следующего на {data.delta_over_rank_below}</span>
              ) : null}
            </div>
          ) : null}

          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
            {data.rows.map((row, i) => {
              const prevRank = i > 0 ? data.rows[i - 1].rank : row.rank;
              const gap = row.rank - prevRank;
              return (
                <Fragment key={row.manager_id}>
                  {i > 0 && gap > 1 ? (
                    <div style={hiddenRange}>
                      Позиции {prevRank + 1}–{row.rank - 1} скрыты
                    </div>
                  ) : null}
                  <LeaderboardRow rank={row.rank} label={row.label} value={row.value} isCurrentUser={row.is_current_user} />
                </Fragment>
              );
            })}
          </div>
          {data.rows.length === 0 ? <p style={{ color: "var(--text-muted)" }}>Пока нет данных за этот период</p> : null}
        </>
      ) : null}
    </div>
  );
}
