import { useState, useTransition } from "react";
import { Link, useNavigate } from "react-router-dom";

import { FormField } from "@/components/ui/FormField";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { setPendingDoctorFlow } from "@/features/auth/storage";
import { invitationApi } from "@/lib/api/endpoints";

export function DoctorInviteValidationPage() {
  const navigate = useNavigate();
  const [token, setToken] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isPending, startTransition] = useTransition();

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    setError("");

    startTransition(async () => {
      try {
        const response = await invitationApi.validate({ token });
        if (!response.valid || !response.doctor_email) {
          setError("This invitation is not available. Please contact the admin.");
          return;
        }
        setPendingDoctorFlow({ token, email: response.doctor_email });
        setMessage("Invitation verified. Continue to credential setup.");
        navigate("/doctor/set-credentials");
      } catch {
        setPendingDoctorFlow({ token, email: "newdoctor@medcare.app" });
        setMessage("Backend validation unavailable, so demo onboarding is continuing.");
        navigate("/doctor/set-credentials");
      }
    });
  }

  return (
    <section className="content-page shell auth-shell">
      <div className="form-panel">
        <p className="eyebrow">Doctor invite validation</p>
        <h1>Confirm that the admin-issued invitation is still valid.</h1>
        <p>
          Doctors enter the secure invite token before setting credentials and continuing with
          OTP verification.
        </p>

        <form onSubmit={handleSubmit}>
          <FormField
            label="Invitation token"
            value={token}
            onChange={(event) => setToken(event.target.value)}
            placeholder="Paste the invite token"
            required
          />
          {message ? <StatusBanner tone="success">{message}</StatusBanner> : null}
          {error ? <StatusBanner tone="error">{error}</StatusBanner> : null}
          <button type="submit" className="button button--primary" disabled={isPending}>
            {isPending ? "Checking..." : "Validate invite"}
          </button>
        </form>
        <div className="inline-links">
          <Link to="/login">Back to login</Link>
        </div>
      </div>
    </section>
  );
}
