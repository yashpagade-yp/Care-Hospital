import { Outlet, useLocation } from "react-router-dom";

import { SiteFooter } from "@/components/layout/SiteFooter";
import { SiteHeader } from "@/components/layout/SiteHeader";

const marketingRoutes = new Set(["/"]);

export function AppLayout() {
  const location = useLocation();
  const isMarketingRoute = marketingRoutes.has(location.pathname);

  return (
    <div className="app-shell">
      <SiteHeader isMarketingRoute={isMarketingRoute} />
      <main>
        <Outlet />
      </main>
      <SiteFooter />
    </div>
  );
}
