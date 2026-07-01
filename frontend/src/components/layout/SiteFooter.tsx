import { Link } from "react-router-dom";

import { useAppSession } from "@/features/auth/session/AppSessionProvider";

const quickLinks = [
  "Find a doctor",
  "Departments",
  "Insurance support",
  "Patient resources",
];

const professionalLinks = [
  "Doctor invitations",
  "Research and training",
  "Clinical workflow support",
  "Operational dashboards",
];

export function SiteFooter() {
  const { session } = useAppSession();
  const workspacePath = session ? `/${session.role.toLowerCase()}/dashboard` : "/login";

  return (
    <footer className="site-footer">
      <section className="site-footer__banner">
        <div className="shell site-footer__banner-inner">
          <div>
            <p className="eyebrow">Advancing care with purpose</p>
            <h2>Simple workflows for patients, doctors, and hospital operations.</h2>
          </div>
          <Link to={workspacePath} className="button button--primary">
            {session ? "Open workspace" : "Enter platform"}
          </Link>
        </div>
      </section>

      <div className="shell site-footer__grid">
        <div>
          <h3>MedCare</h3>
          <p>
            A single-hospital care platform built for secure onboarding, smooth booking,
            and protected clinical workflows.
          </p>
        </div>

        <div>
          <h4>Patients</h4>
          <ul>
            {quickLinks.map((link) => (
              <li key={link}>{link}</li>
            ))}
          </ul>
        </div>

        <div>
          <h4>Hospital teams</h4>
          <ul>
            {professionalLinks.map((link) => (
              <li key={link}>{link}</li>
            ))}
          </ul>
        </div>

        <div>
          <h4>Phase 1 access</h4>
          <ul>
            <li>Patient self-registration with OTP</li>
            <li>Invite-only doctor onboarding</li>
            <li>Shared login for all three roles</li>
            <li>Operational admin oversight</li>
          </ul>
        </div>
      </div>
    </footer>
  );
}
