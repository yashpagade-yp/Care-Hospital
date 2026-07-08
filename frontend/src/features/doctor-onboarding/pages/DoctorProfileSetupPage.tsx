import { useState, useTransition } from "react";
import { useNavigate } from "react-router-dom";

import { FormField } from "@/components/ui/FormField";
import { StatusBanner } from "@/components/ui/StatusBanner";
import {
  clearPendingDoctorFlow,
  getPendingDoctorFlow,
} from "@/features/auth/storage";
import { userApi } from "@/lib/api/endpoints";

export function DoctorProfileSetupPage() {
  const navigate = useNavigate();
  const pendingDoctor = getPendingDoctorFlow();
  const [isPending, startTransition] = useTransition();
  const [name, setName] = useState("");
  const [qualification, setQualification] = useState("");
  const [specialty, setSpecialty] = useState("");
  const [experienceYears, setExperienceYears] = useState("0");
  const [services, setServices] = useState("General consultation, Preventive care");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    setError("");

    startTransition(async () => {
      if (!pendingDoctor.email) {
        setError("Doctor email is missing. Please restart the invitation flow.");
        return;
      }

      const parsedExperienceYears = Number(experienceYears);
      if (!Number.isInteger(parsedExperienceYears) || parsedExperienceYears < 0) {
        setError("Experience must be a valid non-negative number.");
        return;
      }

      try {
        await userApi.completeDoctorProfile({
          name,
          email: pendingDoctor.email,
          qualification,
          specialty,
          experience_years: parsedExperienceYears,
          services: services
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
          working_slots: [],
        });
        clearPendingDoctorFlow();
        setMessage("Doctor onboarding is complete. Sign in to access the doctor workspace.");
        navigate("/login");
      } catch (apiError) {
        setError(
          apiError instanceof Error
            ? apiError.message
            : typeof apiError === "object" && apiError && "message" in apiError
              ? String(apiError.message)
              : "We could not save the doctor profile. Please review the details and try again.",
        );
      }
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
            min="0"
            step="1"
            value={experienceYears}
            onChange={(event) => setExperienceYears(event.target.value)}
            required
          />
          <FormField
            label="Services"
            value={services}
            onChange={(event) => setServices(event.target.value)}
            hint="Enter comma-separated services."
            required
          />

          <div className="form-actions form-actions--full">
            {message ? <StatusBanner tone="success">{message}</StatusBanner> : null}
            {error ? <StatusBanner tone="error">{error}</StatusBanner> : null}
            <button type="submit" className="button button--primary" disabled={isPending}>
              {isPending ? "Saving profile..." : "Complete onboarding"}
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}
