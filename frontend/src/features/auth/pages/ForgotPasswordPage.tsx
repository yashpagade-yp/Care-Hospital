import { useState, useTransition } from "react";
import { Link, useNavigate } from "react-router-dom";

import { FormField } from "@/components/ui/FormField";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { authApi } from "@/lib/api/endpoints";

export function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [isPending, startTransition] = useTransition();
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");

    startTransition(async () => {
      try {
        await authApi.forgotPassword({ email });
      } catch {
        // Keep the reset path usable in demo mode.
      }
      setMessage("If the email is registered, the password reset OTP flow has started.");
      navigate("/auth/reset-password", { state: { email } });
    });
  }

  return (
    <section className="content-page shell auth-shell">
      <div className="form-panel">
        <p className="eyebrow">Password reset</p>
        <h1>Start the password reset flow.</h1>
        <p>
          This screen follows the backend rule that the system must not reveal whether the
          email exists.
        </p>
        <form onSubmit={handleSubmit}>
          <FormField
            label="Email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="Enter your account email"
            required
          />
          {message ? <StatusBanner tone="success">{message}</StatusBanner> : null}
          <button type="submit" className="button button--primary" disabled={isPending}>
            {isPending ? "Sending..." : "Send reset OTP"}
          </button>
        </form>
        <div className="inline-links">
          <Link to="/auth/reset-password">Already have the OTP?</Link>
          <Link to="/login">Back to login</Link>
        </div>
      </div>
    </section>
  );
}
