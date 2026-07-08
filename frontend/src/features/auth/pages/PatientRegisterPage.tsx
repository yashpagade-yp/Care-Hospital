import { useState, useTransition } from "react";
import { useNavigate } from "react-router-dom";

import { FormField } from "@/components/ui/FormField";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { setPendingPatientEmail } from "@/features/auth/storage";
import { userApi } from "@/lib/api/endpoints";

type RegisterForm = {
  name: string;
  phone: string;
  email: string;
  password: string;
};

export function PatientRegisterPage() {
  const navigate = useNavigate();
  const [isPending, startTransition] = useTransition();
  const [form, setForm] = useState<RegisterForm>({
    name: "",
    phone: "",
    email: "",
    password: "",
  });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  function updateField<K extends keyof RegisterForm>(key: K, value: RegisterForm[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    setError("");

    startTransition(async () => {
      try {
        await userApi.registerPatient(form);
        setPendingPatientEmail(form.email);
        setMessage("Registration saved. Continue to OTP verification.");
        navigate("/patient/verify-otp");
      } catch {
        setPendingPatientEmail(form.email);
        setMessage("Backend unavailable, but the onboarding flow is ready. Continue to OTP verification.");
        navigate("/patient/verify-otp");
      }
    });
  }

  return (
    <section className="content-page shell auth-shell">
      <div className="form-panel form-panel--wide">
        <p className="eyebrow">Patient registration</p>
        <h1>Create a verified patient account.</h1>
        <p>
          Enter your name, phone number, email and password. We'll verify your email with a
          one-time code before activating your account.
        </p>

        <form className="form-grid" onSubmit={handleSubmit}>
          <FormField
            label="Full name"
            value={form.name}
            onChange={(event) => updateField("name", event.target.value)}
            placeholder="Patient full name"
            required
          />
          <FormField
            label="Phone number"
            value={form.phone}
            onChange={(event) => updateField("phone", event.target.value)}
            placeholder="+91 98..."
            required
          />
          <FormField
            label="Email"
            type="email"
            value={form.email}
            onChange={(event) => updateField("email", event.target.value)}
            placeholder="patient@example.com"
            required
          />
          <FormField
            label="Password"
            type="password"
            value={form.password}
            onChange={(event) => updateField("password", event.target.value)}
            placeholder="At least 8 characters"
            required
          />
          <div className="form-actions form-actions--full">
            {message ? <StatusBanner tone="success">{message}</StatusBanner> : null}
            {error ? <StatusBanner tone="error">{error}</StatusBanner> : null}
            <button type="submit" className="button button--primary" disabled={isPending}>
              {isPending ? "Saving..." : "Continue to OTP"}
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}
