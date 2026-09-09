import { useEffect, useState } from "react";

import { api, ApiError } from "../api/client";
import type { LeaderboardData, LeaderboardMetric, LeaderboardPeriod } from "../types";

const METRICS: { value: LeaderboardMetric; label: string }[] = [
  { value: "cashflow", label: "Касса" },
  { value: "fd_revenue_per_lead", label: "Выручка FD на лид" },
  { value: "lead_to_fd", label: "Lead → FD" },
  { value: "fd_to_rd", label: "FD → RD" },
];

const BADGES: Record<number, string> = { 1: "🥇", 2: "🥈", 3: "🥉" };

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
    <div className="page">
      <h1>Лидерборд</h1>

      <div className="filters">
        <label>
          Метрика
          <select value={metric} onChange={(e) => setMetric(e.target.value as LeaderboardMetric)}>
            {METRICS.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Период
          <select value={period} onChange={(e) => setPeriod(e.target.value as LeaderboardPeriod)}>
            <option value="week">Неделя</option>
            <option value="month">Месяц</option>
          </select>
        </label>
      </div>

      {error && <p className="form-error">{error}</p>}
      {loading && <p>Загрузка...</p>}

      {data && (
        <>
          {data.current_user_rank != null && (
            <div className="leaderboard-summary">
              <span>
                Ваша позиция: <strong>#{data.current_user_rank}</strong> из {data.total_participants}
              </span>
              {data.delta_to_rank_above != null && (
                <span>Не хватает {data.delta_to_rank_above} до следующей позиции</span>
              )}
              {data.delta_over_rank_below != null && (
                <span>Опережаете следующего на {data.delta_over_rank_below}</span>
              )}
            </div>
          )}

          <ul className="leaderboard-list">
            {data.rows.map((row, i) => {
              const prevRank = i > 0 ? data.rows[i - 1].rank : row.rank;
              const gap = row.rank - prevRank;
              return (
                <li key={row.manager_id}>
                  {i > 0 && gap > 1 && (
                    <div className="leaderboard-hidden-range">
                      Позиции {prevRank + 1}–{row.rank - 1} скрыты
                    </div>
                  )}
                  <div className={`leaderboard-row ${row.is_current_user ? "leaderboard-row-me" : ""}`}>
                    <span className="leaderboard-rank">{BADGES[row.rank] ?? `#${row.rank}`}</span>
                    <span className="leaderboard-name">
                      {row.label} {row.is_current_user && <em>(Вы)</em>}
                    </span>
                    <span className="leaderboard-value">{row.value}</span>
                  </div>
                </li>
              );
            })}
          </ul>
          {data.rows.length === 0 && <p className="empty-block">Пока нет данных за этот период</p>}
        </>
      )}
    </div>
  );
}
