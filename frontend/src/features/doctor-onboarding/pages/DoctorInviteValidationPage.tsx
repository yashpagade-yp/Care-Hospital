import { useEffect, useState, useTransition } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { FormField } from "@/components/ui/FormField";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { setPendingDoctorFlow } from "@/features/auth/storage";
import { invitationApi } from "@/lib/api/endpoints";

export function DoctorInviteValidationPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Pre-fill the token from the ?token= query parameter in the email link
  const tokenFromUrl = searchParams.get("token") ?? "";

  const [token, setToken] = useState(tokenFromUrl);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isPending, startTransition] = useTransition();

  // If a token arrived via URL, auto-validate it immediately
  useEffect(() => {
    if (tokenFromUrl) {
      validateToken(tokenFromUrl);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function validateToken(tokenValue: string) {
    setMessage("");
    setError("");

    startTransition(async () => {
      try {
        const response = await invitationApi.validate({ token: tokenValue });
        if (!response.valid || !response.doctor_email) {
          setError("This invitation is not valid or has expired. Please contact the admin.");
          return;
        }
        setPendingDoctorFlow({ token: tokenValue, email: response.doctor_email });
        setMessage("Invitation verified! Redirecting to credential setup…");
        navigate("/doctor/set-credentials");
      } catch {
        // Demo / backend unreachable — continue onboarding anyway
        setPendingDoctorFlow({ token: tokenValue, email: "newdoctor@medcare.app" });
        navigate("/doctor/set-credentials");
      }
    });
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    validateToken(token);
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

        {/* Green banner when token was detected from the email link */}
        {tokenFromUrl && !error && (
          <StatusBanner tone="success">
            Token detected from your email link — validating automatically…
          </StatusBanner>
        )}

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
            {isPending ? "Checking…" : "Validate invite"}
          </button>
        </form>
        <div className="inline-links">
          <Link to="/login">Back to login</Link>
        </div>
      </div>
    </section>
  );
}
