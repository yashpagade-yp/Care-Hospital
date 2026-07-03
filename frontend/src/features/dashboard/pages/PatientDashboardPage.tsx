import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { SidebarLayout } from "@/components/layout/SidebarLayout";
import { useAppSession } from "@/features/auth/session/AppSessionProvider";
import { loadPatientDashboard } from "@/features/shared/resource-loaders";
import { useAsyncResource } from "@/hooks/useAsyncResource";
import { formatDateTime } from "@/lib/utils/format";
import { availabilityApi } from "@/lib/api/endpoints";
import type { DoctorAvailability } from "@/types/domain";

// Derive the next upcoming slot label from a doctor's weekly availabilities
function getNextSlotLabel(avails: DoctorAvailability[]): string | null {
  const dayMap: Record<string, number> = {
    MONDAY: 1, TUESDAY: 2, WEDNESDAY: 3, THURSDAY: 4,
    FRIDAY: 5, SATURDAY: 6, SUNDAY: 0,
  };
  const now = new Date();
  for (let daysAhead = 0; daysAhead <= 14; daysAhead++) {
    const date = new Date(now);
    date.setDate(now.getDate() + daysAhead);
    const dayNum = date.getDay();
    for (const avail of avails) {
      if (avail.availability_type !== "RECURRING" || !avail.day_of_week) continue;
      if (dayMap[avail.day_of_week] !== dayNum) continue;
      const [h, m] = avail.start_time.split(":").map(Number);
      const slotDate = new Date(date);
      slotDate.setHours(h, m, 0, 0);
      if (slotDate <= now) continue;
      const label = daysAhead === 0 ? "Today" : daysAhead === 1 ? "Tomorrow"
        : date.toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short" });
      return `${label} · ${avail.start_time}`;
    }
  }
  return null;
}

const PATIENT_NAV = [
  {
    title: "Platform",
    links: [{ label: "My Dashboard", to: "/patient/dashboard" }],
  },
  {
    title: "Workspace",
    links: [
      { label: "My Appointments", to: "/patient/appointments" },
      { label: "My Prescriptions", to: "/patient/prescriptions" },
      { label: "My Reviews", to: "/patient/reviews" },
      { label: "Book Appointment", to: "/patient/book" },
    ],
  },
];

export { PATIENT_NAV };

export function PatientDashboardPage() {
  const { session } = useAppSession();
  const { data, isLoading } = useAsyncResource(loadPatientDashboard, []);
  const [doctorSlots, setDoctorSlots] = useState<Record<string, string | null>>({});

  // Load availability for each doctor and compute next slot label
  useEffect(() => {
    if (!data?.doctor_cards) return;
    for (const doc of data.doctor_cards) {
      availabilityApi.listDoctorAvailability(doc.doctor_id)
        .then((res) => {
          const nextSlot = getNextSlotLabel(res.items);
          setDoctorSlots((prev) => ({ ...prev, [doc.doctor_id]: nextSlot }));
        })
        .catch(() => {
          setDoctorSlots((prev) => ({ ...prev, [doc.doctor_id]: null }));
        });
    }
  }, [data?.doctor_cards]);

  const patientName = session?.user.name ?? "Patient";

  return (
    <SidebarLayout sections={PATIENT_NAV}>
      <div className="ws-page-header">
        <p className="ws-page-eyebrow">Patient Workspace</p>
        <h1 className="ws-page-heading">Hello, {patientName.split(" ")[0]} 🌿</h1>
        <p className="ws-page-sub">
          Your health journey at a glance — upcoming visits, recommended doctors, and your care history.
        </p>
      </div>

      {/* Header action */}
      <div style={{ marginBottom: "1.5rem" }}>
        <Link to="/patient/book" className="ws-btn ws-btn--primary">
          Book a new appointment
        </Link>
      </div>

      <div className="ws-stats-row">
        <div className="ws-stat-card">
          <span className="ws-stat-card__value">{data?.upcoming_appointments?.length ?? "—"}</span>
          <span className="ws-stat-card__label">Upcoming visits</span>
          <span className="ws-stat-card__accent">scheduled</span>
        </div>
        <div className="ws-stat-card">
          <span className="ws-stat-card__value">{data?.appointment_history?.length ?? "—"}</span>
          <span className="ws-stat-card__label">Past consultations</span>
          <span className="ws-stat-card__accent">completed</span>
        </div>
        <div className="ws-stat-card">
          <span className="ws-stat-card__value">{data?.doctor_cards?.length ?? "—"}</span>
          <span className="ws-stat-card__label">Available doctors</span>
          <span className="ws-stat-card__accent">on MedCare</span>
        </div>
        <div className="ws-stat-card">
          <span className="ws-stat-card__value">✓</span>
          <span className="ws-stat-card__label">Account verified</span>
          <span className="ws-stat-card__accent">email confirmed</span>
        </div>
      </div>

      {isLoading && <div className="ws-loading">Loading your health workspace…</div>}

      {data && (
        <div className="ws-grid ws-grid--2">
          {/* Recommended doctors */}
          <div className="ws-card">
            <div className="ws-card__header">
              <h2 className="ws-card__title">Our doctors</h2>
              <Link
                to="/patient/book"
                style={{ fontSize: "0.85rem", color: "var(--blue)", fontWeight: 600 }}
              >
                Book now →
              </Link>
            </div>
            {data.doctor_cards.length === 0 ? (
              <div className="ws-empty">
                <div className="ws-empty__icon">🩺</div>
                <p className="ws-empty__title">No doctors yet</p>
                <p className="ws-empty__sub">Doctors will appear once they join the platform.</p>
              </div>
            ) : (
              <div className="ws-list">
                {data.doctor_cards.slice(0, 5).map((doc) => (
                  <div key={doc.doctor_id} className="ws-list-item">
                    <div className="ws-user-cell">
                      <div className="ws-user-avatar">
                        {doc.specialty?.slice(0, 2).toUpperCase() ?? "DR"}
                      </div>
                      <div>
                        <span className="ws-user-name">{doc.name}</span>
                        <span className="ws-user-email">
                          {doc.specialty ?? "General Care"}{doc.experience_years != null ? ` · ${doc.experience_years} yrs exp.` : ""}
                        </span>
                        {/* Next available slot */}
                        {doctorSlots[doc.doctor_id] !== undefined && (
                          <span style={{
                            display: "block",
                            fontSize: "0.76rem",
                            marginTop: "0.2rem",
                            color: doctorSlots[doc.doctor_id] ? "var(--green)" : "var(--text-soft)",
                            fontWeight: 600,
                          }}>
                            {doctorSlots[doc.doctor_id]
                              ? `🕐 Next: ${doctorSlots[doc.doctor_id]}`
                              : "No upcoming slots"}
                          </span>
                        )}
                      </div>
                    </div>
                    <Link
                      to="/patient/book"
                      className="ws-btn ws-btn--ghost"
                      style={{ fontSize: "0.8rem" }}
                    >
                      Book
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Upcoming appointments */}
          <div className="ws-card">
            <div className="ws-card__header">
              <h2 className="ws-card__title">Upcoming visits</h2>
              <Link
                to="/patient/appointments"
                style={{ fontSize: "0.85rem", color: "var(--blue)", fontWeight: 600 }}
              >
                View all →
              </Link>
            </div>
            {data.upcoming_appointments.length === 0 ? (
              <div className="ws-empty">
                <div className="ws-empty__icon">📅</div>
                <p className="ws-empty__title">No upcoming visits</p>
                <p className="ws-empty__sub">Book a consultation to begin your care journey.</p>
              </div>
            ) : (
              <div className="ws-list">
                {data.upcoming_appointments.slice(0, 5).map((apt) => (
                  <div key={apt.id} className="ws-list-item">
                    <div className="ws-list-item__main">
                      <span className="ws-list-item__title">{formatDateTime(apt.date_time)}</span>
                      <span className="ws-list-item__sub">
                        Fee: ₹{apt.fee}
                      </span>
                    </div>
                    <span className={`ws-badge ws-badge--${apt.status.toLowerCase()}`}>
                      {apt.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </SidebarLayout>
  );
}
