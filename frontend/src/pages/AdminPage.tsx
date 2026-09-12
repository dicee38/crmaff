import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";

import { api, ApiError } from "../api/client";
import { Badge, Button, Card, DataTable, Field, FormMessage, Input, PageHeader } from "../ds";
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
      const [partnersResp, channelsResp] = await Promise.all([api.get<Partner[]>("/partners"), api.get<Channel[]>("/channels")]);
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
    <div>
      <PageHeader eyebrow="Управление" title="Админ-панель" />
      {error ? <FormMessage tone="error">{error}</FormMessage> : null}
      {loading ? <p>Загрузка...</p> : null}

      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-6)" }}>
        <Card title="Партнёрские сети">
          <form onSubmit={handleAddPartner} style={{ display: "flex", gap: "var(--space-4)", alignItems: "end", marginBottom: "var(--space-5)" }}>
            <Field label="Название" style={{ flex: "1 1 260px" }}>
              <Input value={newPartner} onChange={(e) => setNewPartner(e.target.value)} placeholder="PocketOption" />
            </Field>
            <Button type="submit">Добавить</Button>
          </form>
          <DataTable
            rows={partners}
            rowKey={(p) => p.id}
            emptyLabel="Партнёров пока нет"
            columns={[
              { key: "name", header: "Название" },
              {
                key: "is_active",
                header: "Статус",
                render: (p) => <Badge tone={p.is_active ? "positive" : "neutral"}>{p.is_active ? "активен" : "выключен"}</Badge>,
              },
              {
                key: "_toggle",
                header: "",
                render: (p) => (
                  <Button size="sm" variant="secondary" onClick={() => void togglePartner(p)}>
                    {p.is_active ? "Выключить" : "Включить"}
                  </Button>
                ),
              },
            ]}
          />
        </Card>

        <Card title="Каналы">
          <form onSubmit={handleAddChannel} style={{ display: "flex", gap: "var(--space-4)", alignItems: "end", marginBottom: "var(--space-5)" }}>
            <Field label="Название" style={{ flex: "1 1 260px" }}>
              <Input value={newChannel} onChange={(e) => setNewChannel(e.target.value)} placeholder="MENA-Karim" />
            </Field>
            <Button type="submit">Добавить</Button>
          </form>
          <DataTable
            rows={channels}
            rowKey={(c) => c.id}
            emptyLabel="Каналов пока нет"
            columns={[
              { key: "name", header: "Название" },
              {
                key: "is_active",
                header: "Статус",
                render: (c) => <Badge tone={c.is_active ? "positive" : "neutral"}>{c.is_active ? "активен" : "выключен"}</Badge>,
              },
              {
                key: "_toggle",
                header: "",
                render: (c) => (
                  <Button size="sm" variant="secondary" onClick={() => void toggleChannel(c)}>
                    {c.is_active ? "Выключить" : "Включить"}
                  </Button>
                ),
              },
            ]}
          />
        </Card>
      </div>
    </div>
  );
}
