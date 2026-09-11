import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";

import { api, ApiError } from "../api/client";
import type { Channel, Partner } from "../types";

export function AdminPage() {
  const [partners, setPartners] = useState<Partner[]>([]);
  const [channels, setChannels] = useState<Channel[]>([]);
  const [newPartner, setNewPartner] = useState("");
  const [newChannel, setNewChannel] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [partnersResp, channelsResp] = await Promise.all([
        api.get<Partner[]>("/partners"),
        api.get<Channel[]>("/channels"),
      ]);
      setPartners(partnersResp);
      setChannels(channelsResp);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось загрузить справочники");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchAll();
  }, [fetchAll]);

  async function handleAddPartner(e: FormEvent) {
    e.preventDefault();
    if (!newPartner.trim()) return;
    try {
      await api.post("/partners", { name: newPartner.trim() });
      setNewPartner("");
      await fetchAll();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось добавить партнёра");
    }
  }

  async function handleAddChannel(e: FormEvent) {
    e.preventDefault();
    if (!newChannel.trim()) return;
    try {
      await api.post("/channels", { name: newChannel.trim() });
      setNewChannel("");
      await fetchAll();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось добавить канал");
    }
  }

  async function togglePartner(p: Partner) {
    try {
      await api.patch(`/partners/${p.id}`, { is_active: !p.is_active });
      await fetchAll();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось обновить партнёра");
    }
  }

  async function toggleChannel(c: Channel) {
    try {
      await api.patch(`/channels/${c.id}`, { is_active: !c.is_active });
      await fetchAll();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось обновить канал");
    }
  }

  return (
    <div className="page">
      <h1>Админ-панель</h1>
      {error && <p className="form-error">{error}</p>}
      {loading && <p>Загрузка...</p>}

      <section className="card-block">
        <h2>Партнёрские сети</h2>
        <form className="actions-form" onSubmit={handleAddPartner}>
          <label>
            Название
            <input value={newPartner} onChange={(e) => setNewPartner(e.target.value)} placeholder="PocketOption" />
          </label>
          <button type="submit">Добавить</button>
        </form>
        <table className="leads-table">
          <thead>
            <tr>
              <th>Название</th>
              <th>Статус</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {partners.map((p) => (
              <tr key={p.id}>
                <td>{p.name}</td>
                <td>
                  <span className={`status-badge ${p.is_active ? "status-active" : "status-churned"}`}>
                    {p.is_active ? "активен" : "выключен"}
                  </span>
                </td>
                <td>
                  <button onClick={() => togglePartner(p)}>{p.is_active ? "Выключить" : "Включить"}</button>
                </td>
              </tr>
            ))}
            {partners.length === 0 && !loading && (
              <tr>
                <td colSpan={3}>Партнёров пока нет</td>
              </tr>
            )}
          </tbody>
        </table>
      </section>

      <section className="card-block">
        <h2>Каналы</h2>
        <form className="actions-form" onSubmit={handleAddChannel}>
          <label>
            Название
            <input value={newChannel} onChange={(e) => setNewChannel(e.target.value)} placeholder="MENA-Karim" />
          </label>
          <button type="submit">Добавить</button>
        </form>
        <table className="leads-table">
          <thead>
            <tr>
              <th>Название</th>
              <th>Статус</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {channels.map((c) => (
              <tr key={c.id}>
                <td>{c.name}</td>
                <td>
                  <span className={`status-badge ${c.is_active ? "status-active" : "status-churned"}`}>
                    {c.is_active ? "активен" : "выключен"}
                  </span>
                </td>
                <td>
                  <button onClick={() => toggleChannel(c)}>{c.is_active ? "Выключить" : "Включить"}</button>
                </td>
              </tr>
            ))}
            {channels.length === 0 && !loading && (
              <tr>
                <td colSpan={3}>Каналов пока нет</td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}
