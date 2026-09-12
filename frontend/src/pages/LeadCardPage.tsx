import { useEffect, useState } from "react";
import type { CSSProperties } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { api, ApiError } from "../api/client";
import { Card, DataTable, DefinitionList, FormMessage, StatusBadge, Timeline } from "../ds";
import type { LeadCard } from "../types";

const backLink: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: "var(--space-3)",
  fontFamily: "var(--font-body)",
  fontSize: "var(--text-caption)",
  color: "var(--text-link)",
  textDecoration: "none",
  background: "none",
  border: "none",
  padding: 0,
  cursor: "pointer",
  marginBottom: "var(--space-5)",
};
const cardGrid: CSSProperties = { display: "grid", gridTemplateColumns: "minmax(0,1fr) minmax(0,1fr)", gap: "var(--space-5)" };
const idStyle: CSSProperties = { fontFamily: "var(--font-mono)", fontSize: "var(--text-h2)" };
const eyebrow: CSSProperties = {
  display: "block",
  fontFamily: "var(--font-body)",
  fontSize: "var(--text-micro)",
  fontWeight: "var(--weight-semibold)",
  letterSpacing: "var(--tracking-eyebrow)",
  textTransform: "uppercase",
  color: "var(--navy-600)",
  marginBottom: "var(--space-3)",
};

export function LeadCardPage() {
  const { leadId } = useParams<{ leadId: string }>();
  const navigate = useNavigate();
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

  if (loading) return <p>Загрузка...</p>;
  if (error) return <FormMessage tone="error">{error}</FormMessage>;
  if (!card) return null;

  const { profile, acquisition, manager, communications, affiliate } = card;

  return (
    <div>
      <button style={backLink} onClick={() => navigate("/leads")}>
        ← К списку лидов
      </button>

      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: "var(--space-6)", marginBottom: "var(--space-6)" }}>
        <div style={{ minWidth: 0 }}>
          <span style={eyebrow}>Карточка лида</span>
          <h1 style={idStyle}>{profile.lead_id}</h1>
        </div>
        <StatusBadge status={profile.status} />
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-5)" }}>
        <div style={cardGrid}>
          <Card title="Профиль">
            <DefinitionList
              items={[
                { term: "GEO", value: profile.geo },
                { term: "Язык / диалект", value: `${profile.language ?? "—"} / ${profile.dialect ?? "—"}` },
                { term: "Telegram user id", value: profile.telegram_user_id, mono: true },
                { term: "Согласие", value: profile.consent_status },
                { term: "Создан", value: new Date(profile.created_at).toLocaleString(), mono: true },
              ]}
            />
          </Card>
          <Card title="Acquisition">
            {acquisition ? (
              <DefinitionList
                items={[
                  { term: "Канал", value: acquisition.source_channel },
                  { term: "Click ID", value: acquisition.click_id, mono: true },
                  {
                    term: "Campaign / Adset / Creative",
                    value: `${acquisition.campaign_id ?? "—"} / ${acquisition.adset_id ?? "—"} / ${acquisition.creative_id ?? "—"}`,
                    mono: true,
                  },
                  { term: "Landing", value: acquisition.landing_id, mono: true },
                  {
                    term: "Первый визит",
                    value: acquisition.first_seen_at ? new Date(acquisition.first_seen_at).toLocaleString() : null,
                    mono: true,
                  },
                ]}
              />
            ) : (
              <p style={{ margin: 0, color: "var(--text-muted)", fontSize: "var(--text-body-sm)" }}>Нет данных о привлечении</p>
            )}
          </Card>
        </div>

        <Card title="Менеджер">
          {manager ? (
            <DefinitionList items={[{ term: "Имя", value: manager.full_name }, { term: "Email", value: manager.email, mono: true }]} />
          ) : (
            <p style={{ margin: 0, color: "var(--text-muted)", fontSize: "var(--text-body-sm)" }}>Менеджер не назначен</p>
          )}
        </Card>

        <Card title={`Коммуникации (${communications.length})`}>
          <Timeline
            items={communications.map((c) => ({
              id: c.id,
              channel: c.channel,
              direction: c.direction,
              timestamp: new Date(c.created_at).toLocaleString(),
              text: c.message_text ?? "",
            }))}
          />
        </Card>

        <Card title={`Affiliate-события (${affiliate.length})`} padding="sm">
          <DataTable
            dense
            rows={affiliate}
            rowKey={(r) => r.id}
            emptyLabel="Affiliate-событий пока нет"
            columns={[
              { key: "event_type", header: "Событие" },
              {
                key: "amount",
                header: "Сумма",
                align: "right",
                numeric: true,
                render: (r) => (r.amount != null ? `${r.amount} ${r.currency ?? ""}` : "—"),
              },
              { key: "received_at", header: "Получено", mono: true, render: (r) => new Date(r.received_at).toLocaleString() },
            ]}
          />
        </Card>
      </div>
    </div>
  );
}
