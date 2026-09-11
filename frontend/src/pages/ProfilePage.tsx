import { useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";

import { api, ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";

const ROLE_LABELS: Record<string, string> = {
  admin: "Администратор",
  tech_lead: "Технический руководитель",
  compliance: "Compliance",
  affiliate_manager: "Affiliate-менеджер",
  mop_lead: "Руководитель группы МОП",
  sales_manager: "Менеджер (МОП)",
  smm_manager: "SMM-менеджер",
  analyst: "Аналитик",
};

export function ProfilePage() {
  const { user } = useAuth();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  if (!user) return null;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    if (newPassword.length < 8) {
      setError("Новый пароль должен быть не короче 8 символов");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Пароли не совпадают");
      return;
    }

    setSubmitting(true);
    try {
      await api.post("/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setSuccess(true);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось сменить пароль");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page">
      <h1>Профиль</h1>

      <section className="card-block">
        <h2>Данные аккаунта</h2>
        <dl>
          <dt>Имя</dt>
          <dd>{user.full_name}</dd>
          <dt>Email</dt>
          <dd>{user.email}</dd>
          <dt>Роль</dt>
          <dd>{ROLE_LABELS[user.role] ?? user.role}</dd>
          {user.geo_coverage.length > 0 && (
            <>
              <dt>GEO</dt>
              <dd>{user.geo_coverage.join(", ")}</dd>
            </>
          )}
          {user.dialects.length > 0 && (
            <>
              <dt>Диалекты</dt>
              <dd>{user.dialects.join(", ")}</dd>
            </>
          )}
        </dl>
      </section>

      <section className="card-block">
        <h2>Сменить пароль</h2>
        <form className="actions-form" onSubmit={handleSubmit}>
          <label>
            Текущий пароль
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
            />
          </label>
          <label>
            Новый пароль
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={8}
            />
          </label>
          <label>
            Повторите новый пароль
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              minLength={8}
            />
          </label>
          {error && <p className="form-error">{error}</p>}
          {success && <p className="form-success">Пароль изменён</p>}
          <button type="submit" disabled={submitting}>
            {submitting ? "Сохранение..." : "Сменить пароль"}
          </button>
        </form>
      </section>

      {user.role === "admin" && (
        <p>
          <Link to="/admin">Перейти в админ-панель →</Link>
        </p>
      )}
    </div>
  );
}
