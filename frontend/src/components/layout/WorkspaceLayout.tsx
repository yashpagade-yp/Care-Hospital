import { Outlet } from "react-router-dom";

/**
 * Bare wrapper for authenticated workspace routes (Admin / Doctor / Patient).
 * No SiteHeader, no SiteFooter — the SidebarLayout inside each page handles
 * its own chrome.
 */
export function WorkspaceLayout() {
  return <Outlet />;
}
