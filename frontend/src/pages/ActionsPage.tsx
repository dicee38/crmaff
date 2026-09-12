import { useCallback, useEffect, useState } from "react";
import type { CSSProperties, FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { api, ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Badge, Button, DataTable, Field, FilterBar, FormMessage, Input, KpiTile, PageHeader, Select } from "../ds";
import type { ActionListResponse, ActionRow, Channel, ManualActionCreate, Partner } from "../types";

const EVENT_TYPES = ["registration", "ftd", "deposit", "withdrawal", "chargeback"] as const;
const AMOUNT_REQUIRED = new Set(["ftd", "deposit", "withdrawal"]);

const EVENT_TYPE_LABELS: Record<ActionRow["event_type"], string> = {
  registration: "Регистрация",
  email_confirmed: "Подтверждение email",
  kyc_approved: "KYC подтверждён",
  ftd: "Первый депозит",
  deposit: "Повторный депозит",
  withdrawal: "Вывод средств",
  commission: "Комиссия",
  chargeback: "Чарджбэк",
};

const WARNING_LABELS: Record<string, string> = {
  unmatched_lead: "лид не сматчен",
  possible_duplicate: "возможный дубль",
};

const kpiGrid: CSSProperties = { display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: "var(--space-4)", marginBottom: "var(--space-5)" };
const formGrid: CSSProperties = { display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: "var(--space-5)", alignItems: "end" };

function formatDate(iso: string): string {
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}.${pad(d.getMonth() + 1)}.${pad(d.getDate())}`;
}

export function ActionsPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const isAdmin = user?.role === "admin";

  const [data, setData] = useState<ActionListResponse | null>(null);
  const [partners, setPartners] = useState<Partner[]>([]);
  const [channels, setChannels] = useState<Channel[]>([]);
  const [sourceFilter, setSourceFilter] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [form, setForm] = useState<ManualActionCreate>({
    player_id: "",
    partner_name: "",
    channel: "",
    event_type: "registration",
    amount: "",
    currency: "USD",
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchActions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = sourceFilter ? `?source=${sourceFilter}` : "";
      const resp = await api.get<ActionListResponse>(`/actions${params}`);
      setData(resp);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось загрузить журнал действий");
    } finally {
      setLoading(false);
    }
  }, [sourceFilter]);

  useEffect(() => {
    void fetchActions();
  }, [fetchActions]);

  useEffect(() => {
    api
      .get<Partner[]>("/partners")
      .then((list) => {
        setPartners(list);
        if (list.length > 0) {
          setForm((f) => (f.partner_name ? f : { ...f, partner_name: list[0].name }));
        }
      })
      .catch(() => undefined);
    api
      .get<Channel[]>("/channels")
      .then(setChannels)
      .catch(() => undefined);
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError(null);

    if (!form.partner_name) {
      setFormError("Выберите партнёрскую сеть");
      return;
    }
    if (AMOUNT_REQUIRED.has(form.event_type) && !form.amount) {
      setFormError(`Сумма обязательна для типа "${form.event_type}"`);
      return;
    }

    setSubmitting(true);
    try {
      await api.post("/actions", {
        ...form,
        channel: form.channel || undefined,
        amount: form.amount || undefined,
      });
      setForm({ ...form, player_id: "", amount: "" });
      await fetchActions();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Не удалось сохранить действие");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    if (!window.confirm("Удалить это действие безвозвратно?")) return;
    try {
      await api.delete(`/actions/${id}`);
      await fetchActions();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось удалить действие");
    }
  }

  return (
    <div>
      <PageHeader eyebrow="Учёт" title="Действия" />

      <div style={{ background: "var(--surface-card)", border: "var(--border-width) solid var(--border-subtle)", borderRadius: "var(--radius-md)", padding: "var(--space-6)", marginBottom: "var(--space-6)" }}>
        <h2 style={{ margin: "0 0 var(--space-5)", fontSize: "var(--text-micro)", fontWeight: "var(--weight-semibold)", letterSpacing: "var(--tracking-eyebrow)", textTransform: "uppercase", color: "var(--text-muted)" }}>
          Внести действие вручную
        </h2>
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "var(--space-5)" }}>
          <div style={formGrid}>
            <Field label="ID игрока" hint="click_id или telegram_user_id">
              <Input value={form.player_id} onChange={(e) => setForm({ ...form, player_id: e.target.value })} required />
            </Field>
            <Field label="Партнёрская сеть">
              <Select
                placeholder="Выберите..."
                value={form.partner_name}
                onChange={(e) => setForm({ ...form, partner_name: e.target.value })}
                options={partners.map((p) => ({ value: p.name, label: p.name }))}
              />
            </Field>
            <Field label="Канал">
              <Select
                placeholder="Без канала"
                value={form.channel}
                onChange={(e) => setForm({ ...form, channel: e.target.value })}
                options={channels.map((c) => ({ value: c.name, label: c.name }))}
              />
            </Field>
            <Field label="Тип действия">
              <Select
                value={form.event_type}
                onChange={(e) => setForm({ ...form, event_type: e.target.value as ManualActionCreate["event_type"] })}
                options={EVENT_TYPES.map((t) => ({ value: t, label: EVENT_TYPE_LABELS[t] ?? t }))}
              />
            </Field>
            <Field label="Сумма" required={AMOUNT_REQUIRED.has(form.event_type)}>
              <Input type="number" step="0.01" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} />
            </Field>
          </div>
          {formError ? <FormMessage tone="error">{formError}</FormMessage> : null}
          {partners.length === 0 ? (
            <FormMessage tone="hint">
              Нет ни одной партнёрской сети в справочнике.{" "}
              {isAdmin ? <a href="/admin" onClick={(e) => { e.preventDefault(); navigate("/admin"); }}>Добавьте её в админ-панели</a> : "Попросите администратора добавить её."}
            </FormMessage>
          ) : null}
          <div>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Сохранение..." : "Сохранить"}
            </Button>
          </div>
        </form>
      </div>

      <FilterBar>
        <Field label="Источник" style={{ width: 220 }}>
          <Select
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            options={[
              { value: "", label: "Все" },
              { value: "api", label: "Только API (postback)" },
              { value: "manual", label: "Только ручные" },
            ]}
          />
        </Field>
      </FilterBar>

      {error ? <FormMessage tone="error">{error}</FormMessage> : null}
      {loading ? <p>Загрузка...</p> : null}

      {data ? (
        <>
          <div style={kpiGrid}>
            <KpiTile label="Всего действий" value={data.aggregates.total_actions} />
            <KpiTile label="Уникальных лидов" value={data.aggregates.lead_count} />
            <KpiTile label="Депозитов" value={data.aggregates.deposit_count} />
            <KpiTile label="Сумма депозитов" value={data.aggregates.deposit_sum} unit="$" accent />
          </div>

          <DataTable
            rows={data.items}
            rowKey={(r) => r.id}
            emptyLabel="Действий не найдено"
            columns={[
              { key: "id", header: "ID", mono: true, render: (r) => r.id.slice(0, 8) },
              { key: "received_at", header: "Дата", mono: true, render: (r) => formatDate(r.received_at) },
              { key: "partner", header: "Партнёрская сеть" },
              { key: "channel", header: "Канал", render: (r) => r.channel ?? "—" },
              { key: "event_type", header: "Тип действия", render: (r) => EVENT_TYPE_LABELS[r.event_type] ?? r.event_type },
              { key: "player_external_id", header: "ID игрока", mono: true, render: (r) => r.player_external_id ?? "—" },
              {
                key: "amount",
                header: "Сумма депозита",
                align: "right",
                numeric: true,
                render: (r) => (r.amount != null ? `${r.amount} ${r.currency ?? ""}` : "—"),
              },
              {
                key: "manager_full_name",
                header: "МОП",
                render: (r) => (r.manager_full_name ? `${r.manager_full_name} — ${r.manager_role}` : "—"),
              },
              {
                key: "validation_flags",
                header: "Предупреждения",
                render: (r) =>
                  r.validation_flags ? (
                    <div style={{ display: "flex", gap: "var(--space-2)", flexWrap: "wrap" }}>
                      {Object.entries(r.validation_flags)
                        .filter(([, v]) => v)
                        .map(([key]) => (
                          <Badge key={key} tone="attention">
                            {WARNING_LABELS[key] ?? key}
                          </Badge>
                        ))}
                    </div>
                  ) : (
                    "—"
                  ),
              },
              {
                key: "lead_id",
                header: "Лид",
                render: (r) =>
                  r.lead_id ? (
                    <a href={`/leads/${r.lead_id}`} onClick={(e) => { e.preventDefault(); navigate(`/leads/${r.lead_id}`); }}>
                      лид
                    </a>
                  ) : (
                    "—"
                  ),
              },
              ...(isAdmin
                ? [
                    {
                      key: "_delete",
                      header: "",
                      render: (r: ActionRow) => (
                        <Button variant="danger" size="sm" onClick={() => void handleDelete(r.id)}>
                          Удалить
                        </Button>
                      ),
                    },
                  ]
                : []),
            ]}
          />
        </>
      ) : null}
    </div>
  );
}
