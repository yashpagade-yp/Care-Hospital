import { Outlet, useLocation } from "react-router-dom";

import { SiteFooter } from "@/components/layout/SiteFooter";
import { SiteHeader } from "@/components/layout/SiteHeader";

const marketingRoutes = new Set(["/"]);
const authFullscreenRoutes = new Set(["/login"]);

export function AppLayout() {
  const location = useLocation();
  const isMarketingRoute = marketingRoutes.has(location.pathname);
  const isAuthFullscreenRoute = authFullscreenRoutes.has(location.pathname);

  return (
    <div className="app-shell">
      <SiteHeader isMarketingRoute={isMarketingRoute} />
      <main className={`app-main${isAuthFullscreenRoute ? " app-main--auth" : ""}`}>
        <Outlet />
      </main>
      {!isAuthFullscreenRoute ? <SiteFooter /> : null}
    </div>
  );
}
