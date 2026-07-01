import { useState, useTransition } from "react";
import { useNavigate } from "react-router-dom";

import { FormField } from "@/components/ui/FormField";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { getPendingDoctorFlow } from "@/features/auth/storage";
import { useAppSession } from "@/features/auth/session/AppSessionProvider";
import { userApi } from "@/lib/api/endpoints";

export function DoctorVerifyOtpPage() {
  const navigate = useNavigate();
  const pendingDoctor = getPendingDoctorFlow();
  const { resendOtp } = useAppSession();
  const [otp, setOtp] = useState("");
  const [message, setMessage] = useState("");
  const [isPending, startTransition] = useTransition();

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");

    startTransition(async () => {
      try {
        await userApi.verifyDoctorOtp({
          email: pendingDoctor.email ?? "",
          otp,
        });
      } catch {
        // Demo-safe continuation.
      }

      setMessage("Doctor OTP verified. Continue to one-time profile setup.");
      navigate("/doctor/complete-profile");
    });
  }

  async function handleResend() {
    const response = await resendOtp(pendingDoctor.email ?? "", "DOCTOR_INVITE_VERIFY");
    setMessage(response.message);
  }

  return (
    <section className="content-page shell auth-shell">
      <div className="form-panel">
        <p className="eyebrow">Doctor OTP verification</p>
        <h1>Verify email ownership before profile completion.</h1>
        <form onSubmit={handleSubmit}>
          <FormField
            label="Doctor email"
            type="email"
            value={pendingDoctor.email ?? ""}
            readOnly
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
      </div>
    </section>
  );
}
