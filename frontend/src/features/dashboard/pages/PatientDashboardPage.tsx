import { Link } from "react-router-dom";

import { RoleWorkspace } from "@/components/layout/RoleWorkspace";
import { EmptyState } from "@/components/ui/EmptyState";
import { StatCard } from "@/components/ui/StatCard";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { useAppSession } from "@/features/auth/session/AppSessionProvider";
import { patientWorkspaceLinks } from "@/features/shared/workspace-links";
import { loadPatientDashboard } from "@/features/shared/resource-loaders";
import { useAsyncResource } from "@/hooks/useAsyncResource";
import { formatDateTime } from "@/lib/utils/format";

export function PatientDashboardPage() {
  const { session } = useAppSession();
  const { data, isLoading, error } = useAsyncResource(loadPatientDashboard, []);

  return (
    <RoleWorkspace
      heading="Patient dashboard"
      summary="Discover doctors, review upcoming care, and manage your appointment journey from one workspace."
      links={patientWorkspaceLinks}
      actions={<Link to="/patient/book" className="button button--primary">Book appointment</Link>}
    >
      {error ? <StatusBanner tone="warning">{error}</StatusBanner> : null}
      {isLoading || !data ? (
        <div className="loading-panel">Loading patient workspace...</div>
      ) : (
        <>
          <div className="stats-grid">
            <StatCard label="Upcoming visits" value={data.upcoming_appointments.length} />
            <StatCard label="Previous appointments" value={data.appointment_history.length} />
            <StatCard label="Available doctors" value={data.doctor_cards.length} />
            <StatCard label="Signed in as" value={session?.user.name ?? data.profile.name} />
          </div>

          <div className="content-grid">
            <section className="surface-card">
              <div className="surface-card__header">
                <div>
                  <p className="eyebrow">Doctor discovery</p>
                  <h2>Recommended doctors</h2>
                </div>
              </div>
              <div className="doctor-card-grid">
                {data.doctor_cards.map((doctor) => (
                  <article key={doctor.doctor_id} className="doctor-card">
                    <div className="doctor-card__badge">{doctor.specialty?.slice(0, 2) ?? "DR"}</div>
                    <div>
                      <h3>{doctor.name}</h3>
                      <p>{doctor.specialty ?? "General care"}</p>
                    </div>
                    <dl>
                      <div>
                        <dt>Experience</dt>
                        <dd>{doctor.experience_years ?? 0} years</dd>
                      </div>
                      <div>
                        <dt>Rating</dt>
                        <dd>{doctor.rating ?? "N/A"}</dd>
                      </div>
                    </dl>
                    <Link to="/patient/book" className="button button--ghost">
                      Book now
                    </Link>
                  </article>
                ))}
              </div>
            </section>

            <section className="surface-card">
              <div className="surface-card__header">
                <div>
                  <p className="eyebrow">Upcoming appointments</p>
                  <h2>Next scheduled visits</h2>
                </div>
                <Link to="/patient/appointments">View all</Link>
              </div>
              {data.upcoming_appointments.length ? (
                <div className="stack-list">
                  {data.upcoming_appointments.map((appointment) => (
                    <article key={appointment.id} className="stack-list__item">
                      <div>
                        <h3>{formatDateTime(appointment.date_time)}</h3>
                        <p>Status: {appointment.status}</p>
                      </div>
                      <strong>Rs. {appointment.fee}</strong>
                    </article>
                  ))}
                </div>
              ) : (
                <EmptyState
                  title="No upcoming visits"
                  description="Book a consultation to start your care journey."
                />
              )}
            </section>
          </div>
        </>
      )}
    </RoleWorkspace>
  );
}
