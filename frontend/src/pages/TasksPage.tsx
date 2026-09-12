import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";

import { api, ApiError } from "../api/client";
import { Badge, Button, Card, DataTable, Field, FilterBar, FormMessage, Input, PageHeader, Select } from "../ds";
import type { Task, TaskListResponse, TaskStatus } from "../types";

const TASK_STATUS_TONE: Record<TaskStatus, "neutral" | "positive" | "critical"> = {
  open: "neutral",
  done: "positive",
  cancelled: "critical",
};
const TASK_STATUS_LABEL: Record<TaskStatus, string> = { open: "открыта", done: "выполнена", cancelled: "отменена" };

export function TasksPage() {
  const [data, setData] = useState<TaskListResponse | null>(null);
  const [statusFilter, setStatusFilter] = useState<TaskStatus | "">("open");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [leadId, setLeadId] = useState("");
  const [title, setTitle] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = statusFilter ? `?status=${statusFilter}` : "";
      const resp = await api.get<TaskListResponse>(`/tasks${params}`);
      setData(resp);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось загрузить задачи");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    void fetchTasks();
  }, [fetchTasks]);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setFormError(null);
    setSubmitting(true);
    try {
      await api.post("/tasks", { lead_id: leadId, title });
      setLeadId("");
      setTitle("");
      await fetchTasks();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Не удалось создать задачу");
    } finally {
      setSubmitting(false);
    }
  }

  async function updateStatus(task: Task, status: TaskStatus) {
    try {
      await api.patch(`/tasks/${task.id}`, { status });
      await fetchTasks();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось обновить задачу");
    }
  }

  return (
    <div>
      <PageHeader eyebrow="Работа с лидами" title="Задачи" />

      <Card title="Новая задача" style={{ marginBottom: "var(--space-6)" }}>
        <form onSubmit={handleCreate} style={{ display: "flex", flexDirection: "column", gap: "var(--space-5)" }}>
          <div style={{ display: "flex", gap: "var(--space-5)", flexWrap: "wrap" }}>
            <Field label="Lead ID" style={{ flex: "1 1 260px" }}>
              <Input mono value={leadId} onChange={(e) => setLeadId(e.target.value)} required />
            </Field>
            <Field label="Заголовок" style={{ flex: "2 1 320px" }}>
              <Input value={title} onChange={(e) => setTitle(e.target.value)} required />
            </Field>
          </div>
          {formError ? <FormMessage tone="error">{formError}</FormMessage> : null}
          <div>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Создание..." : "Создать"}
            </Button>
          </div>
        </form>
      </Card>

      <FilterBar>
        <Field label="Статус" style={{ width: 200 }}>
          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as TaskStatus | "")}
            options={[
              { value: "", label: "Все" },
              { value: "open", label: "Открытые" },
              { value: "done", label: "Выполненные" },
              { value: "cancelled", label: "Отменённые" },
            ]}
          />
        </Field>
      </FilterBar>

      {error ? <FormMessage tone="error">{error}</FormMessage> : null}
      {loading ? <p>Загрузка...</p> : null}

      {data ? (
        <DataTable
          rows={data.items}
          rowKey={(r) => r.id}
          emptyLabel="Задач не найдено"
          columns={[
            { key: "title", header: "Заголовок" },
            { key: "lead_id", header: "Lead ID", mono: true, render: (r) => r.lead_id.slice(0, 8) + "…" },
            { key: "status", header: "Статус", render: (r) => <Badge tone={TASK_STATUS_TONE[r.status]}>{TASK_STATUS_LABEL[r.status]}</Badge> },
            { key: "due_at", header: "Дедлайн", mono: true, render: (r) => (r.due_at ? new Date(r.due_at).toLocaleString() : "—") },
            {
              key: "_actions",
              header: "",
              render: (r) =>
                r.status === "open" ? (
                  <div style={{ display: "flex", gap: "var(--space-3)" }}>
                    <Button size="sm" variant="secondary" onClick={() => void updateStatus(r, "done")}>
                      Готово
                    </Button>
                    <Button size="sm" variant="danger" onClick={() => void updateStatus(r, "cancelled")}>
                      Отменить
                    </Button>
                  </div>
                ) : null,
            },
          ]}
        />
      ) : null}
    </div>
  );
}
