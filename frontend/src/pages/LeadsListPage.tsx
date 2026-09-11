import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api, ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { ARAB_COUNTRIES } from "../constants/geo";
import type { Lead, LeadListResponse, LeadStatus } from "../types";

const STATUS_OPTIONS: LeadStatus[] = [
  "new",
  "contacted",
  "qualified",
  "registered",
  "kyc_pending",
  "kyc_approved",
  "ftd",
  "active",
  "churned",
  "unsubscribed",
];

export function LeadsListPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const [leads, setLeads] = useState<Lead[]>([]);
  const [geo, setGeo] = useState("");
  const [status, setStatus] = useState("");
  const [cursor, setCursor] = useState<string | null>(null);
  const [cursorHistory, setCursorHistory] = useState<(string | null)[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLeads = useCallback(
    async (targetCursor: string | null) => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        params.set("limit", "20");
        if (geo) params.set("geo", geo);
        if (status) params.set("status", status);
        if (targetCursor) params.set("cursor", targetCursor);

        const data = await api.get<LeadListResponse>(`/leads?${params.toString()}`);
        setLeads(data.items);
        setNextCursor(data.next_cursor);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Не удалось загрузить лидов");
      } finally {
        setLoading(false);
      }
    },
    [geo, status]
  );

  useEffect(() => {
    setCursor(null);
    setCursorHistory([]);
    void fetchLeads(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [geo, status]);

  function goNext() {
    if (!nextCursor) return;
    setCursorHistory((h) => [...h, cursor]);
    setCursor(nextCursor);
    void fetchLeads(nextCursor);
  }

  function goPrev() {
    const history = [...cursorHistory];
    const prev = history.pop() ?? null;
    setCursorHistory(history);
    setCursor(prev);
    void fetchLeads(prev);
  }

  async function handleDelete(leadId: string) {
    if (!window.confirm("Удалить этого лида безвозвратно? Связанные коммуникации/задачи будут удалены.")) return;
    try {
      await api.delete(`/leads/${leadId}`);
      await fetchLeads(cursor);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось удалить лида");
    }
  }

  return (
    <div className="page">
      <h1>Лиды</h1>

      <div className="filters">
        <label>
          GEO
          <select value={geo} onChange={(e) => setGeo(e.target.value)}>
            <option value="">Все</option>
            {ARAB_COUNTRIES.map((c) => (
              <option key={c.code} value={c.code}>
                {c.name} ({c.code})
              </option>
            ))}
          </select>
        </label>
        <label>
          Статус
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">Все</option>
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error && <p className="form-error">{error}</p>}
      {loading && <p>Загрузка...</p>}

      <table className="leads-table">
        <thead>
          <tr>
            <th>Lead ID</th>
            <th>GEO</th>
            <th>Статус</th>
            <th>Канал</th>
            <th>Создан</th>
            {isAdmin && <th></th>}
          </tr>
        </thead>
        <tbody>
          {leads.map((lead) => (
            <tr key={lead.lead_id}>
              <td>
                <Link to={`/leads/${lead.lead_id}`}>{lead.lead_id.slice(0, 8)}...</Link>
              </td>
              <td>{lead.geo ?? "—"}</td>
              <td>
                <span className={`status-badge status-${lead.status}`}>{lead.status}</span>
              </td>
              <td>{lead.source_channel}</td>
              <td>{new Date(lead.created_at).toLocaleString()}</td>
              {isAdmin && (
                <td>
                  <button onClick={() => handleDelete(lead.lead_id)} className="danger-link">
                    Удалить
                  </button>
                </td>
              )}
            </tr>
          ))}
          {!loading && leads.length === 0 && (
            <tr>
              <td colSpan={isAdmin ? 6 : 5}>Лидов не найдено</td>
            </tr>
          )}
        </tbody>
      </table>

      <div className="pagination">
        <button onClick={goPrev} disabled={cursorHistory.length === 0 && !cursor}>
          Назад
        </button>
        <button onClick={goNext} disabled={!nextCursor}>
          Вперёд
        </button>
      </div>
    </div>
  );
}
