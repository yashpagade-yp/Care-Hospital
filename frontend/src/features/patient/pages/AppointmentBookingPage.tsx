import { useMemo, useState, useTransition } from "react";

import { RoleWorkspace } from "@/components/layout/RoleWorkspace";
import { FormField } from "@/components/ui/FormField";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { useAppSession } from "@/features/auth/session/AppSessionProvider";
import { patientWorkspaceLinks } from "@/features/shared/workspace-links";
import { doctorCards, mockUsers } from "@/lib/mock/data";
import { appointmentApi } from "@/lib/api/endpoints";
import { calculateAge, formatDate, formatDateTime } from "@/lib/utils/format";

const bookingSlots = [
  { label: "Tomorrow · 9:30 AM", dateTime: new Date(Date.now() + 86_400_000).toISOString() },
  { label: "Tomorrow · 11:00 AM", dateTime: new Date(Date.now() + 90_000_000).toISOString() },
  { label: "Day after · 2:30 PM", dateTime: new Date(Date.now() + 172_800_000).toISOString() },
];

export function AppointmentBookingPage() {
  const { session } = useAppSession();
  const [selectedDoctorId, setSelectedDoctorId] = useState(doctorCards[0]?.doctor_id ?? "");
  const [selectedSlot, setSelectedSlot] = useState(bookingSlots[0]?.dateTime ?? "");
  const [patientName, setPatientName] = useState(session?.user.name ?? mockUsers.patient.name);
  const [patientPhone, setPatientPhone] = useState(session?.user.phone ?? mockUsers.patient.phone ?? "");
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState("");
  const [confirmation, setConfirmation] = useState<string>("");
  const [isPending, startTransition] = useTransition();

  const selectedDoctor = useMemo(
    () => doctorCards.find((doctor) => doctor.doctor_id === selectedDoctorId) ?? null,
    [selectedDoctorId],
  );

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");

    startTransition(async () => {
      try {
        const hold = await appointmentApi.createSlotHold({
          doctor_id: selectedDoctorId,
          date_time: selectedSlot,
        });

        const booked = await appointmentApi.confirm({
          slot_hold_id: hold.id,
          patient_name: patientName,
          patient_phone: patientPhone,
          reason,
          fee: selectedDoctor?.specialty === "Cardiology" ? 1500 : 800,
        });

        setConfirmation(
          `Appointment confirmed for ${booked.doctor_name ?? selectedDoctor?.name ?? "the selected doctor"} on ${formatDateTime(booked.appointment.date_time)}.`,
        );
      } catch {
        setConfirmation(
          `Demo booking completed for ${selectedDoctor?.name ?? "the selected doctor"} on ${formatDateTime(selectedSlot)}.`,
        );
      }
    });
  }

  return (
    <RoleWorkspace
      heading="Book an appointment"
      summary="Choose a doctor, hold a slot, confirm patient details, and complete the mock payment flow."
      links={patientWorkspaceLinks}
    >
      <div className="content-grid">
        <section className="surface-card">
          <div className="surface-card__header">
            <div>
              <p className="eyebrow">Three-step booking</p>
              <h2>Appointment workflow</h2>
            </div>
          </div>
          <form className="form-grid" onSubmit={handleSubmit}>
            <div className="form-actions--full">
              <div className="selector-grid">
                {doctorCards.map((doctor) => (
                  <button
                    key={doctor.doctor_id}
                    type="button"
                    className={`selector-card${selectedDoctorId === doctor.doctor_id ? " selector-card--active" : ""}`}
                    onClick={() => setSelectedDoctorId(doctor.doctor_id)}
                  >
                    <strong>{doctor.name}</strong>
                    <span>{doctor.specialty}</span>
                    <small>{doctor.experience_years} years</small>
                  </button>
                ))}
              </div>
            </div>

            <div className="form-actions--full">
              <div className="selector-grid selector-grid--compact">
                {bookingSlots.map((slot) => (
                  <button
                    key={slot.dateTime}
                    type="button"
                    className={`selector-card${selectedSlot === slot.dateTime ? " selector-card--active" : ""}`}
                    onClick={() => setSelectedSlot(slot.dateTime)}
                  >
                    <strong>{slot.label}</strong>
                    <span>{formatDate(slot.dateTime)}</span>
                  </button>
                ))}
              </div>
            </div>

            <FormField
              label="Patient name"
              value={patientName}
              onChange={(event) => setPatientName(event.target.value)}
            />
            <FormField
              label="Patient phone"
              value={patientPhone}
              onChange={(event) => setPatientPhone(event.target.value)}
            />
            <FormField
              label="Patient age"
              value={String(calculateAge(mockUsers.patient.dob) ?? "")}
              readOnly
            />
            <FormField
              label="Consultation fee"
              value={`Rs. ${selectedDoctor?.specialty === "Cardiology" ? 1500 : 800}`}
              readOnly
            />
            <div className="form-actions--full">
              <FormField
                as="textarea"
                label="Reason for visit"
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                rows={4}
              />
            </div>
            <div className="form-actions form-actions--full">
              {message ? <StatusBanner tone="info">{message}</StatusBanner> : null}
              {confirmation ? <StatusBanner tone="success">{confirmation}</StatusBanner> : null}
              <button type="submit" className="button button--primary" disabled={isPending}>
                {isPending ? "Confirming..." : "Confirm booking"}
              </button>
            </div>
          </form>
        </section>

        <section className="surface-card">
          <div className="surface-card__header">
            <div>
              <p className="eyebrow">Booking summary</p>
              <h2>Selected visit details</h2>
            </div>
          </div>
          <dl className="detail-list">
            <div>
              <dt>Doctor</dt>
              <dd>{selectedDoctor?.name ?? "Not selected"}</dd>
            </div>
            <div>
              <dt>Specialty</dt>
              <dd>{selectedDoctor?.specialty ?? "N/A"}</dd>
            </div>
            <div>
              <dt>Slot</dt>
              <dd>{formatDateTime(selectedSlot)}</dd>
            </div>
            <div>
              <dt>Fee</dt>
              <dd>Rs. {selectedDoctor?.specialty === "Cardiology" ? 1500 : 800}</dd>
            </div>
          </dl>
        </section>
      </div>
    </RoleWorkspace>
  );
}
