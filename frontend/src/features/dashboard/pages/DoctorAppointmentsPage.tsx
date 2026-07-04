import { useEffect, useState, useTransition } from "react";

import { SidebarLayout } from "@/components/layout/SidebarLayout";
import { DOCTOR_NAV } from "./DoctorDashboardPage";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { useAppSession } from "@/features/auth/session/AppSessionProvider";
import { loadDoctorAppointments } from "@/features/shared/resource-loaders";
import { appointmentApi } from "@/lib/api/endpoints";
import { formatDateTime } from "@/lib/utils/format";
import type { Appointment } from "@/types/domain";

function formatPatientSummary(appointment: Appointment) {
  const summaryParts = [
    appointment.patient_age ? `${appointment.patient_age} yrs` : null,
    appointment.patient_gender ?? null,
    appointment.patient_blood_group ? `Blood ${appointment.patient_blood_group}` : null,
  ].filter(Boolean);

  return summaryParts.length > 0 ? summaryParts.join(" • ") : "Patient information not available";
}

export function DoctorAppointmentsPage() {
  const { session } = useAppSession();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [message, setMessage] = useState("");
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    if (!session) {
      return;
    }
    loadDoctorAppointments(session.user.id).then((items) => setAppointments(items as Appointment[]));
  }, [session]);

  function updateStatus(appointmentId: string, status: "COMPLETED" | "NO_SHOW") {
    setMessage("");
    startTransition(async () => {
      try {
        const updated = await appointmentApi.updateStatus(appointmentId, { status });
        setAppointments((current) =>
          current.map((item) => (item.id === appointmentId ? updated : item)),
        );
      } catch {
        setAppointments((current) =>
          current.map((item) => (item.id === appointmentId ? { ...item, status } : item)),
        );
      }
      setMessage(`Appointment marked as ${status}.`);
    });
  }

  return (
    <SidebarLayout sections={DOCTOR_NAV}>
      {message ? <StatusBanner tone="success">{message}</StatusBanner> : null}
      <section className="surface-card">
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Date and time</th>
                <th>Patient</th>
                <th>Status</th>
                <th>Fee</th>
                <th>Clinical action</th>
              </tr>
            </thead>
            <tbody>
              {appointments.map((appointment) => (
                <tr key={appointment.id}>
                  <td>{formatDateTime(appointment.date_time)}</td>
                  <td>
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.2rem" }}>
                      <span style={{ fontWeight: 700, color: "var(--navy)" }}>
                        {appointment.patient_name ?? "Patient"}
                      </span>
                      <span style={{ fontSize: "0.8rem", color: "var(--text-soft)" }}>
                        {formatPatientSummary(appointment)}
                      </span>
                      {appointment.patient_phone ? (
                        <span style={{ fontSize: "0.78rem", color: "var(--text-soft)" }}>
                          {appointment.patient_phone}
                        </span>
                      ) : null}
                      {appointment.reason ? (
                        <span style={{ fontSize: "0.78rem", color: "var(--text-soft)" }}>
                          Reason: {appointment.reason}
                        </span>
                      ) : null}
                    </div>
                  </td>
                  <td><span className={`pill pill--${appointment.status.toLowerCase()}`}>{appointment.status}</span></td>
                  <td>Rs. {appointment.fee}</td>
                  <td>
                    {appointment.status === "CONFIRMED" ? (
                      <div className="table-actions">
                        <button
                          type="button"
                          className="button button--ghost button--compact"
                          onClick={() => updateStatus(appointment.id, "COMPLETED")}
                          disabled={isPending}
                        >
                          Mark completed
                        </button>
                        <button
                          type="button"
                          className="button button--ghost button--compact"
                          onClick={() => updateStatus(appointment.id, "NO_SHOW")}
                          disabled={isPending}
                        >
                          Mark no-show
                        </button>
                      </div>
                    ) : (
                      <span className="table-note">No further action</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </SidebarLayout>
  );
}
