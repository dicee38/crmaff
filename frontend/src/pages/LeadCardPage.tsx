import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api, ApiError } from "../api/client";
import type { LeadCard } from "../types";

export function LeadCardPage() {
  const { leadId } = useParams<{ leadId: string }>();
  const [card, setCard] = useState<LeadCard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!leadId) return;
    setLoading(true);
    setError(null);
    api
      .get<LeadCard>(`/leads/${leadId}/card`)
      .then(setCard)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Не удалось загрузить карточку лида"))
      .finally(() => setLoading(false));
  }, [leadId]);

  if (loading) return <div className="page">Загрузка...</div>;
  if (error) return <div className="page form-error">{error}</div>;
  if (!card) return null;

  const { profile, acquisition, manager, communications, affiliate } = card;

  return (
    <div className="page">
      <p>
        <Link to="/leads">&larr; К списку лидов</Link>
      </p>
      <h1>Лид {profile.lead_id}</h1>

      <section className="card-block">
        <h2>Профиль</h2>
        <dl>
          <dt>GEO</dt>
          <dd>{profile.geo ?? "—"}</dd>
          <dt>Язык / диалект</dt>
          <dd>
            {profile.language ?? "—"} / {profile.dialect ?? "—"}
          </dd>
          <dt>Статус</dt>
          <dd>
            <span className={`status-badge status-${profile.status}`}>{profile.status}</span>
          </dd>
          <dt>Telegram user id</dt>
          <dd>{profile.telegram_user_id ?? "—"}</dd>
          <dt>Согласие на коммуникацию</dt>
          <dd>{profile.consent_status}</dd>
          <dt>Создан</dt>
          <dd>{new Date(profile.created_at).toLocaleString()}</dd>
        </dl>
      </section>

      <section className="card-block">
        <h2>Acquisition</h2>
        {acquisition ? (
          <dl>
            <dt>Канал</dt>
            <dd>{acquisition.source_channel}</dd>
            <dt>Click ID</dt>
            <dd>{acquisition.click_id ?? "—"}</dd>
            <dt>Campaign / Adset / Creative</dt>
            <dd>
              {acquisition.campaign_id ?? "—"} / {acquisition.adset_id ?? "—"} / {acquisition.creative_id ?? "—"}
            </dd>
            <dt>Landing</dt>
            <dd>{acquisition.landing_id ?? "—"}</dd>
            <dt>Первый визит</dt>
            <dd>{acquisition.first_seen_at ? new Date(acquisition.first_seen_at).toLocaleString() : "—"}</dd>
          </dl>
        ) : (
          <p className="empty-block">Нет данных о привлечении</p>
        )}
      </section>

      <section className="card-block">
        <h2>Менеджер</h2>
        {manager ? (
          <dl>
            <dt>Имя</dt>
            <dd>{manager.full_name}</dd>
            <dt>Email</dt>
            <dd>{manager.email}</dd>
          </dl>
        ) : (
          <p className="empty-block">Менеджер не назначен</p>
        )}
      </section>

      <section className="card-block">
        <h2>Коммуникации ({communications.length})</h2>
        {communications.length > 0 ? (
          <ul className="comm-list">
            {communications.map((c) => (
              <li key={c.id} className={`comm-item comm-${c.direction}`}>
                <span className="comm-meta">
                  {c.channel} · {c.direction} · {new Date(c.created_at).toLocaleString()}
                </span>
                <p>{c.message_text}</p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="empty-block">Коммуникаций пока нет</p>
        )}
      </section>

      <section className="card-block">
        <h2>Affiliate-события ({affiliate.length})</h2>
        {affiliate.length > 0 ? (
          <table className="affiliate-table">
            <thead>
              <tr>
                <th>Событие</th>
                <th>Сумма</th>
                <th>Дата</th>
              </tr>
            </thead>
            <tbody>
              {affiliate.map((e) => (
                <tr key={e.id}>
                  <td>{e.event_type}</td>
                  <td>{e.amount != null ? `${e.amount} ${e.currency ?? ""}` : "—"}</td>
                  <td>{new Date(e.received_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="empty-block">Affiliate-событий пока нет</p>
        )}
      </section>
    </div>
  );
}
