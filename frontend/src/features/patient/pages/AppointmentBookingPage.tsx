import { useEffect, useMemo, useState, useTransition } from "react";
import { SidebarLayout } from "@/components/layout/SidebarLayout";
import { useAppSession } from "@/features/auth/session/AppSessionProvider";
import { isApiError } from "@/lib/api/client";
import { appointmentApi, availabilityApi, userApi } from "@/lib/api/endpoints";
import type { DoctorAvailability, DoctorProfile } from "@/types/domain";
import { PATIENT_NAV } from "@/features/dashboard/pages/PatientDashboardPage";

// Generate next 5 bookable slots from a doctor's weekly availability
// NOTE: we use a local-time ISO string (not UTC toISOString) so the backend
// receives the exact HH:MM the doctor configured, not the UTC-shifted version.
function toLocalISOString(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  const offsetMin = -d.getTimezoneOffset(); // e.g. +330 for IST
  const sign = offsetMin >= 0 ? "+" : "-";
  const absOffset = Math.abs(offsetMin);
  const oh = pad(Math.floor(absOffset / 60));
  const om = pad(absOffset % 60);
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
    `T${pad(d.getHours())}:${pad(d.getMinutes())}:00${sign}${oh}:${om}`
  );
}

function slotTimestamp(value: string): number | null {
  const timestamp = new Date(value).getTime();
  return Number.isNaN(timestamp) ? null : timestamp;
}

function generateUpcomingSlots(
  availabilities: DoctorAvailability[],
  bookedSlotTimes: string[],
  count = 5,
): { label: string; dateTime: string }[] {
  const dayMap: Record<string, number> = {
    MONDAY: 1, TUESDAY: 2, WEDNESDAY: 3, THURSDAY: 4,
    FRIDAY: 5, SATURDAY: 6, SUNDAY: 0,
  };
  const slots: { label: string; dateTime: string }[] = [];
  const now = new Date();
  const bookedSlotSet = new Set(
    bookedSlotTimes
      .map(slotTimestamp)
      .filter((timestamp): timestamp is number => timestamp !== null),
  );

  for (let daysAhead = 0; daysAhead <= 14 && slots.length < count; daysAhead++) {
    const date = new Date(now);
    date.setDate(now.getDate() + daysAhead);
    const dayNum = date.getDay();

    for (const avail of availabilities) {
      if (avail.availability_type !== "RECURRING" || !avail.day_of_week) continue;
      if (dayMap[avail.day_of_week] !== dayNum) continue;

      const [startH, startM] = avail.start_time.split(":").map(Number);
      const slotDate = new Date(date);
      slotDate.setHours(startH, startM, 0, 0);
      if (slotDate <= now) continue;
      if (bookedSlotSet.has(slotDate.getTime())) continue;

      const label = daysAhead === 0
        ? `Today · ${avail.start_time}`
        : daysAhead === 1
        ? `Tomorrow · ${avail.start_time}`
        : `${date.toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short" })} · ${avail.start_time}`;

      // Use local ISO string to preserve exact local HH:MM (not UTC-shifted)
      slots.push({ label, dateTime: toLocalISOString(slotDate) });
      if (slots.length >= count) break;
    }
  }

  // Fallback if no weekly availability set — generate generic slots
  if (slots.length === 0) {
    for (let i = 1; i <= count; i++) {
      const d = new Date(now);
      d.setDate(d.getDate() + i);
      d.setHours(10, 0, 0, 0);
      if (bookedSlotSet.has(d.getTime())) continue;
      slots.push({
        label: `${d.toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short" })} · 10:00 AM`,
        dateTime: toLocalISOString(d),
      });
    }
  }

  return slots;
}

function formatSlotFull(iso: string) {
  return new Date(iso).toLocaleString("en-IN", {
    weekday: "short", day: "numeric", month: "short",
    year: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

export function AppointmentBookingPage() {
  const { session } = useAppSession();

  const [doctors, setDoctors] = useState<DoctorProfile[]>([]);
  const [selectedDoctorId, setSelectedDoctorId] = useState("");
  const [availability, setAvailability] = useState<DoctorAvailability[]>([]);
  const [bookedSlotTimes, setBookedSlotTimes] = useState<string[]>([]);
  const [selectedSlot, setSelectedSlot] = useState("");
  // Patient details (Step 3) — editable so user can book for a family member
  const [patientName, setPatientName] = useState(session?.user.name ?? "");
  const [patientAge, setPatientAge] = useState("");
  const [patientGender, setPatientGender] = useState("");
  const [patientBloodGroup, setPatientBloodGroup] = useState("");
  const [patientPhone, setPatientPhone] = useState(session?.user.phone ?? "");
  const [reason, setReason] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [error, setError] = useState("");
  const [loadingDoctors, setLoadingDoctors] = useState(true);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [isPending, startTransition] = useTransition();

  const selectedDoctor = useMemo(
    () => doctors.find((d) => d.id === selectedDoctorId) ?? null,
    [doctors, selectedDoctorId],
  );

  const slots = useMemo(
    () => generateUpcomingSlots(availability, bookedSlotTimes),
    [availability, bookedSlotTimes],
  );

  // Load real doctors from backend
  useEffect(() => {
    userApi.listDoctors()
      .then((res) => {
        const active = res.items.filter((d) => d.doctor_status !== "SUSPENDED");
        setDoctors(active);
        if (active.length > 0) setSelectedDoctorId(active[0].id);
      })
      .catch(() => {})
      .finally(() => setLoadingDoctors(false));
  }, []);

  // Load availability when doctor changes
  useEffect(() => {
    if (!selectedDoctorId) return;
    setLoadingSlots(true);
    setAvailability([]);
    setBookedSlotTimes([]);
    setSelectedSlot("");
    Promise.all([
      availabilityApi.listDoctorAvailability(selectedDoctorId),
      appointmentApi.listDoctorBookedSlots(selectedDoctorId),
    ])
      .then(([availabilityResponse, bookedSlotsResponse]) => {
        setAvailability(availabilityResponse.items);
        setBookedSlotTimes(bookedSlotsResponse.items);
      })
      .catch(() => {
        setAvailability([]);
        setBookedSlotTimes([]);
      })
      .finally(() => setLoadingSlots(false));
  }, [selectedDoctorId]);

  // Auto-select first slot when slots change
  useEffect(() => {
    if (slots.length > 0) setSelectedSlot(slots[0].dateTime);
  }, [slots]);

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setConfirmation("");
    setError("");

    startTransition(async () => {
      try {
        // Step 1: Create a slot hold
        const hold = await appointmentApi.createSlotHold({
          doctor_id: selectedDoctorId,
          date_time: selectedSlot,
        });

        // Step 2: Confirm the appointment
        await appointmentApi.confirm({
          slot_hold_id: hold.id,
          patient_name: patientName || session?.user.name || "Patient",
          patient_phone: patientPhone || session?.user.phone || "",
          patient_age: Number(patientAge),
          patient_gender: patientGender,
          patient_blood_group: patientBloodGroup || undefined,
          reason,
          fee: selectedDoctor?.consultation_fee ?? 500,
        });

        setConfirmation(
          `✅ Appointment booked with ${selectedDoctor?.name ?? "the doctor"} on ${formatSlotFull(selectedSlot)}. You will receive a confirmation shortly.`,
        );
        setBookedSlotTimes((current) => {
          const selectedTimestamp = slotTimestamp(selectedSlot);
          if (selectedTimestamp === null) {
            return current;
          }

          const alreadyTracked = current.some(
            (slot) => slotTimestamp(slot) === selectedTimestamp,
          );
          return alreadyTracked ? current : [...current, selectedSlot];
        });
        setReason("");
      } catch (error) {
        if (isApiError(error) && error.status === 409) {
          setBookedSlotTimes((current) => {
            const selectedTimestamp = slotTimestamp(selectedSlot);
            if (selectedTimestamp === null) {
              return current;
            }

            const alreadyTracked = current.some(
              (slot) => slotTimestamp(slot) === selectedTimestamp,
            );
            return alreadyTracked ? current : [...current, selectedSlot];
          });
          setError("This slot was just booked by someone else. Please choose another available time.");
          return;
        }

        setError(
          isApiError(error)
            ? error.message
            : "Could not complete the booking. Please try again or contact support.",
        );
      }
    });
  }

  return (
    <SidebarLayout sections={PATIENT_NAV}>
      <div className="ws-page-header">
        <p className="ws-page-eyebrow">Patient Workspace</p>
        <h1 className="ws-page-heading">Book an appointment</h1>
        <p className="ws-page-sub">
          Choose your doctor, pick an available slot, and confirm your visit.
        </p>
      </div>

      {confirmation && (
        <div style={{
          padding: "1rem 1.25rem",
          background: "var(--green-soft)",
          border: "1px solid rgba(13,158,110,0.25)",
          borderRadius: "var(--radius-sm)",
          color: "var(--status-active-text)",
          fontWeight: 600,
          marginBottom: "1.5rem",
          fontSize: "0.92rem",
        }}>
          {confirmation}
        </div>
      )}

      {error && (
        <div style={{
          padding: "1rem 1.25rem",
          background: "#fff0f0",
          border: "1px solid rgba(220,53,69,0.25)",
          borderRadius: "var(--radius-sm)",
          color: "#c0392b",
          fontWeight: 600,
          marginBottom: "1.5rem",
          fontSize: "0.92rem",
        }}>
          {error}
        </div>
      )}

      <div className="ws-grid ws-grid--2">
        {/* ── Left: booking form ── */}
        <form onSubmit={handleSubmit}>
          {/* Step 1: Select doctor */}
          <div className="ws-card" style={{ marginBottom: "1.25rem" }}>
            <div className="ws-card__header">
              <h2 className="ws-card__title">Step 1 — Choose a doctor</h2>
            </div>
            {loadingDoctors ? (
              <div className="ws-loading">Loading doctors…</div>
            ) : doctors.length === 0 ? (
              <div className="ws-empty">
                <div className="ws-empty__icon">🩺</div>
                <p className="ws-empty__title">No doctors available</p>
                <p className="ws-empty__sub">Please check back later.</p>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem", padding: "0 1.25rem 1.25rem" }}>
                {doctors.map((doc) => (
                  <button
                    key={doc.id}
                    type="button"
                    onClick={() => setSelectedDoctorId(doc.id)}
                    style={{
                      display: "flex",
                      alignItems: "flex-start",
                      gap: "0.85rem",
                      padding: "0.85rem 1rem",
                      borderRadius: "var(--radius-sm)",
                      border: selectedDoctorId === doc.id
                        ? "2px solid var(--blue)"
                        : "2px solid var(--line)",
                      background: selectedDoctorId === doc.id ? "var(--blue-soft)" : "var(--surface)",
                      cursor: "pointer",
                      textAlign: "left",
                      transition: "all 0.16s",
                      width: "100%",
                    }}
                  >
                    <div className="ws-user-avatar" style={{ flexShrink: 0, marginTop: "0.1rem" }}>
                      {doc.name.split(" ").map((p) => p[0]).join("").slice(0, 2).toUpperCase()}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 700, color: "var(--navy)", fontSize: "0.95rem" }}>
                        Dr. {doc.name}
                      </div>
                      <div style={{ fontSize: "0.82rem", color: "var(--text-soft)", marginBottom: "0.35rem" }}>
                        {doc.specialty ?? "General"}{doc.experience_years != null ? ` · ${doc.experience_years} yrs exp.` : ""}
                      </div>
                      {/* Show doctor's weekly schedule */}
                      {(() => {
                        const recurSlots = availability.filter(
                          (a) => a.doctor_id === doc.id && a.availability_type === "RECURRING"
                        );
                        if (recurSlots.length === 0) return null;
                        return (
                          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.3rem", marginTop: "0.25rem" }}>
                            {recurSlots.map((sl) => (
                              <span key={sl.id} style={{
                                fontSize: "0.72rem", fontWeight: 600,
                                background: "#dbeafe", color: "#1d4ed8",
                                padding: "0.15rem 0.5rem", borderRadius: "999px",
                              }}>
                                {sl.day_of_week} · {sl.start_time?.slice(0,5)}–{sl.end_time?.slice(0,5)}
                              </span>
                            ))}
                          </div>
                        );
                      })()}
                    </div>
                    {selectedDoctorId === doc.id && (
                      <span style={{ color: "var(--blue)", fontWeight: 700, fontSize: "1.1rem" }}>✓</span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Step 2: Select time slot */}
          <div className="ws-card" style={{ marginBottom: "1.25rem" }}>
            <div className="ws-card__header">
              <h2 className="ws-card__title">Step 2 — Pick a time slot</h2>
            </div>
            {loadingSlots ? (
              <div className="ws-loading">Loading available slots…</div>
            ) : slots.length === 0 ? (
              <div className="ws-empty">
                <div className="ws-empty__icon">📅</div>
                <p className="ws-empty__title">
                  {availability.length > 0 ? "No free slots right now" : "No slots configured"}
                </p>
                <p className="ws-empty__sub">
                  {availability.length > 0
                    ? "All currently visible slots are already booked. Please try another doctor or refresh later."
                    : "This doctor has not set their availability yet."}
                </p>
              </div>
            ) : (
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.6rem", padding: "0 1.25rem 1.25rem" }}>
                {slots.map((slot) => (
                  <button
                    key={slot.dateTime}
                    type="button"
                    onClick={() => setSelectedSlot(slot.dateTime)}
                    style={{
                      padding: "0.55rem 1rem",
                      borderRadius: "var(--radius-sm)",
                      border: selectedSlot === slot.dateTime
                        ? "2px solid var(--blue)"
                        : "2px solid var(--line)",
                      background: selectedSlot === slot.dateTime ? "var(--blue)" : "var(--surface)",
                      color: selectedSlot === slot.dateTime ? "#fff" : "var(--text)",
                      fontWeight: 600,
                      fontSize: "0.85rem",
                      cursor: "pointer",
                      transition: "all 0.16s",
                    }}
                  >
                    {slot.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Step 3: Confirm details */}
          <div className="ws-card">
            <div className="ws-card__header">
              <h2 className="ws-card__title">Step 3 — Confirm patient details</h2>
            </div>
            <div style={{ padding: "0 1.25rem 1.25rem", display: "flex", flexDirection: "column", gap: "0.85rem" }}>

              {/* Helper note */}
              <p style={{ fontSize: "0.82rem", color: "var(--text-soft)", margin: 0 }}>
                Fill in the details of the patient visiting the doctor. You can book for yourself or a family member.
              </p>

              {/* Row 1: Full Name + Phone */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.85rem" }}>
                <div>
                  <label style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--text-soft)", display: "block", marginBottom: "0.3rem" }}>Patient full name *</label>
                  <input
                    type="text"
                    value={patientName}
                    onChange={(e) => setPatientName(e.target.value)}
                    placeholder="Enter patient's full name"
                    required
                    style={{
                      width: "100%", padding: "0.6rem 0.85rem",
                      border: "1px solid var(--line)", borderRadius: "var(--radius-sm)",
                      fontSize: "0.9rem", fontFamily: "inherit",
                    }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--text-soft)", display: "block", marginBottom: "0.3rem" }}>Phone number *</label>
                  <input
                    type="tel"
                    value={patientPhone}
                    onChange={(e) => setPatientPhone(e.target.value)}
                    placeholder="+91 98765 43210"
                    required
                    style={{
                      width: "100%", padding: "0.6rem 0.85rem",
                      border: "1px solid var(--line)", borderRadius: "var(--radius-sm)",
                      fontSize: "0.9rem", fontFamily: "inherit",
                    }}
                  />
                </div>
              </div>

              {/* Row 2: Age + Gender */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.85rem" }}>
                <div>
                  <label style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--text-soft)", display: "block", marginBottom: "0.3rem" }}>Age *</label>
                  <input
                    type="number"
                    value={patientAge}
                    onChange={(e) => setPatientAge(e.target.value)}
                    placeholder="e.g. 45"
                    min={0}
                    max={120}
                    required
                    style={{
                      width: "100%", padding: "0.6rem 0.85rem",
                      border: "1px solid var(--line)", borderRadius: "var(--radius-sm)",
                      fontSize: "0.9rem", fontFamily: "inherit",
                    }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--text-soft)", display: "block", marginBottom: "0.3rem" }}>Gender *</label>
                  <select
                    value={patientGender}
                    onChange={(e) => setPatientGender(e.target.value)}
                    required
                    style={{
                      width: "100%", padding: "0.6rem 0.85rem",
                      border: "1px solid var(--line)", borderRadius: "var(--radius-sm)",
                      fontSize: "0.9rem", fontFamily: "inherit",
                      background: "var(--surface)", cursor: "pointer",
                    }}
                  >
                    <option value="">Select gender</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                    <option value="Prefer not to say">Prefer not to say</option>
                  </select>
                </div>
              </div>

              {/* Row 3: Blood Group + Consultation Fee */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.85rem" }}>
                <div>
                  <label style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--text-soft)", display: "block", marginBottom: "0.3rem" }}>Blood group</label>
                  <select
                    value={patientBloodGroup}
                    onChange={(e) => setPatientBloodGroup(e.target.value)}
                    style={{
                      width: "100%", padding: "0.6rem 0.85rem",
                      border: "1px solid var(--line)", borderRadius: "var(--radius-sm)",
                      fontSize: "0.9rem", fontFamily: "inherit",
                      background: "var(--surface)", cursor: "pointer",
                    }}
                  >
                    <option value="">Select blood group</option>
                    {["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].map((bg) => (
                      <option key={bg} value={bg}>{bg}</option>
                    ))}
                    <option value="Unknown">Unknown</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--text-soft)", display: "block", marginBottom: "0.3rem" }}>Consultation fee</label>
                  <input
                    type="text"
                    value={selectedDoctor?.consultation_fee != null ? `₹${selectedDoctor.consultation_fee}` : "₹500"}
                    readOnly
                    style={{
                      width: "100%", padding: "0.6rem 0.85rem",
                      border: "1px solid var(--line)", borderRadius: "var(--radius-sm)",
                      background: "#f8f9fa", color: "var(--text)", fontSize: "0.9rem",
                    }}
                  />
                </div>
              </div>

              {/* Reason for visit */}
              <div>
                <label style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--text-soft)", display: "block", marginBottom: "0.3rem" }}>Reason for visit (optional)</label>
                <textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  rows={3}
                  placeholder="Describe symptoms or reason for the visit…"
                  style={{
                    width: "100%", padding: "0.6rem 0.85rem",
                    border: "1px solid var(--line)", borderRadius: "var(--radius-sm)",
                    fontSize: "0.9rem", resize: "vertical", fontFamily: "inherit",
                  }}
                />
              </div>

              <button
                type="submit"
                className="ws-btn ws-btn--primary ws-btn--full"
                disabled={isPending || !selectedDoctorId || !selectedSlot || !patientName || !patientAge || !patientGender}
              >
                {isPending ? "Booking…" : "Confirm appointment"}
              </button>
            </div>
          </div>
        </form>

        {/* ── Right: Booking summary ── */}
        <div className="ws-card" style={{ height: "fit-content", position: "sticky", top: "1.5rem" }}>
          <div className="ws-card__header">
            <h2 className="ws-card__title">Booking summary</h2>
          </div>
          <div style={{ padding: "0 1.25rem 1.25rem" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <tbody>
                {[
                  ["Doctor", selectedDoctor ? `Dr. ${selectedDoctor.name}` : "—"],
                  ["Specialty", selectedDoctor?.specialty ?? "—"],
                  ["Qualification", selectedDoctor?.qualification ?? "—"],
                  ["Experience", selectedDoctor?.experience_years != null ? `${selectedDoctor.experience_years} years` : "—"],
                  ["Slot", selectedSlot ? formatSlotFull(selectedSlot) : "—"],
                  ["Fee", selectedDoctor?.consultation_fee != null ? `₹${selectedDoctor.consultation_fee}` : "₹500"],
                ].map(([label, value]) => (
                  <tr key={label}>
                    <td style={{ padding: "0.65rem 0", color: "var(--text-soft)", fontSize: "0.84rem", fontWeight: 600, borderBottom: "1px solid var(--line)", width: "40%" }}>{label}</td>
                    <td style={{ padding: "0.65rem 0", fontWeight: 600, fontSize: "0.9rem", borderBottom: "1px solid var(--line)", color: "var(--navy)" }}>{value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </SidebarLayout>
  );
}
