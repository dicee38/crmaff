import { useState } from "react";
import type { CSSProperties, FormEvent } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Button, Field, FormMessage, Input, Logo } from "../ds";

const loginPage: CSSProperties = {
  minHeight: "100vh",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  background: "var(--bone-100)",
  padding: "var(--space-9) var(--space-5)",
};
const loginForm: CSSProperties = {
  background: "var(--surface-card)",
  border: "var(--border-width) solid var(--border-subtle)",
  borderRadius: "var(--radius-md)",
  padding: "var(--space-8)",
  width: "340px",
  display: "flex",
  flexDirection: "column",
  gap: "var(--space-5)",
};
const loginTitle: CSSProperties = { fontFamily: "var(--font-display)", fontSize: "var(--text-h2)", fontWeight: 600, letterSpacing: "var(--tracking-heading)", margin: 0 };

export function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [totpCode, setTotpCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (user) {
    return <Navigate to="/leads" replace />;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password, totpCode);
      navigate("/leads");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Ошибка входа");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={loginPage}>
      <form style={loginForm} onSubmit={handleSubmit}>
        <Logo size={28} />
        <div>
          <h1 style={loginTitle}>Вход в CRM</h1>
          <FormMessage tone="hint">Партнёрская платформа Verdance · MENA</FormMessage>
        </div>
        <Field label="Email">
          <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus />
        </Field>
        <Field label="Пароль">
          <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </Field>
        <Field label="2FA-код" hint="Только для роли admin">
          <Input mono inputMode="numeric" placeholder="123456" value={totpCode} onChange={(e) => setTotpCode(e.target.value)} />
        </Field>
        {error ? <FormMessage tone="error">{error}</FormMessage> : null}
        <Button type="submit" fullWidth disabled={submitting}>
          {submitting ? "Вход..." : "Войти"}
        </Button>
      </form>
    </div>
  );
}
