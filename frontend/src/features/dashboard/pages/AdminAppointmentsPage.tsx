import { useEffect, useState } from "react";

import { SidebarLayout } from "@/components/layout/SidebarLayout";
import { EmptyState } from "@/components/ui/EmptyState";
import { loadAdminAppointments, loadPaymentByAppointment } from "@/features/shared/resource-loaders";
import { formatDateTime } from "@/lib/utils/format";
import type { Appointment, Payment } from "@/types/domain";
import { ADMIN_NAV } from "./AdminDashboardPage";

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
    <SidebarLayout sections={ADMIN_NAV}>
      <div className="ws-page-header">
        <p className="ws-page-eyebrow">Admin Workspace</p>
        <h1 className="ws-page-heading">All Appointments</h1>
        <p className="ws-page-sub">
          View and manage all patient-doctor appointments, payment statuses, and booking details.
        </p>
      </div>

      <div className="ws-grid ws-grid--2">
        <div className="ws-card" style={{ gridColumn: '1 / -1' }}>
          <div className="ws-card__header">
            <h2 className="ws-card__title">Appointment records</h2>
          </div>
          <div className="ws-table-wrap">
            <table className="ws-table">
              <thead>
                <tr>
                  <th>Date &amp; Time</th>
                  <th>Patient</th>
                  <th>Doctor</th>
                  <th>Status</th>
                  <th>Payment</th>
                </tr>
              </thead>
              <tbody>
                {appointments.map((appointment) => (
                  <tr key={appointment.id}>
                    <td style={{ fontWeight: 600 }}>{formatDateTime(appointment.date_time)}</td>
                    <td style={{ color: 'var(--text-soft)', fontSize: '0.85rem' }}>{appointment.patient_id}</td>
                    <td style={{ color: 'var(--text-soft)', fontSize: '0.85rem' }}>{appointment.doctor_id}</td>
                    <td><span className={`ws-badge ws-badge--${appointment.status.toLowerCase()}`}>{appointment.status}</span></td>
                    <td>
                      <button
                        type="button"
                        className="ws-btn ws-btn--ghost"
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
        </div>

        {selectedPayment && (
          <div className="ws-card">
            <div className="ws-card__header">
              <h2 className="ws-card__title">Payment detail</h2>
            </div>
            <div className="ws-card__body">
              <dl className="detail-list">
                <div>
                  <dt>Transaction ref</dt>
                  <dd>{selectedPayment.transaction_ref}</dd>
                </div>
                <div>
                  <dt>Amount</dt>
                  <dd>₹{selectedPayment.amount}</dd>
                </div>
                <div>
                  <dt>Status</dt>
                  <dd>{selectedPayment.status}</dd>
                </div>
              </dl>
            </div>
          </div>
        )}
      </div>
    </SidebarLayout>
  );
}
