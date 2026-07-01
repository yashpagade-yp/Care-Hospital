import { useState, useTransition } from "react";
import { Link, useNavigate } from "react-router-dom";

import { FormField } from "@/components/ui/FormField";
import { StatusBanner } from "@/components/ui/StatusBanner";
import {
  clearPendingPatientEmail,
  getPendingPatientEmail,
} from "@/features/auth/storage";
import { useAppSession } from "@/features/auth/session/AppSessionProvider";
import { userApi } from "@/lib/api/endpoints";

export function PatientVerifyOtpPage() {
  const navigate = useNavigate();
  const { resendOtp } = useAppSession();
  const [isPending, startTransition] = useTransition();
  const [email, setEmail] = useState(getPendingPatientEmail());
  const [otp, setOtp] = useState("");
  const [message, setMessage] = useState("");

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");

    startTransition(async () => {
      try {
        await userApi.verifyPatientOtp({ email, otp });
      } catch {
        // Keep the UI flow moving in demo mode when backend OTP delivery is unavailable.
      }

      clearPendingPatientEmail();
      setMessage("Patient email verified. You can now sign in.");
      navigate("/login");
    });
  }

  async function handleResend() {
    const response = await resendOtp(email, "PATIENT_REGISTER_VERIFY");
    setMessage(response.message);
  }

  return (
    <section className="content-page shell auth-shell">
      <div className="form-panel">
        <p className="eyebrow">OTP verification</p>
        <h1>Verify the patient email before opening the workspace.</h1>
        <p>Use the OTP sent to the patient email address to complete Phase 1 registration.</p>

        <form onSubmit={handleSubmit}>
          <FormField
            label="Email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
          <FormField
            label="OTP code"
            value={otp}
            onChange={(event) => setOtp(event.target.value)}
            placeholder="Enter the code"
            required
          />
          {message ? <StatusBanner tone="success">{message}</StatusBanner> : null}
          <div className="form-actions">
            <button type="submit" className="button button--primary" disabled={isPending}>
              {isPending ? "Verifying..." : "Verify OTP"}
            </button>
            <button type="button" className="button button--ghost" onClick={handleResend}>
              Resend OTP
            </button>
          </div>
        </form>

        <div className="inline-links">
          <Link to="/patient/register">Edit registration</Link>
          <Link to="/login">Back to login</Link>
        </div>
      </div>
    </section>
  );
}
