import { useEffect, useState } from "react";
import type { CSSProperties } from "react";

import { api, ApiError } from "../api/client";
import { ARAB_COUNTRIES } from "../constants/geo";
import { Card, Field, FilterBar, FormMessage, FunnelRow, KpiTile, PageHeader, Select } from "../ds";
import type { FunnelData, KpiData } from "../types";

const kpiGrid: CSSProperties = { display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: "var(--space-4)", marginBottom: "var(--space-5)" };

export function DashboardPage() {
  const [funnel, setFunnel] = useState<FunnelData | null>(null);
  const [kpi, setKpi] = useState<KpiData | null>(null);
  const [geo, setGeo] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setError(null);
    const params = geo ? `?geo=${geo}` : "";
    Promise.all([api.get<FunnelData>(`/dashboard/funnel${params}`), api.get<KpiData>(`/dashboard/kpi${params}`)])
      .then(([f, k]) => {
        setFunnel(f);
        setKpi(k);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Не удалось загрузить дашборд"))
      .finally(() => setLoading(false));
  }, [geo]);

  const funnelStages: { key: keyof FunnelData; label: string; tone?: "brand" | "soft" | "data" | "accent" }[] = [
    { key: "clicks", label: "Клики", tone: "data" },
    { key: "leads_created", label: "Лиды", tone: "data" },
    { key: "manager_assigned", label: "Назначен менеджер", tone: "soft" },
    { key: "registered", label: "Регистрация", tone: "brand" },
    { key: "ftd", label: "FTD", tone: "accent" },
  ];

  const maxValue = funnel ? Math.max(...funnelStages.map((s) => Number(funnel[s.key]))) : 0;

  return (
    <div>
      <PageHeader eyebrow="Аналитика" title="Dashboard" />

      <FilterBar>
        <Field label="GEO" style={{ width: 220 }}>
          <Select
            placeholder="Все"
            value={geo}
            onChange={(e) => setGeo(e.target.value)}
            options={ARAB_COUNTRIES.map((c) => ({ value: c.code, label: `${c.name} (${c.code})` }))}
          />
        </Field>
      </FilterBar>

      {error ? <FormMessage tone="error">{error}</FormMessage> : null}
      {loading ? <p>Загрузка...</p> : null}

      {kpi ? (
        <div style={kpiGrid}>
          <KpiTile label="Лидов всего" value={kpi.total_leads} tone="data" />
          <KpiTile label="Регистраций" value={kpi.total_registered} tone="data" />
          <KpiTile label="FTD" value={kpi.total_ftd} />
          <KpiTile label="Lead → Reg" value={kpi.lead2reg_pct} unit="%" />
          <KpiTile label="Reg → FTD" value={kpi.reg2fd_pct} unit="%" />
          <KpiTile label="Revenue" value={kpi.total_revenue} unit="$" accent />
        </div>
      ) : null}

      {funnel ? (
        <Card title="Воронка">
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
            {funnelStages.map((stage) => {
              const value = Number(funnel[stage.key]);
              const percent = maxValue > 0 ? (value / maxValue) * 100 : 0;
              return <FunnelRow key={stage.key} label={stage.label} value={value} percent={percent} tone={stage.tone} />;
            })}
          </div>
        </Card>
      ) : null}
    </div>
  );
}
