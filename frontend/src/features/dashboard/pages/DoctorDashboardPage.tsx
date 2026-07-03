import { SidebarLayout } from "@/components/layout/SidebarLayout";
import { useAppSession } from "@/features/auth/session/AppSessionProvider";
import { loadDoctorDashboard } from "@/features/shared/resource-loaders";
import { useAsyncResource } from "@/hooks/useAsyncResource";
import { formatDateTime } from "@/lib/utils/format";

const DOCTOR_NAV = [
  {
    title: "Platform",
    links: [{ label: "My Dashboard", to: "/doctor/dashboard" }],
  },
  {
    title: "Workspace",
    links: [
      { label: "Appointments", to: "/doctor/appointments" },
      { label: "My Availability", to: "/doctor/availability" },
      { label: "Prescriptions", to: "/doctor/prescriptions" },
    ],
  },
];

export { DOCTOR_NAV };

export function DoctorDashboardPage() {
  const { session } = useAppSession();
  const { data, isLoading } = useAsyncResource(loadDoctorDashboard, []);

  const doctorName = session?.user.name ?? "Doctor";

  return (
    <SidebarLayout sections={DOCTOR_NAV}>
      <div className="ws-page-header">
        <p className="ws-page-eyebrow">Doctor Workspace</p>
        <h1 className="ws-page-heading">Welcome, Dr. {doctorName.split(" ").pop()} 👨‍⚕️</h1>
        <p className="ws-page-sub">
          Your upcoming schedule, patient appointments, and professional details — all in one place.
        </p>
      </div>

      <div className="ws-stats-row">
        <div className="ws-stat-card">
          <span className="ws-stat-card__value">{data?.upcoming_appointments?.length ?? "—"}</span>
          <span className="ws-stat-card__label">Upcoming appointments</span>
        </div>
        <div className="ws-stat-card">
          <span className="ws-stat-card__value">{data?.appointment_history?.length ?? "—"}</span>
          <span className="ws-stat-card__label">Completed consultations</span>
        </div>
        <div className="ws-stat-card">
          <span className="ws-stat-card__value">{data?.profile?.specialty ?? "—"}</span>
          <span className="ws-stat-card__label">Specialty</span>
        </div>
        <div className="ws-stat-card">
          <span className="ws-stat-card__value">
            {data?.profile?.experience_years != null
              ? `${data.profile.experience_years} yrs`
              : "—"}
          </span>
          <span className="ws-stat-card__label">Experience</span>
        </div>
      </div>

      {isLoading && <div className="ws-loading">Loading your workspace…</div>}

      {data && (
        <div className="ws-grid ws-grid--2">
          {/* Upcoming appointments */}
          <div className="ws-card">
            <div className="ws-card__header">
              <h2 className="ws-card__title">Upcoming appointments</h2>
            </div>
            {data.upcoming_appointments.length === 0 ? (
              <div className="ws-empty">
                <div className="ws-empty__icon">📅</div>
                <p className="ws-empty__title">No upcoming appointments</p>
                <p className="ws-empty__sub">New bookings will appear here once confirmed.</p>
              </div>
            ) : (
              <div className="ws-list">
                {data.upcoming_appointments.slice(0, 6).map((apt) => (
                  <div key={apt.id} className="ws-list-item">
                    <div className="ws-list-item__main">
                      <span className="ws-list-item__title">
                        {formatDateTime(apt.date_time)}
                      </span>
                      <span className="ws-list-item__sub">Patient consultation</span>
                    </div>
                    <span className={`ws-badge ws-badge--${apt.status.toLowerCase()}`}>
                      {apt.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Professional profile */}
          <div className="ws-card">
            <div className="ws-card__header">
              <h2 className="ws-card__title">Professional profile</h2>
            </div>
            <div className="ws-card__body">
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <tbody>
                  {[
                    ["Name", data.profile.name],
                    ["Email", data.profile.email],
                    ["Qualification", data.profile.qualification ?? "Not set"],
                    ["Specialty", data.profile.specialty ?? "Not set"],
                    ["Experience", data.profile.experience_years != null
                      ? `${data.profile.experience_years} years`
                      : "Not set"],
                  ].map(([label, value]) => (
                    <tr key={label}>
                      <td
                        style={{
                          padding: "0.6rem 0",
                          color: "var(--text-soft)",
                          fontSize: "0.85rem",
                          width: "40%",
                          fontWeight: 600,
                          borderBottom: "1px solid var(--line)",
                        }}
                      >
                        {label}
                      </td>
                      <td
                        style={{
                          padding: "0.6rem 0",
                          fontSize: "0.9rem",
                          borderBottom: "1px solid var(--line)",
                          fontWeight: 600,
                          color: "var(--text)",
                        }}
                      >
                        {value}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </SidebarLayout>
  );
}
