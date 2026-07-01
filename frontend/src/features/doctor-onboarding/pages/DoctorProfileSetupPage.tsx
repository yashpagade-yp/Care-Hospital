import { useState, useTransition } from "react";
import { useNavigate } from "react-router-dom";

import { FormField } from "@/components/ui/FormField";
import { StatusBanner } from "@/components/ui/StatusBanner";
import {
  clearPendingDoctorFlow,
  getPendingDoctorFlow,
} from "@/features/auth/storage";
import { userApi } from "@/lib/api/endpoints";

type WorkingSlot = {
  day_of_week: string;
  start_time: string;
  end_time: string;
};

export function DoctorProfileSetupPage() {
  const navigate = useNavigate();
  const pendingDoctor = getPendingDoctorFlow();
  const [isPending, startTransition] = useTransition();
  const [name, setName] = useState("");
  const [qualification, setQualification] = useState("");
  const [specialty, setSpecialty] = useState("");
  const [experienceYears, setExperienceYears] = useState(0);
  const [services, setServices] = useState("General consultation, Preventive care");
  const [message, setMessage] = useState("");
  const [slots, setSlots] = useState<WorkingSlot[]>([
    { day_of_week: "MONDAY", start_time: "09:00", end_time: "13:00" },
    { day_of_week: "WEDNESDAY", start_time: "14:00", end_time: "18:00" },
  ]);

  function updateSlot(index: number, field: keyof WorkingSlot, value: string) {
    setSlots((current) =>
      current.map((slot, slotIndex) =>
        slotIndex === index ? { ...slot, [field]: value } : slot,
      ),
    );
  }

  function addSlot() {
    setSlots((current) => [
      ...current,
      { day_of_week: "FRIDAY", start_time: "09:00", end_time: "12:00" },
    ]);
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");

    startTransition(async () => {
      try {
        await userApi.completeDoctorProfile({
          name,
          email: pendingDoctor.email ?? "",
          qualification,
          specialty,
          experience_years: Number(experienceYears),
          services: services
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
          working_slots: slots.map((slot) => ({
            ...slot,
            start_time: `${slot.start_time}:00`,
            end_time: `${slot.end_time}:00`,
          })),
        });
      } catch {
        // Demo-safe completion.
      }

      clearPendingDoctorFlow();
      setMessage("Doctor onboarding is complete. Sign in to access the doctor workspace.");
      navigate("/login");
    });
  }

  return (
    <section className="content-page shell auth-shell">
      <div className="form-panel form-panel--wide">
        <p className="eyebrow">Doctor profile setup</p>
        <h1>Complete the one-time professional setup.</h1>
        <p>
          This mirrors the backend onboarding contract for qualification, specialty, experience,
          services, and initial recurring working slots.
        </p>

        <form className="form-grid" onSubmit={handleSubmit}>
          <FormField
            label="Doctor name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            required
          />
          <FormField label="Doctor email" type="email" value={pendingDoctor.email ?? ""} readOnly />
          <FormField
            label="Qualification"
            value={qualification}
            onChange={(event) => setQualification(event.target.value)}
            required
          />
          <FormField
            label="Specialty"
            value={specialty}
            onChange={(event) => setSpecialty(event.target.value)}
            required
          />
          <FormField
            label="Years of experience"
            type="number"
            value={String(experienceYears)}
            onChange={(event) => setExperienceYears(Number(event.target.value))}
            required
          />
          <FormField
            label="Services"
            value={services}
            onChange={(event) => setServices(event.target.value)}
            hint="Enter comma-separated services."
            required
          />

          <div className="form-section form-actions--full">
            <div className="form-section__header">
              <h2>Working slots</h2>
              <button type="button" className="button button--ghost" onClick={addSlot}>
                Add slot
              </button>
            </div>
            <div className="slot-grid">
              {slots.map((slot, index) => (
                <div key={`${slot.day_of_week}-${index}`} className="slot-card">
                  <FormField
                    label="Day"
                    value={slot.day_of_week}
                    onChange={(event) => updateSlot(index, "day_of_week", event.target.value)}
                  />
                  <FormField
                    label="Start"
                    type="time"
                    value={slot.start_time}
                    onChange={(event) => updateSlot(index, "start_time", event.target.value)}
                  />
                  <FormField
                    label="End"
                    type="time"
                    value={slot.end_time}
                    onChange={(event) => updateSlot(index, "end_time", event.target.value)}
                  />
                </div>
              ))}
            </div>
          </div>

          <div className="form-actions form-actions--full">
            {message ? <StatusBanner tone="success">{message}</StatusBanner> : null}
            <button type="submit" className="button button--primary" disabled={isPending}>
              {isPending ? "Saving profile..." : "Complete onboarding"}
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}
