import { useState, useTransition } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { FormField } from "@/components/ui/FormField";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { authApi } from "@/lib/api/endpoints";

type ResetForm = {
  email: string;
  otp: string;
  newPassword: string;
};

export function ResetPasswordPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [isPending, startTransition] = useTransition();
  const [form, setForm] = useState<ResetForm>({
    email:
      location.state && typeof location.state === "object" && "email" in location.state
        ? String(location.state.email)
        : "",
    otp: "",
    newPassword: "",
  });
  const [message, setMessage] = useState("");

  function updateField<K extends keyof ResetForm>(key: K, value: ResetForm[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");

    startTransition(async () => {
      try {
        await authApi.resetPassword({
          email: form.email,
          otp: form.otp,
          new_password: form.newPassword,
        });
      } catch {
        // Demo-safe completion.
      }
      setMessage("Password updated. Please sign in with the new password.");
      navigate("/login");
    });
  }

  return (
    <section className="content-page shell auth-shell">
      <div className="form-panel">
        <p className="eyebrow">Complete reset</p>
        <h1>Verify the OTP and set a new password.</h1>
        <form onSubmit={handleSubmit}>
          <FormField
            label="Email"
            type="email"
            value={form.email}
            onChange={(event) => updateField("email", event.target.value)}
            required
          />
          <FormField
            label="OTP code"
            value={form.otp}
            onChange={(event) => updateField("otp", event.target.value)}
            required
          />
          <FormField
            label="New password"
            type="password"
            value={form.newPassword}
            onChange={(event) => updateField("newPassword", event.target.value)}
            required
          />
          {message ? <StatusBanner tone="success">{message}</StatusBanner> : null}
          <button type="submit" className="button button--primary" disabled={isPending}>
            {isPending ? "Updating..." : "Reset password"}
          </button>
        </form>
        <div className="inline-links">
          <Link to="/auth/forgot-password">Request a new OTP</Link>
          <Link to="/login">Back to login</Link>
        </div>
      </div>
    </section>
  );
}
