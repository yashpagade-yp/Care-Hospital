import { useState, useTransition } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { FormField } from "@/components/ui/FormField";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { useAppSession } from "@/features/auth/session/AppSessionProvider";
import { demoAccounts } from "@/lib/mock/data";
import { formatRole } from "@/lib/utils/format";

type LoginForm = {
  email: string;
  password: string;
};

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAppSession();
  const [isPending, startTransition] = useTransition();
  const [form, setForm] = useState<LoginForm>({
    email: "patient@medcare.app",
    password: "patient123",
  });
  const [error, setError] = useState("");

  function updateField<K extends keyof LoginForm>(key: K, value: LoginForm[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    startTransition(async () => {
      try {
        const session = await login(form);
        const fallbackPath =
          location.state && typeof location.state === "object" && "from" in location.state
            ? String(location.state.from)
            : `/${session.role.toLowerCase()}/dashboard`;
        navigate(fallbackPath);
      } catch (caughtError) {
        setError(
          caughtError instanceof Error ? caughtError.message : "Login failed. Please try again.",
        );
      }
    });
  }

  return (
    <section className="content-page shell auth-shell">
      <div className="auth-card">
        <div className="auth-card__intro">
          <p className="eyebrow">Shared login</p>
          <h1>One entry point for every role in MedCare.</h1>
          <p>
            Patients, doctors, and admins all use the same email-and-password flow, then land
            in role-specific workspaces after authentication.
          </p>
        </div>

        <form className="form-panel" onSubmit={handleSubmit}>
          <h2>Sign in</h2>
          <FormField
            label="Email"
            type="email"
            value={form.email}
            onChange={(event) => updateField("email", event.target.value)}
            placeholder="name@example.com"
            required
          />
          <FormField
            label="Password"
            type="password"
            value={form.password}
            onChange={(event) => updateField("password", event.target.value)}
            placeholder="Enter your password"
            required
          />
          {error ? <StatusBanner tone="error">{error}</StatusBanner> : null}
          <button type="submit" className="button button--primary" disabled={isPending}>
            {isPending ? "Signing in..." : "Sign in"}
          </button>

          <div className="inline-links">
            <Link to="/auth/forgot-password">Forgot password?</Link>
            <Link to="/patient/register">Create patient account</Link>
          </div>
        </form>
      </div>

      <div className="info-grid">
        <article className="process-card">
          <p className="eyebrow">Demo accounts</p>
          <ul className="bullet-list">
            {demoAccounts.map((account) => (
              <li key={account.email}>
                <strong>{formatRole(account.role)}</strong>: {account.email} / {account.password}
              </li>
            ))}
          </ul>
        </article>

        <article className="process-card">
          <p className="eyebrow">Flow links</p>
          <ul className="bullet-list">
            <li>
              <Link to="/doctor/invite">Doctor invite validation</Link>
            </li>
            <li>
              <Link to="/patient/register">Patient registration and OTP</Link>
            </li>
            <li>
              <Link to="/auth/reset-password">Password reset completion</Link>
            </li>
          </ul>
        </article>
      </div>
    </section>
  );
}
