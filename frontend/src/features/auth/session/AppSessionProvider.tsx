import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { setPendingDoctorFlow } from "@/features/auth/storage";
import { isApiError } from "@/lib/api/client";
import { authApi } from "@/lib/api/endpoints";
import { createDemoSession, demoAccounts } from "@/lib/mock/data";
import type { OtpPurpose, Session, UserRole } from "@/types/domain";

const SESSION_STORAGE_KEY = "medcare-session";

type SessionContextValue = {
  session: Session | null;
  isAuthenticated: boolean;
  /** Phase 1 — verify credentials and send the 6-digit code to the user's email. */
  sendLoginCode: (payload: { email: string; password: string }) => Promise<{ email: string }>;
  /** Phase 2 — verify the 6-digit code and create the authenticated session. */
  confirmLoginCode: (payload: { email: string; otp: string }) => Promise<Session>;
  logout: () => void;
  resendOtp: (email: string, purpose: OtpPurpose) => Promise<{ message: string }>;
};

const SessionContext = createContext<SessionContextValue | null>(null);

function readStoredSession(): Session | null {
  const raw = globalThis.localStorage?.getItem(SESSION_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as Session;
  } catch {
    return null;
  }
}

export function AppSessionProvider({ children }: { children: ReactNode }) {
  // Read session synchronously on first render so ProtectedRoute never sees null
  // on a page reload (avoids the brief redirect-to-login race condition).
  const [session, setSession] = useState<Session | null>(readStoredSession);

  const value = useMemo<SessionContextValue>(
    () => ({
      session,
      isAuthenticated: Boolean(session),

      async sendLoginCode(payload) {
        // Try the real API first; fall back to demo mode when backend is unavailable.
        try {
          const response = await authApi.login(payload);
          return { email: response.email };
        } catch (error) {
          if (isApiError(error)) {
            if (
              error.status === 403 &&
              error.message.includes("doctor profile setup must be completed")
            ) {
              setPendingDoctorFlow({ email: payload.email.toLowerCase() });
            }
            throw new Error(error.message);
          }

          const demoMatch = demoAccounts.find(
            (account) =>
              account.email === payload.email.toLowerCase() &&
              account.password === payload.password,
          );
          if (!demoMatch) {
            throw new Error("Invalid email or password. Please check your credentials.");
          }
          // In demo mode, we skip the real OTP and return the email to advance to phase 2.
          return { email: payload.email.toLowerCase() };
        }
      },

      async confirmLoginCode(payload) {
        // Try the real verify endpoint; fall back to demo mode.
        try {
          const response = await authApi.verifyLoginOtp(payload);
          const nextSession: Session = {
            token: response.access_token,
            role: response.role,
            user: response.user,
          };
          setSession(nextSession);
          localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(nextSession));
          return nextSession;
        } catch (error) {
          if (isApiError(error)) {
            throw new Error(error.message);
          }

          const demoMatch = demoAccounts.find(
            (account) => account.email === payload.email.toLowerCase(),
          );
          if (!demoMatch) {
            throw new Error("The code you entered is incorrect. Please try again.");
          }
          // In demo mode any code passes — create a demo session.
          const nextSession = createDemoSession(demoMatch.role as UserRole);
          setSession(nextSession);
          localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(nextSession));
          return nextSession;
        }
      },

      logout() {
        setSession(null);
        localStorage.removeItem(SESSION_STORAGE_KEY);
      },

      async resendOtp(email, purpose) {
        try {
          await authApi.resendOtp({ email, purpose });
          return { message: "A new code has been sent to your email." };
        } catch (error) {
          if (isApiError(error)) {
            throw new Error(error.message);
          }
          return { message: "Demo mode — treat this as a successful code resend." };
        }
      },
    }),
    [session],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useAppSession() {
  const value = useContext(SessionContext);
  if (!value) {
    throw new Error("useAppSession must be used inside AppSessionProvider");
  }
  return value;
}
