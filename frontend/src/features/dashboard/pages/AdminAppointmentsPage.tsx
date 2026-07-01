import { useEffect, useState } from "react";

import { RoleWorkspace } from "@/components/layout/RoleWorkspace";
import { EmptyState } from "@/components/ui/EmptyState";
import { adminWorkspaceLinks } from "@/features/shared/workspace-links";
import { loadAdminAppointments, loadPaymentByAppointment } from "@/features/shared/resource-loaders";
import { formatDateTime } from "@/lib/utils/format";
import type { Appointment, Payment } from "@/types/domain";

export function AdminAppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [selectedPayment, setSelectedPayment] = useState<Payment | null>(null);

  useEffect(() => {
    loadAdminAppointments().then(setAppointments);
  }, []);

  async function handleLoadPayment(appointmentId: string) {
    const payment = await loadPaymentByAppointment(appointmentId);
    setSelectedPayment(payment);
  }

  return (
    <RoleWorkspace
      heading="Admin appointments"
      summary="Track operational booking state, patient-doctor mapping, and payment references without exposing prescriptions."
      links={adminWorkspaceLinks}
    >
      <div className="content-grid">
        <section className="surface-card">
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date and time</th>
                  <th>Patient</th>
                  <th>Doctor</th>
                  <th>Status</th>
                  <th>Payment</th>
                </tr>
              </thead>
              <tbody>
                {appointments.map((appointment) => (
                  <tr key={appointment.id}>
                    <td>{formatDateTime(appointment.date_time)}</td>
                    <td>{appointment.patient_id}</td>
                    <td>{appointment.doctor_id}</td>
                    <td><span className={`pill pill--${appointment.status.toLowerCase()}`}>{appointment.status}</span></td>
                    <td>
                      <button
                        type="button"
                        className="button button--ghost button--compact"
                        onClick={() => handleLoadPayment(appointment.id)}
                      >
                        View payment
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="surface-card">
          <div className="surface-card__header">
            <div>
              <p className="eyebrow">Payment detail</p>
              <h2>Appointment-linked payment</h2>
            </div>
          </div>
          {selectedPayment ? (
            <dl className="detail-list">
              <div>
                <dt>Transaction</dt>
                <dd>{selectedPayment.transaction_ref}</dd>
              </div>
              <div>
                <dt>Amount</dt>
                <dd>Rs. {selectedPayment.amount}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>{selectedPayment.status}</dd>
              </div>
            </dl>
          ) : (
            <EmptyState
              title="No payment selected"
              description="Choose an appointment from the table to inspect payment details."
            />
          )}
        </section>
      </div>
    </RoleWorkspace>
  );
}
