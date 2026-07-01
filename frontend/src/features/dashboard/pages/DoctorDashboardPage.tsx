import { RoleWorkspace } from "@/components/layout/RoleWorkspace";
import { EmptyState } from "@/components/ui/EmptyState";
import { StatCard } from "@/components/ui/StatCard";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { useAppSession } from "@/features/auth/session/AppSessionProvider";
import { doctorWorkspaceLinks } from "@/features/shared/workspace-links";
import { loadDoctorDashboard } from "@/features/shared/resource-loaders";
import { useAsyncResource } from "@/hooks/useAsyncResource";
import { formatDateTime } from "@/lib/utils/format";

export function DoctorDashboardPage() {
  const { session } = useAppSession();
  const { data, isLoading, error } = useAsyncResource(loadDoctorDashboard, []);

  return (
    <RoleWorkspace
      heading="Doctor dashboard"
      summary="Track upcoming appointments, review history, and move through the consultation workflow with clarity."
      links={doctorWorkspaceLinks}
    >
      {error ? <StatusBanner tone="warning">{error}</StatusBanner> : null}
      {isLoading || !data ? (
        <div className="loading-panel">Loading doctor workspace...</div>
      ) : (
        <>
          <div className="stats-grid">
            <StatCard label="Upcoming appointments" value={data.upcoming_appointments.length} />
            <StatCard label="History items" value={data.appointment_history.length} />
            <StatCard label="Specialty" value={data.profile.specialty ?? "General"} />
            <StatCard label="Signed in as" value={session?.user.name ?? data.profile.name} />
          </div>

          <div className="content-grid">
            <section className="surface-card">
              <div className="surface-card__header">
                <div>
                  <p className="eyebrow">Upcoming appointments</p>
                  <h2>Today's operational focus</h2>
                </div>
              </div>
              {data.upcoming_appointments.length ? (
                <div className="stack-list">
                  {data.upcoming_appointments.map((appointment) => (
                    <article key={appointment.id} className="stack-list__item">
                      <div>
                        <h3>{formatDateTime(appointment.date_time)}</h3>
                        <p>Patient ID: {appointment.patient_id}</p>
                      </div>
                      <strong>{appointment.status}</strong>
                    </article>
                  ))}
                </div>
              ) : (
                <EmptyState
                  title="No upcoming appointments"
                  description="New bookings will appear here when patients confirm appointments."
                />
              )}
            </section>

            <section className="surface-card">
              <div className="surface-card__header">
                <div>
                  <p className="eyebrow">Professional profile</p>
                  <h2>Doctor summary</h2>
                </div>
              </div>
              <dl className="detail-list">
                <div>
                  <dt>Qualification</dt>
                  <dd>{data.profile.qualification ?? "Not set"}</dd>
                </div>
                <div>
                  <dt>Specialty</dt>
                  <dd>{data.profile.specialty ?? "Not set"}</dd>
                </div>
                <div>
                  <dt>Experience</dt>
                  <dd>{data.profile.experience_years ?? 0} years</dd>
                </div>
              </dl>
            </section>
          </div>
        </>
      )}
    </RoleWorkspace>
  );
}
