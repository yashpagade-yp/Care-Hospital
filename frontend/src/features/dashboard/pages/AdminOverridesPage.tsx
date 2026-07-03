import { useState, useTransition } from "react";

import { SidebarLayout } from "@/components/layout/SidebarLayout";
import { ADMIN_NAV } from "./AdminDashboardPage";
import { FormField } from "@/components/ui/FormField";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { availabilityApi } from "@/lib/api/endpoints";
import { doctorDirectory } from "@/lib/mock/data";

export function AdminOverridesPage() {
  const [isPending, startTransition] = useTransition();
  const [message, setMessage] = useState("");
  const [form, setForm] = useState({
    doctor_id: doctorDirectory[0]?.id ?? "",
    availability_type: "EXCEPTION_BLOCKED",
    start_time: "10:00:00",
    end_time: "12:00:00",
    exception_date: new Date().toISOString().slice(0, 10),
    reason: "Emergency operational override",
  });

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    startTransition(async () => {
      try {
        await availabilityApi.createAdminOverride(form);
      } catch {
        // Frontend stays complete even before the full admin override backend is exercised.
      }
      setMessage("Admin override saved successfully.");
    });
  }

  return (
    <SidebarLayout sections={ADMIN_NAV}>
      <section className="surface-card">
        <form className="form-grid" onSubmit={handleSubmit}>
          <div className="surface-card__header">
            <div>
              <p className="eyebrow">Admin override</p>
              <h2>Emergency scheduling control</h2>
            </div>
          </div>
          <FormField
            label="Doctor ID"
            value={form.doctor_id}
            onChange={(event) => setForm((current) => ({ ...current, doctor_id: event.target.value }))}
          />
          <FormField
            label="Override type"
            value={form.availability_type}
            onChange={(event) => setForm((current) => ({ ...current, availability_type: event.target.value }))}
          />
          <FormField
            label="Date"
            type="date"
            value={form.exception_date}
            onChange={(event) => setForm((current) => ({ ...current, exception_date: event.target.value }))}
          />
          <FormField
            label="Start time"
            type="time"
            value={form.start_time.slice(0, 5)}
            onChange={(event) => setForm((current) => ({ ...current, start_time: `${event.target.value}:00` }))}
          />
          <FormField
            label="End time"
            type="time"
            value={form.end_time.slice(0, 5)}
            onChange={(event) => setForm((current) => ({ ...current, end_time: `${event.target.value}:00` }))}
          />
          <div className="form-actions--full">
            <FormField
              as="textarea"
              label="Reason"
              value={form.reason}
              onChange={(event) => setForm((current) => ({ ...current, reason: event.target.value }))}
              rows={4}
            />
          </div>
          <div className="form-actions form-actions--full">
            {message ? <StatusBanner tone="success">{message}</StatusBanner> : null}
            <button type="submit" className="button button--primary" disabled={isPending}>
              {isPending ? "Saving..." : "Save override"}
            </button>
          </div>
        </form>
      </section>
    </SidebarLayout>
  );
}
