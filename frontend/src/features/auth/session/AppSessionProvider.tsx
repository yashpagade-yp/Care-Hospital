import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { authApi } from "@/lib/api/endpoints";
import { createDemoSession, demoAccounts } from "@/lib/mock/data";
import type { OtpPurpose, Session, UserRole } from "@/types/domain";

const SESSION_STORAGE_KEY = "medcare-session";

type SessionContextValue = {
  session: Session | null;
  isAuthenticated: boolean;
  login: (payload: { email: string; password: string }) => Promise<Session>;
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
  const [session, setSession] = useState<Session | null>(null);

  useEffect(() => {
    setSession(readStoredSession());
  }, []);

  const value = useMemo<SessionContextValue>(
    () => ({
      session,
      isAuthenticated: Boolean(session),
      async login(payload) {
        try {
          const response = await authApi.login(payload);
          const nextSession: Session = {
            token: response.access_token,
            role: response.role,
            user: response.user,
          };
          setSession(nextSession);
          localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(nextSession));
          return nextSession;
        } catch (error) {
          const demoMatch = demoAccounts.find(
            (account) =>
              account.email === payload.email.toLowerCase() &&
              account.password === payload.password,
          );

          if (!demoMatch) {
            throw error;
          }

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
          return { message: "OTP sent successfully." };
        } catch {
          return { message: "Demo mode active. Treat this as an OTP resend success." };
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
