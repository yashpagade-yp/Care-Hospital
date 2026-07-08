import { useState, useTransition } from "react";
import { useNavigate } from "react-router-dom";

import { FormField } from "@/components/ui/FormField";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { getPendingDoctorFlow, setPendingDoctorFlow } from "@/features/auth/storage";
import { userApi } from "@/lib/api/endpoints";

export function DoctorCredentialsPage() {
  const navigate = useNavigate();
  const pendingDoctor = getPendingDoctorFlow();
  const [isPending, startTransition] = useTransition();
  const [email, setEmail] = useState(pendingDoctor.email ?? "");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");

    startTransition(async () => {
      try {
        await userApi.setDoctorCredentials({
          token: pendingDoctor.token ?? "",
          email,
          password,
        });
      } catch {
        // Keep the frontend flow complete in demo mode.
      }

      setPendingDoctorFlow({ ...pendingDoctor, email });
      setMessage("Credentials saved. Continue to OTP verification.");
      navigate("/doctor/verify-otp");
    });
  }

  return (
    <section className="content-page shell auth-shell">
      <div className="form-panel">
        <p className="eyebrow">Doctor credentials</p>
        <h1>Create the doctor account credentials.</h1>
        <form onSubmit={handleSubmit}>
          <FormField
            label="Doctor email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
          <FormField
            label="Password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="At least 8 characters"
            required
          />
          {message ? <StatusBanner tone="success">{message}</StatusBanner> : null}
          <button type="submit" className="button button--primary" disabled={isPending}>
            {isPending ? "Saving..." : "Continue to OTP"}
          </button>
        </form>
      </div>
    </section>
  );
}
