import { useEffect, useMemo, useState, useTransition } from "react";

import { SidebarLayout } from "@/components/layout/SidebarLayout";
import { PrescriptionSheet } from "@/components/ui/PrescriptionSheet";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { useAppSession } from "@/features/auth/session/AppSessionProvider";
import { loadDoctorAppointments, loadPrescriptionsForDoctor } from "@/features/shared/resource-loaders";
import { prescriptionApi } from "@/lib/api/endpoints";
import { formatDateTime } from "@/lib/utils/format";
import type { Appointment, Prescription } from "@/types/domain";

import { DOCTOR_NAV } from "./DoctorDashboardPage";

const HOSPITAL_NAME = "MedCare Hospital";
const HOSPITAL_ADDRESS = "24 Green Avenue, Lakeview Road, Bengaluru 560048";

export function DoctorPrescriptionsPage() {
  const { session } = useAppSession();
  const [items, setItems] = useState<Prescription[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [appointmentId, setAppointmentId] = useState("");
  const [medicines, setMedicines] = useState("");
  const [message, setMessage] = useState("");
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    if (!session) {
      return;
    }
    loadPrescriptionsForDoctor(session.user.id).then(setItems);
    loadDoctorAppointments(session.user.id).then((loaded) => setAppointments(loaded as Appointment[]));
  }, [session]);

  const prescribedAppointmentIds = useMemo(
    () => new Set(items.map((item) => item.appointment_id)),
    [items],
  );

  const completedAppointments = useMemo(
    () =>
      appointments.filter(
        (appointment) =>
          appointment.status === "COMPLETED" && !prescribedAppointmentIds.has(appointment.id),
      ),
    [appointments, prescribedAppointmentIds],
  );

  const selectedAppointment = useMemo(
    () => completedAppointments.find((appointment) => appointment.id === appointmentId) ?? null,
    [appointmentId, completedAppointments],
  );

  useEffect(() => {
    if (completedAppointments.length === 0) {
      if (appointmentId) {
        setAppointmentId("");
      }
      return;
    }
    if (!appointmentId || !completedAppointments.some((appointment) => appointment.id === appointmentId)) {
      setAppointmentId(completedAppointments[0].id);
    }
  }, [appointmentId, completedAppointments]);

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");

    startTransition(async () => {
      const payload = {
        appointment_id: appointmentId,
        medicines: medicines
          .split(/\r?\n|,/)
          .map((item) => item.trim())
          .filter(Boolean),
      };

      try {
        const created = await prescriptionApi.createPrescription(payload);
        setItems((current) => [created, ...current]);
      } catch {
        setItems((current) => [
          {
            id: `rx-${current.length + 10}`,
            appointment_id: appointmentId,
            doctor_id: session?.user.id ?? "doctor-demo",
            doctor_name: session?.user.name ?? "Treating Doctor",
            patient_id: selectedAppointment?.patient_id ?? "patient-101",
            patient_name: selectedAppointment?.patient_name ?? "Patient",
            patient_phone: selectedAppointment?.patient_phone ?? null,
            patient_age: selectedAppointment?.patient_age ?? null,
            patient_gender: selectedAppointment?.patient_gender ?? null,
            patient_blood_group: selectedAppointment?.patient_blood_group ?? null,
            visit_reason: selectedAppointment?.reason ?? null,
            medicines: payload.medicines,
            notes: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          ...current,
        ]);
      }

      setMedicines("");
      setMessage("Prescription saved successfully.");
    });
  }

  return (
    <SidebarLayout sections={DOCTOR_NAV}>
      <div className="content-grid">
        <section className="surface-card">
          <div className="surface-card__header">
            <div>
              <p className="eyebrow">Create prescription</p>
              <h2>Patient details and medicines</h2>
            </div>
          </div>
          <form className="form-grid" onSubmit={handleSubmit}>
            <div className="form-actions--full" style={{ display: "grid", gap: "0.8rem" }}>
              <label style={{ display: "grid", gap: "0.35rem" }}>
                <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-soft)" }}>
                  Completed appointment
                </span>
                <select
                  value={appointmentId}
                  onChange={(event) => setAppointmentId(event.target.value)}
                  disabled={completedAppointments.length === 0}
                  style={{
                    width: "100%",
                    padding: "0.75rem 0.9rem",
                    borderRadius: "var(--radius-sm)",
                    border: "1px solid var(--line)",
                    background: "var(--surface)",
                    font: "inherit",
                  }}
                >
                  {completedAppointments.length === 0 ? (
                    <option value="">No completed appointments available</option>
                  ) : null}
                  {completedAppointments.map((appointment) => (
                    <option key={appointment.id} value={appointment.id}>
                      {appointment.patient_name ?? "Patient"} - {formatDateTime(appointment.date_time)}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            {selectedAppointment ? (
              <div
                className="form-actions--full"
                style={{
                  padding: "1rem",
                  border: "1px solid var(--line)",
                  borderRadius: "var(--radius-sm)",
                  background: "var(--surface-muted)",
                }}
              >
                <div style={{ display: "grid", gap: "0.45rem" }}>
                  <h3 style={{ margin: 0, color: "var(--navy)" }}>
                    {selectedAppointment.patient_name ?? "Patient"}
                  </h3>
                  <p style={{ margin: 0, color: "var(--text-soft)", fontSize: "0.9rem" }}>
                    {selectedAppointment.patient_age ? `${selectedAppointment.patient_age} years` : "Age not provided"}
                    {selectedAppointment.patient_gender ? ` • ${selectedAppointment.patient_gender}` : ""}
                    {selectedAppointment.patient_blood_group ? ` • ${selectedAppointment.patient_blood_group}` : ""}
                  </p>
                  <p style={{ margin: 0, color: "var(--text-soft)", fontSize: "0.9rem" }}>
                    {selectedAppointment.patient_phone ?? "Phone not provided"}
                  </p>
                  <p style={{ margin: 0, color: "var(--text-soft)", fontSize: "0.9rem" }}>
                    Appointment: {formatDateTime(selectedAppointment.date_time)}
                  </p>
                  <p style={{ margin: 0, color: "var(--text-soft)", fontSize: "0.9rem" }}>
                    Reason: {selectedAppointment.reason ?? "Not provided"}
                  </p>
                </div>
              </div>
            ) : null}

            <div className="form-actions--full">
              <label style={{ display: "grid", gap: "0.35rem" }}>
                <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-soft)" }}>
                  Medicines and dosage
                </span>
                <textarea
                  value={medicines}
                  onChange={(event) => setMedicines(event.target.value)}
                  rows={5}
                  placeholder={"Paracetamol 650mg - 1 tablet twice daily\nVitamin D3 - 1 capsule after lunch"}
                  style={{
                    width: "100%",
                    padding: "0.85rem 0.9rem",
                    borderRadius: "var(--radius-sm)",
                    border: "1px solid var(--line)",
                    font: "inherit",
                    resize: "vertical",
                    minHeight: "7rem",
                  }}
                />
              </label>
              <p style={{ margin: "0.45rem 0 0", color: "var(--text-soft)", fontSize: "0.8rem" }}>
                Add one medicine per line with the required dosage.
              </p>
            </div>

            <div className="form-actions form-actions--full">
              {message ? <StatusBanner tone="success">{message}</StatusBanner> : null}
              <button
                type="submit"
                className="button button--primary"
                disabled={isPending || !appointmentId || medicines.trim().length === 0}
              >
                {isPending ? "Saving..." : "Save prescription"}
              </button>
            </div>
          </form>
        </section>

        <section className="surface-card">
          <div className="surface-card__header">
            <div>
              <p className="eyebrow">Prescription history</p>
              <h2>Saved prescriptions</h2>
            </div>
          </div>
          <div className="stack-list">
            {items.map((item) => (
              <PrescriptionSheet
                key={item.id}
                hospitalName={HOSPITAL_NAME}
                hospitalAddress={HOSPITAL_ADDRESS}
                doctorName={item.doctor_name ?? session?.user.name ?? "Doctor"}
                patientName={item.patient_name ?? "Patient"}
                patientPhone={item.patient_phone}
                patientAge={item.patient_age}
                patientGender={item.patient_gender}
                patientBloodGroup={item.patient_blood_group}
                visitReason={item.visit_reason}
                medicines={item.medicines}
                notes={item.notes}
                issuedAt={formatDateTime(item.updated_at)}
              />
            ))}
          </div>
        </section>
      </div>
    </SidebarLayout>
  );
}
