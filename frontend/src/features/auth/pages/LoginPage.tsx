import { useState, useTransition } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAppSession } from "@/features/auth/session/AppSessionProvider";

type Phase = "credentials" | "verify-code";

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { sendLoginCode, confirmLoginCode, resendOtp } = useAppSession();

  const [isPending, startTransition] = useTransition();
  const [phase, setPhase] = useState<Phase>("credentials");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");

  const [sentEmail, setSentEmail] = useState("");
  const [error, setError] = useState("");
  const [resendMsg, setResendMsg] = useState("");

  /* ── Phase 1: submit credentials ── */
  function handleSendCode(event: React.FormEvent) {
    event.preventDefault();
    setError("");

    startTransition(async () => {
      try {
        const result = await sendLoginCode({ email, password });
        setSentEmail(result.email);
        setPhase("verify-code");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Invalid email or password.");
      }
    });
  }

  /* ── Phase 2: verify code ── */
  function handleVerifyCode(event: React.FormEvent) {
    event.preventDefault();
    setError("");

    startTransition(async () => {
      try {
        const session = await confirmLoginCode({ email: sentEmail, otp: code });
        const fallback =
          location.state && typeof location.state === "object" && "from" in location.state
            ? String(location.state.from)
            : `/${session.role.toLowerCase()}/dashboard`;
        navigate(fallback);
      } catch (err) {
        setError(err instanceof Error ? err.message : "The code is incorrect. Please try again.");
      }
    });
  }

  async function handleResend() {
    setResendMsg("");
    const result = await resendOtp(sentEmail, "LOGIN_VERIFY");
    setResendMsg(result.message);
  }

  return (
    <div className="login-root">
      {/* ── Left panel ── */}
      <div className="login-left">
        <div className="login-left__logo">
          <div className="login-left__logo-icon">✚</div>
          <span className="login-left__logo-name">MedCare</span>
        </div>

        <div className="login-left__hero">
          <p className="login-left__eyebrow">Hospital Platform</p>
          <h1 className="login-left__heading">
            Your health,<br />in trusted hands.
          </h1>
          <p className="login-left__sub">
            A single secure entry point for doctors, patients, and our medical team.
            We verify your identity at every login to keep your health data safe.
          </p>

          <div className="login-left__features">
            <div className="login-left__feature">
              <div className="login-left__feature-dot" />
              <span>Secure two-step identity check on every login</span>
            </div>
            <div className="login-left__feature">
              <div className="login-left__feature-dot" />
              <span>Role-based workspace for doctors, patients and admins</span>
            </div>
            <div className="login-left__feature">
              <div className="login-left__feature-dot" />
              <span>Your health records stay encrypted and private</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Right panel ── */}
      <div className="login-right">
        <div className="login-card">
          {phase === "credentials" && (
            <div className="login-phase-enter">
              <h2 className="login-card__heading">Welcome back</h2>
              <p className="login-card__sub">
                Enter your email and password. We'll send a short code to confirm it's you.
              </p>

              <form onSubmit={handleSendCode}>
                <div className="login-field">
                  <label htmlFor="login-email">Email address</label>
                  <input
                    id="login-email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@example.com"
                    required
                    autoComplete="email"
                  />
                </div>

                <div className="login-field">
                  <label htmlFor="login-password">Password</label>
                  <input
                    id="login-password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Your password"
                    required
                    autoComplete="current-password"
                  />
                </div>

                {error && <div className="login-error">{error}</div>}

                <button
                  type="submit"
                  className="login-btn login-btn--primary"
                  disabled={isPending}
                >
                  {isPending ? "Sending code…" : "Send verification code →"}
                </button>
              </form>

              <div className="login-links">
                <Link to="/auth/forgot-password">Forgot your password?</Link>
                <Link to="/patient/register">Create a patient account</Link>
              </div>
            </div>
          )}

          {phase === "verify-code" && (
            <div className="login-phase-enter">
              <h2 className="login-card__heading">Check your inbox</h2>
              <p className="login-card__sub">
                Enter the 6-digit code we sent to your email to continue.
              </p>

              {/* Green inbox banner */}
              <div className="login-inbox-banner">
                <span className="login-inbox-banner__icon">✉️</span>
                <p className="login-inbox-banner__text">
                  A verification code was sent to{" "}
                  <span className="login-inbox-banner__email">{sentEmail}</span>.
                  Check your inbox (and spam folder) and enter it below.
                </p>
              </div>

              {/* Dimmed credential summary */}
              <div className="login-field">
                <label>Email address</label>
                <input type="email" value={sentEmail} disabled />
              </div>

              <form onSubmit={handleVerifyCode}>
                <div className="login-field">
                  <label htmlFor="login-code">6-digit verification code</label>
                  <input
                    id="login-code"
                    type="text"
                    inputMode="numeric"
                    value={code}
                    onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                    placeholder="e.g. 482 916"
                    required
                    autoComplete="one-time-code"
                    autoFocus
                  />
                </div>

                {error && <div className="login-error">{error}</div>}
                {resendMsg && (
                  <div style={{ fontSize: "0.85rem", color: "var(--green)", marginBottom: "0.5rem" }}>
                    {resendMsg}
                  </div>
                )}

                <button
                  type="submit"
                  className="login-btn login-btn--primary"
                  disabled={isPending || code.length < 6}
                >
                  {isPending ? "Verifying…" : "Continue to your workspace →"}
                </button>
              </form>

              <div className="login-links">
                <button type="button" onClick={handleResend}>
                  Resend code
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setPhase("credentials");
                    setCode("");
                    setError("");
                    setResendMsg("");
                  }}
                >
                  ← Wrong email?
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
