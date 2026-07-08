import { Link, NavLink } from "react-router-dom";

import { useAppSession } from "@/features/auth/session/AppSessionProvider";

type SiteHeaderProps = {
  isMarketingRoute: boolean;
};

const navItems = [
  { to: "/login", label: "Login" },
  { to: "/patient/register", label: "Registration" },
];

export function SiteHeader({ isMarketingRoute }: SiteHeaderProps) {
  const { isAuthenticated, session, logout } = useAppSession();
  const workspacePath = session ? `/${session.role.toLowerCase()}/dashboard` : "/login";

  return (
    <header className={`site-header ${isMarketingRoute ? "site-header--glass" : ""}`}>
      <div className="shell site-header__inner">
        <Link to="/" className="brand-mark" aria-label="MedCare home">
          <span className="brand-mark__icon">M</span>
          <span>
            <strong>MedCare</strong>
            <small>Hospital Platform</small>
          </span>
        </Link>

        <nav className="site-nav" aria-label="Primary">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `site-nav__link${isActive ? " site-nav__link--active" : ""}`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="site-header__cta">
          <span className="site-header__helpline">24/7 Helpline: +91 1800 300 9111</span>
          {isAuthenticated && session ? (
            <>
              <Link to={workspacePath} className="button button--primary button--compact">
                {session.role.toLowerCase()} workspace
              </Link>
              <button
                type="button"
                className="button button--ghost button--compact"
                onClick={logout}
              >
                Sign out
              </button>
            </>
          ) : (
            <Link to="/patient/register" className="button button--primary button--compact">
              Registration
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
