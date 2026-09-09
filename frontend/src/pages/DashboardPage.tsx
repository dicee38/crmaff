import { useEffect, useState } from "react";

import { api, ApiError } from "../api/client";
import type { FunnelData, KpiData } from "../types";

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
    Promise.all([
      api.get<FunnelData>(`/dashboard/funnel${params}`),
      api.get<KpiData>(`/dashboard/kpi${params}`),
    ])
      .then(([f, k]) => {
        setFunnel(f);
        setKpi(k);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Не удалось загрузить дашборд"))
      .finally(() => setLoading(false));
  }, [geo]);

  const funnelStages: { key: keyof FunnelData; label: string }[] = [
    { key: "clicks", label: "Клики" },
    { key: "leads_created", label: "Лиды" },
    { key: "manager_assigned", label: "Назначен менеджер" },
    { key: "registered", label: "Регистрация" },
    { key: "ftd", label: "FTD" },
  ];

  const maxValue = funnel ? Math.max(...funnelStages.map((s) => Number(funnel[s.key]))) : 0;

  return (
    <div className="page">
      <h1>Dashboard</h1>

      <div className="filters">
        <label>
          GEO
          <select value={geo} onChange={(e) => setGeo(e.target.value)}>
            <option value="">Все</option>
            <option value="SY">Сирия (SY)</option>
            <option value="MA">Марокко (MA)</option>
            <option value="SA">Саудовская Аравия (SA)</option>
          </select>
        </label>
      </div>

      {error && <p className="form-error">{error}</p>}
      {loading && <p>Загрузка...</p>}

      {kpi && (
        <div className="kpi-grid">
          <div className="kpi-tile">
            <span className="kpi-value">{kpi.total_leads}</span>
            <span className="kpi-label">Лидов всего</span>
          </div>
          <div className="kpi-tile">
            <span className="kpi-value">{kpi.total_registered}</span>
            <span className="kpi-label">Регистраций</span>
          </div>
          <div className="kpi-tile">
            <span className="kpi-value">{kpi.total_ftd}</span>
            <span className="kpi-label">FTD</span>
          </div>
          <div className="kpi-tile">
            <span className="kpi-value">{kpi.total_revenue}</span>
            <span className="kpi-label">Revenue</span>
          </div>
          <div className="kpi-tile">
            <span className="kpi-value">{kpi.lead2reg_pct}%</span>
            <span className="kpi-label">Lead → Reg</span>
          </div>
          <div className="kpi-tile">
            <span className="kpi-value">{kpi.reg2fd_pct}%</span>
            <span className="kpi-label">Reg → FTD</span>
          </div>
        </div>
      )}

      {funnel && (
        <section className="card-block">
          <h2>Воронка</h2>
          <div className="funnel">
            {funnelStages.map((stage) => {
              const value = Number(funnel[stage.key]);
              const widthPct = maxValue > 0 ? Math.max((value / maxValue) * 100, 4) : 4;
              return (
                <div className="funnel-row" key={stage.key}>
                  <span className="funnel-label">{stage.label}</span>
                  <div className="funnel-bar-track">
                    <div className="funnel-bar" style={{ width: `${widthPct}%` }} />
                  </div>
                  <span className="funnel-value">{value}</span>
                </div>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}
