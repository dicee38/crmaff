import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";

import { api, ApiError } from "../api/client";
import type { ActionListResponse, ManualActionCreate } from "../types";

const EVENT_TYPES = ["registration", "ftd", "deposit", "withdrawal", "chargeback"] as const;
const AMOUNT_REQUIRED = new Set(["ftd", "deposit", "withdrawal"]);

export function ActionsPage() {
  const [data, setData] = useState<ActionListResponse | null>(null);
  const [sourceFilter, setSourceFilter] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [form, setForm] = useState<ManualActionCreate>({
    player_id: "",
    partner_name: "Binolla",
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

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError(null);

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
            Партнёр
            <input
              value={form.partner_name}
              onChange={(e) => setForm({ ...form, partner_name: e.target.value })}
              required
            />
          </label>
          <label>
            Канал
            <input
              value={form.channel}
              onChange={(e) => setForm({ ...form, channel: e.target.value })}
              placeholder="MENA-KARIM"
            />
          </label>
          <label>
            Тип действия
            <select
              value={form.event_type}
              onChange={(e) => setForm({ ...form, event_type: e.target.value as ManualActionCreate["event_type"] })}
            >
              {EVENT_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
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

          <table className="actions-table">
            <thead>
              <tr>
                <th>Тип</th>
                <th>Источник</th>
                <th>Сумма</th>
                <th>Канал</th>
                <th>Предупреждения</th>
                <th>Дата</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((item) => (
                <tr key={item.id}>
                  <td>{item.event_type}</td>
                  <td>{item.source}</td>
                  <td>{item.amount != null ? `${item.amount} ${item.currency ?? ""}` : "—"}</td>
                  <td>{item.channel ?? "—"}</td>
                  <td>
                    {item.validation_flags?.unmatched_lead && (
                      <span className="warning-badge">лид не сматчен</span>
                    )}
                    {item.validation_flags?.possible_duplicate && (
                      <span className="warning-badge">возможный дубль</span>
                    )}
                  </td>
                  <td>{new Date(item.received_at).toLocaleString()}</td>
                </tr>
              ))}
              {data.items.length === 0 && (
                <tr>
                  <td colSpan={6}>Действий не найдено</td>
                </tr>
              )}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}
