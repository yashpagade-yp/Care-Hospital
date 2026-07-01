import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAppSession } from "@/features/auth/session/AppSessionProvider";
import type { UserRole } from "@/types/domain";

export function ProtectedRoute({ allowedRoles }: { allowedRoles: UserRole[] }) {
  const { isAuthenticated, session } = useAppSession();
  const location = useLocation();

  if (!isAuthenticated || !session) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (!allowedRoles.includes(session.role)) {
    return <Navigate to={`/${session.role.toLowerCase()}/dashboard`} replace />;
  }

  return <Outlet />;
}
