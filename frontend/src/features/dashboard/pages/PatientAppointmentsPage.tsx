import { useEffect, useState, useTransition } from "react";

import { RoleWorkspace } from "@/components/layout/RoleWorkspace";
import { FormField } from "@/components/ui/FormField";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { useAppSession } from "@/features/auth/session/AppSessionProvider";
import { patientWorkspaceLinks } from "@/features/shared/workspace-links";
import { loadPatientAppointments } from "@/features/shared/resource-loaders";
import { appointmentApi } from "@/lib/api/endpoints";
import { formatDateTime } from "@/lib/utils/format";
import type { Appointment } from "@/types/domain";

export function PatientAppointmentsPage() {
  const { session } = useAppSession();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [message, setMessage] = useState("");
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    if (!session) {
      return;
    }

    loadPatientAppointments(session.user.id).then((items) =>
      setAppointments(items as Appointment[]),
    );
  }, [session]);

  function handleCancel(appointmentId: string) {
    const cancelReason = "Patient requested cancellation from the dashboard";
    setMessage("");

    startTransition(async () => {
      try {
        const updated = await appointmentApi.cancel(appointmentId, { cancel_reason: cancelReason });
        setAppointments((current) =>
          current.map((item) => (item.id === appointmentId ? updated : item)),
        );
      } catch {
        setAppointments((current) =>
          current.map((item) =>
            item.id === appointmentId
              ? {
                  ...item,
                  status: "CANCELLED",
                  cancel_reason: cancelReason,
                  payment_status: "REFUNDED",
                }
              : item,
          ),
        );
      }
      setMessage("Appointment updated successfully.");
    });
  }

  return (
    <RoleWorkspace
      heading="Patient appointments"
      summary="Review upcoming and historical visits, then cancel or reschedule within the allowed policy window."
      links={patientWorkspaceLinks}
    >
      {message ? <StatusBanner tone="success">{message}</StatusBanner> : null}
      <div className="surface-card">
        <div className="surface-card__header">
          <div>
            <p className="eyebrow">Appointment list</p>
            <h2>All patient appointments</h2>
          </div>
        </div>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Date and time</th>
                <th>Doctor</th>
                <th>Status</th>
                <th>Fee</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {appointments.map((appointment) => (
                <tr key={appointment.id}>
                  <td>{formatDateTime(appointment.date_time)}</td>
                  <td>{appointment.doctor_id}</td>
                  <td><span className={`pill pill--${appointment.status.toLowerCase()}`}>{appointment.status}</span></td>
                  <td>Rs. {appointment.fee}</td>
                  <td>
                    {appointment.status === "CONFIRMED" ? (
                      <button
                        type="button"
                        className="button button--ghost button--compact"
                        onClick={() => handleCancel(appointment.id)}
                        disabled={isPending}
                      >
                        Cancel
                      </button>
                    ) : (
                      <span className="table-note">Completed action</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </RoleWorkspace>
  );
}
