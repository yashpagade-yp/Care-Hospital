import { NavLink, useNavigate } from "react-router-dom";
import { useAppSession } from "@/features/auth/session/AppSessionProvider";
import type { ReactNode } from "react";

export type SidebarLink = {
  label: string;
  to: string;
};

export type SidebarSection = {
  title: string;
  links: SidebarLink[];
};

type SidebarLayoutProps = {
  sections: SidebarSection[];
  children: ReactNode;
};

function getInitials(name: string): string {
  return name
    .split(" ")
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

export function SidebarLayout({ sections, children }: SidebarLayoutProps) {
  const { session, logout } = useAppSession();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="ws-layout">
      {/* ── Sidebar ── */}
      <aside className="ws-sidebar">
        <div className="ws-sidebar__brand">
          <div className="ws-sidebar__logo">
            <span>✚</span>
          </div>
          <div>
            <strong className="ws-sidebar__brand-name">MedCare</strong>
            <span className="ws-sidebar__brand-sub">Hospital Platform</span>
          </div>
        </div>

        <nav className="ws-sidebar__nav">
          {sections.map((section) => (
            <div key={section.title} className="ws-sidebar__section">
              <p className="ws-sidebar__section-label">{section.title}</p>
              {section.links.map((link) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  className={({ isActive }) =>
                    `ws-sidebar__link${isActive ? " ws-sidebar__link--active" : ""}`
                  }
                >
                  {link.label}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        <div className="ws-sidebar__footer">
          {session && (
            <>
              <div className="ws-sidebar__user">
                <div className="ws-sidebar__avatar">
                  {getInitials(session.user.name)}
                </div>
                <div className="ws-sidebar__user-info">
                  <strong className="ws-sidebar__user-name">{session.user.name}</strong>
                  <span className="ws-sidebar__user-email">{session.user.email}</span>
                </div>
              </div>
              <button
                type="button"
                className="ws-sidebar__signout"
                onClick={handleLogout}
              >
                Sign out
              </button>
            </>
          )}
        </div>
      </aside>

      {/* ── Main content ── */}
      <main className="ws-main">
        {/* Refresh button — top right corner */}
        <button
          type="button"
          className="ws-refresh-btn"
          onClick={() => window.location.reload()}
          title="Refresh page"
          aria-label="Refresh"
        >
          ↺ Refresh
        </button>
        {children}
      </main>
    </div>
  );
}
