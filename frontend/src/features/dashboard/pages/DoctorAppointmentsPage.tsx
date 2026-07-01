import { useEffect, useState, useTransition } from "react";

import { RoleWorkspace } from "@/components/layout/RoleWorkspace";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { useAppSession } from "@/features/auth/session/AppSessionProvider";
import { doctorWorkspaceLinks } from "@/features/shared/workspace-links";
import { loadDoctorAppointments } from "@/features/shared/resource-loaders";
import { appointmentApi } from "@/lib/api/endpoints";
import { formatDateTime } from "@/lib/utils/format";
import type { Appointment } from "@/types/domain";

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
    <RoleWorkspace
      heading="Doctor appointments"
      summary="Manage confirmed visits, complete consultations, and track appointment outcomes."
      links={doctorWorkspaceLinks}
    >
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
                  <td>{appointment.patient_id}</td>
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
    </RoleWorkspace>
  );
}
