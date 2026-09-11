import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";

import { api, ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
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

function formatDate(iso: string): string {
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}.${pad(d.getMonth() + 1)}.${pad(d.getDate())}`;
}

export function ActionsPage() {
  const { user } = useAuth();
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
    <div className="page">
      <h1>Действия (постбэки + ручной ввод)</h1>

      <section className="card-block">
        <h2>Внести действие вручную</h2>
        <form className="actions-form" onSubmit={handleSubmit}>
          <label>
            ID игрока (click_id или telegram_user_id)
            <input
              value={form.player_id}
              onChange={(e) => setForm({ ...form, player_id: e.target.value })}
              required
            />
          </label>
          <label>
            Партнёрская сеть
            <select
              value={form.partner_name}
              onChange={(e) => setForm({ ...form, partner_name: e.target.value })}
              required
            >
              <option value="" disabled>
                Выберите...
              </option>
              {partners.map((p) => (
                <option key={p.id} value={p.name}>
                  {p.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Канал
            <select value={form.channel} onChange={(e) => setForm({ ...form, channel: e.target.value })}>
              <option value="">Без канала</option>
              {channels.map((c) => (
                <option key={c.id} value={c.name}>
                  {c.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Тип действия
            <select
              value={form.event_type}
              onChange={(e) => setForm({ ...form, event_type: e.target.value as ManualActionCreate["event_type"] })}
            >
              {EVENT_TYPES.map((t) => (
                <option key={t} value={t}>
                  {EVENT_TYPE_LABELS[t] ?? t}
                </option>
              ))}
            </select>
          </label>
          <label>
            Сумма {AMOUNT_REQUIRED.has(form.event_type) && <span className="required-mark">*</span>}
            <input
              type="number"
              step="0.01"
              value={form.amount}
              onChange={(e) => setForm({ ...form, amount: e.target.value })}
            />
          </label>
          {formError && <p className="form-error">{formError}</p>}
          <button type="submit" disabled={submitting}>
            {submitting ? "Сохранение..." : "Сохранить"}
          </button>
        </form>
        {partners.length === 0 && (
          <p className="empty-block">
            Нет ни одной партнёрской сети в справочнике.{" "}
            {isAdmin ? (
              <Link to="/admin">Добавьте её в админ-панели</Link>
            ) : (
              "Попросите администратора добавить её."
            )}
          </p>
        )}
      </section>

      <div className="filters">
        <label>
          Источник
          <select value={sourceFilter} onChange={(e) => setSourceFilter(e.target.value)}>
            <option value="">Все</option>
            <option value="api">Только API (postback)</option>
            <option value="manual">Только ручные</option>
          </select>
        </label>
      </div>

      {error && <p className="form-error">{error}</p>}
      {loading && <p>Загрузка...</p>}

      {data && (
        <>
          <div className="kpi-grid">
            <div className="kpi-tile">
              <span className="kpi-value">{data.aggregates.total_actions}</span>
              <span className="kpi-label">Всего действий</span>
            </div>
            <div className="kpi-tile">
              <span className="kpi-value">{data.aggregates.lead_count}</span>
              <span className="kpi-label">Уникальных лидов</span>
            </div>
            <div className="kpi-tile">
              <span className="kpi-value">{data.aggregates.deposit_count}</span>
              <span className="kpi-label">Депозитов</span>
            </div>
            <div className="kpi-tile">
              <span className="kpi-value">{data.aggregates.deposit_sum}</span>
              <span className="kpi-label">Сумма депозитов</span>
            </div>
          </div>

          <div className="table-scroll">
            <table className="actions-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Дата</th>
                  <th>Партнёрская сеть</th>
                  <th>Канал</th>
                  <th>Тип действия</th>
                  <th>ID игрока</th>
                  <th>Сумма депозита</th>
                  <th>Количество лидов</th>
                  <th>МОП</th>
                  <th>Предупреждения</th>
                  <th>Ошибки</th>
                  <th>Лид</th>
                  {isAdmin && <th></th>}
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.id}>
                    <td className="mono-cell" title={item.id}>
                      {item.id.slice(0, 8)}
                    </td>
                    <td>{formatDate(item.received_at)}</td>
                    <td>{item.partner}</td>
                    <td>{item.channel ?? "—"}</td>
                    <td>{EVENT_TYPE_LABELS[item.event_type] ?? item.event_type}</td>
                    <td>{item.player_external_id ?? "—"}</td>
                    <td>{item.amount != null ? `${item.amount} ${item.currency ?? ""}` : "—"}</td>
                    <td>—</td>
                    <td>
                      {item.manager_full_name ? `${item.manager_full_name} — ${item.manager_role}` : "—"}
                    </td>
                    <td>
                      {item.validation_flags &&
                        Object.entries(item.validation_flags)
                          .filter(([, v]) => v)
                          .map(([key]) => (
                            <span className="warning-badge" key={key}>
                              {WARNING_LABELS[key] ?? key}
                            </span>
                          ))}
                    </td>
                    <td>—</td>
                    <td>{item.lead_id && <Link to={`/leads/${item.lead_id}`}>лид</Link>}</td>
                    {isAdmin && (
                      <td>
                        <button onClick={() => handleDelete(item.id)} className="danger-link">
                          Удалить
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
                {data.items.length === 0 && (
                  <tr>
                    <td colSpan={isAdmin ? 13 : 12}>Действий не найдено</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
