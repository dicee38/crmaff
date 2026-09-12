import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api, ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { ARAB_COUNTRIES } from "../constants/geo";
import { Button, DataTable, Field, FilterBar, FormMessage, Pagination, PageHeader, Select, StatusBadge } from "../ds";
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
  const navigate = useNavigate();
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
    <div>
      <PageHeader eyebrow="Пайплайн" title="Лиды" />

      <FilterBar>
        <Field label="GEO" style={{ width: 220 }}>
          <Select
            placeholder="Все"
            value={geo}
            onChange={(e) => setGeo(e.target.value)}
            options={ARAB_COUNTRIES.map((c) => ({ value: c.code, label: `${c.name} (${c.code})` }))}
          />
        </Field>
        <Field label="Статус" style={{ width: 200 }}>
          <Select
            placeholder="Все"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            options={STATUS_OPTIONS.map((s) => ({ value: s, label: s }))}
          />
        </Field>
      </FilterBar>

      {error ? <FormMessage tone="error">{error}</FormMessage> : null}

      <DataTable
        rows={leads}
        rowKey={(r) => r.lead_id}
        onRowClick={(r) => navigate(`/leads/${r.lead_id}`)}
        emptyLabel={loading ? "Загрузка..." : "Лидов не найдено"}
        columns={[
          { key: "lead_id", header: "Lead ID", mono: true, render: (r) => r.lead_id.slice(0, 8) + "…" },
          { key: "geo", header: "GEO", render: (r) => r.geo ?? "—" },
          { key: "status", header: "Статус", render: (r) => <StatusBadge status={r.status} /> },
          { key: "source_channel", header: "Канал" },
          { key: "created_at", header: "Создан", mono: true, render: (r) => new Date(r.created_at).toLocaleString() },
          ...(isAdmin
            ? [
                {
                  key: "_delete",
                  header: "",
                  render: (r: Lead) => (
                    <Button variant="danger" size="sm" onClick={() => void handleDelete(r.lead_id)}>
                      Удалить
                    </Button>
                  ),
                },
              ]
            : []),
        ]}
      />

      <Pagination
        hasPrev={cursorHistory.length > 0 || !!cursor}
        hasNext={!!nextCursor}
        onPrev={goPrev}
        onNext={goNext}
      />
    </div>
  );
}
