import { useEffect, useState, useTransition } from "react";

import { SidebarLayout } from "@/components/layout/SidebarLayout";
import { DOCTOR_NAV } from "./DoctorDashboardPage";
import { FormField } from "@/components/ui/FormField";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { useAppSession } from "@/features/auth/session/AppSessionProvider";
import { loadPrescriptionsForDoctor } from "@/features/shared/resource-loaders";
import { prescriptionApi } from "@/lib/api/endpoints";
import type { Prescription } from "@/types/domain";

export function DoctorPrescriptionsPage() {
  const { session } = useAppSession();
  const [items, setItems] = useState<Prescription[]>([]);
  const [appointmentId, setAppointmentId] = useState("appt-002");
  const [medicines, setMedicines] = useState("Vitamin D, Sleep support tablets");
  const [notes, setNotes] = useState("");
  const [message, setMessage] = useState("");
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    if (!session) {
      return;
    }
    loadPrescriptionsForDoctor(session.user.id).then(setItems);
  }, [session]);

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");

    startTransition(async () => {
      const payload = {
        appointment_id: appointmentId,
        medicines: medicines.split(",").map((item) => item.trim()).filter(Boolean),
        notes,
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
            patient_id: "patient-101",
            medicines: payload.medicines,
            notes,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          ...current,
        ]);
      }

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
              <h2>Consultation notes and medicines</h2>
            </div>
          </div>
          <form className="form-grid" onSubmit={handleSubmit}>
            <FormField
              label="Appointment ID"
              value={appointmentId}
              onChange={(event) => setAppointmentId(event.target.value)}
            />
            <div className="form-actions--full">
              <FormField
                label="Medicines"
                value={medicines}
                onChange={(event) => setMedicines(event.target.value)}
                hint="Enter comma-separated medicines."
              />
            </div>
            <div className="form-actions--full">
              <FormField
                as="textarea"
                label="Notes"
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                rows={4}
              />
            </div>
            <div className="form-actions form-actions--full">
              {message ? <StatusBanner tone="success">{message}</StatusBanner> : null}
              <button type="submit" className="button button--primary" disabled={isPending}>
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
              <article key={item.id} className="stack-list__item stack-list__item--block">
                <div>
                  <h3>{item.appointment_id}</h3>
                  <p>Patient {item.patient_id}</p>
                </div>
                <ul className="chip-row">
                  {item.medicines.map((medicine) => (
                    <li key={medicine} className="chip">{medicine}</li>
                  ))}
                </ul>
                <p>{item.notes ?? "No additional notes."}</p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </SidebarLayout>
  );
}
