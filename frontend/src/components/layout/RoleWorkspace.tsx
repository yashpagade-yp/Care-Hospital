import { NavLink } from "react-router-dom";
import type { ReactNode } from "react";

type WorkspaceLink = {
  to: string;
  label: string;
};

type RoleWorkspaceProps = {
  heading: string;
  summary: string;
  links: WorkspaceLink[];
  actions?: ReactNode;
  children: ReactNode;
};

export function RoleWorkspace({
  heading,
  summary,
  links,
  actions,
  children,
}: RoleWorkspaceProps) {
  return (
    <section className="workspace shell">
      <header className="workspace__hero">
        <div>
          <h1>{heading}</h1>
          <p>{summary}</p>
        </div>
        {actions ? <div className="workspace__actions">{actions}</div> : null}
      </header>

      <div className="workspace__nav" aria-label="Workspace sections">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              `workspace__nav-link${isActive ? " workspace__nav-link--active" : ""}`
            }
          >
            {link.label}
          </NavLink>
        ))}
      </div>

      <div className="workspace__content">{children}</div>
    </section>
  );
}
