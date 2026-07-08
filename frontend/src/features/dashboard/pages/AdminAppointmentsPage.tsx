import { useEffect, useState } from "react";

import { SidebarLayout } from "@/components/layout/SidebarLayout";
import { EmptyState } from "@/components/ui/EmptyState";
import { loadAdminAppointments, loadPaymentByAppointment } from "@/features/shared/resource-loaders";
import { formatDateTime } from "@/lib/utils/format";
import type { Appointment, Payment } from "@/types/domain";

import { ADMIN_NAV } from "./AdminDashboardPage";

function formatPatientSummary(appointment: Appointment) {
  const parts = [
    appointment.patient_age ? `${appointment.patient_age} yrs` : null,
    appointment.patient_gender ?? null,
    appointment.patient_blood_group ? `Blood ${appointment.patient_blood_group}` : null,
  ].filter(Boolean);

  return parts.length > 0 ? parts.join(" • ") : "Patient information not available";
}

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
          View real patient bookings, their treatment details, assigned doctors, and payment records.
        </p>
      </div>

      <div className="ws-grid ws-grid--2">
        <div className="ws-card" style={{ gridColumn: "1 / -1" }}>
          <div className="ws-card__header">
            <div>
              <h2 className="ws-card__title">Appointment records</h2>
              <p className="ws-card__sub">
                New appointments created by patients will appear here automatically.
              </p>
            </div>
          </div>

          {appointments.length === 0 ? (
            <div className="ws-card__body">
              <EmptyState
                title="No appointments yet"
                description="Patient-created appointments will appear here once bookings begin."
              />
            </div>
          ) : (
            <div className="ws-table-wrap">
              <table className="ws-table">
                <thead>
                  <tr>
                    <th>Date &amp; Time</th>
                    <th>Patient information</th>
                    <th>Doctor</th>
                    <th>Status</th>
                    <th>Payment</th>
                  </tr>
                </thead>
                <tbody>
                  {appointments.map((appointment) => (
                    <tr key={appointment.id}>
                      <td style={{ fontWeight: 600 }}>{formatDateTime(appointment.date_time)}</td>
                      <td>
                        <div style={{ display: "flex", flexDirection: "column", gap: "0.2rem" }}>
                          <span style={{ fontWeight: 700, color: "var(--navy)" }}>
                            {appointment.patient_name ?? "Patient"}
                          </span>
                          <span style={{ color: "var(--text-soft)", fontSize: "0.82rem" }}>
                            {formatPatientSummary(appointment)}
                          </span>
                          <span style={{ color: "var(--text-soft)", fontSize: "0.82rem" }}>
                            {appointment.patient_phone ?? "Phone not provided"}
                          </span>
                          <span style={{ color: "var(--text-soft)", fontSize: "0.82rem" }}>
                            Reason: {appointment.reason ?? "Not provided"}
                          </span>
                        </div>
                      </td>
                      <td>
                        <div style={{ display: "flex", flexDirection: "column", gap: "0.2rem" }}>
                          <span style={{ fontWeight: 700, color: "var(--navy)" }}>
                            {appointment.doctor_name ?? "Doctor"}
                          </span>
                          <span style={{ color: "var(--text-soft)", fontSize: "0.82rem" }}>
                            {appointment.doctor_id}
                          </span>
                        </div>
                      </td>
                      <td>
                        <span className={`ws-badge ws-badge--${appointment.status.toLowerCase()}`}>
                          {appointment.status}
                        </span>
                      </td>
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
          )}
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
