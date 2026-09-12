import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { api, ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Button, Card, DefinitionList, Field, FormMessage, Input, PageHeader } from "../ds";

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
  const navigate = useNavigate();
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
      await api.post("/auth/change-password", { current_password: currentPassword, new_password: newPassword });
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
    <div>
      <PageHeader eyebrow="Аккаунт" title="Профиль" />

      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-5)" }}>
        <Card title="Данные аккаунта">
          <DefinitionList
            items={[
              { term: "Имя", value: user.full_name },
              { term: "Email", value: user.email, mono: true },
              { term: "Роль", value: ROLE_LABELS[user.role] ?? user.role },
              ...(user.geo_coverage.length > 0 ? [{ term: "GEO", value: user.geo_coverage.join(", ") }] : []),
              ...(user.dialects.length > 0 ? [{ term: "Диалекты", value: user.dialects.join(", ") }] : []),
            ]}
          />
        </Card>

        <Card title="Сменить пароль">
          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "var(--space-5)", maxWidth: 360 }}>
            <Field label="Текущий пароль">
              <Input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required />
            </Field>
            <Field label="Новый пароль">
              <Input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required minLength={8} />
            </Field>
            <Field label="Повторите новый пароль">
              <Input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required minLength={8} />
            </Field>
            {error ? <FormMessage tone="error">{error}</FormMessage> : null}
            {success ? <FormMessage tone="success">Пароль изменён</FormMessage> : null}
            <div>
              <Button type="submit" disabled={submitting}>
                {submitting ? "Сохранение..." : "Сменить пароль"}
              </Button>
            </div>
          </form>
        </Card>

        {user.role === "admin" ? (
          <p>
            <a href="/admin" onClick={(e) => { e.preventDefault(); navigate("/admin"); }}>
              Перейти в админ-панель →
            </a>
          </p>
        ) : null}
      </div>
    </div>
  );
}
