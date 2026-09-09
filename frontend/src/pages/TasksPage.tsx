import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";

import { api, ApiError } from "../api/client";
import type { Task, TaskListResponse, TaskStatus } from "../types";

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
    <div className="page">
      <h1>Задачи</h1>

      <section className="card-block">
        <h2>Новая задача</h2>
        <form className="actions-form" onSubmit={handleCreate}>
          <label>
            Lead ID
            <input value={leadId} onChange={(e) => setLeadId(e.target.value)} required />
          </label>
          <label>
            Заголовок
            <input value={title} onChange={(e) => setTitle(e.target.value)} required />
          </label>
          {formError && <p className="form-error">{formError}</p>}
          <button type="submit" disabled={submitting}>
            {submitting ? "Создание..." : "Создать"}
          </button>
        </form>
      </section>

      <div className="filters">
        <label>
          Статус
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as TaskStatus | "")}>
            <option value="">Все</option>
            <option value="open">Открытые</option>
            <option value="done">Выполненные</option>
            <option value="cancelled">Отменённые</option>
          </select>
        </label>
      </div>

      {error && <p className="form-error">{error}</p>}
      {loading && <p>Загрузка...</p>}

      {data && (
        <table className="leads-table">
          <thead>
            <tr>
              <th>Заголовок</th>
              <th>Lead ID</th>
              <th>Статус</th>
              <th>Дедлайн</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((task) => (
              <tr key={task.id}>
                <td>{task.title}</td>
                <td>{task.lead_id.slice(0, 8)}...</td>
                <td>
                  <span className={`status-badge status-${task.status}`}>{task.status}</span>
                </td>
                <td>{task.due_at ? new Date(task.due_at).toLocaleString() : "—"}</td>
                <td>
                  {task.status === "open" && (
                    <>
                      <button onClick={() => updateStatus(task, "done")}>Готово</button>{" "}
                      <button onClick={() => updateStatus(task, "cancelled")}>Отменить</button>
                    </>
                  )}
                </td>
              </tr>
            ))}
            {data.items.length === 0 && (
              <tr>
                <td colSpan={5}>Задач не найдено</td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}
