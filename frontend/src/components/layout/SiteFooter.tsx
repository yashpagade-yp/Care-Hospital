import { Link } from "react-router-dom";

import { useAppSession } from "@/features/auth/session/AppSessionProvider";

export function SiteFooter() {
  const { session } = useAppSession();
  const workspacePath = session ? `/${session.role.toLowerCase()}/dashboard` : "/login";

  return (
    <footer className="site-footer">
      <section className="site-footer__banner">
        <div className="shell site-footer__banner-inner">
          <div>
            <p className="eyebrow">GoodCare Hospital</p>
            <h2>Care that feels modern, responsive, and deeply reassuring for every family.</h2>
          </div>
          <Link to={workspacePath} className="button button--primary">
            {session ? "Open workspace" : "Open login"}
          </Link>
        </div>
      </section>

      <div className="shell site-footer__grid">
        <div>
          <h3>GoodCare Hospital</h3>
          <p>
            24 Green Avenue, Lakeview Road, Bengaluru 560048. A warm, premium hospital
            experience with specialist care, emergency response, and compassionate support.
          </p>
        </div>

        <div>
          <h4>Helplines</h4>
          <ul>
            <li>Emergency: +91 1800 300 9111</li>
            <li>Ambulance: +91 1800 300 9222</li>
            <li>Appointments: +91 1800 300 9333</li>
            <li>Women's care: +91 1800 300 9444</li>
          </ul>
        </div>

        <div>
          <h4>Hospital info</h4>
          <ul>
            <li>Patients treated: 52,000+</li>
            <li>Average reviews: 4.9 / 5</li>
            <li>Specialist departments: 18+</li>
            <li>Ambulance support: 24/7</li>
          </ul>
        </div>

        <div>
          <h4>Quick access</h4>
          <ul>
            <li>
              <Link to="/login">Patient login</Link>
            </li>
            <li>
              <Link to="/patient/register">New registration</Link>
            </li>
            <li>Emergency desk open all day</li>
            <li>Healthy living support and follow-up guidance</li>
          </ul>
        </div>
      </div>
    </footer>
  );
}
