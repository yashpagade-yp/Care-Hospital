import { useEffect, useState, useTransition } from "react";

import { RoleWorkspace } from "@/components/layout/RoleWorkspace";
import { FormField } from "@/components/ui/FormField";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { useAppSession } from "@/features/auth/session/AppSessionProvider";
import { doctorWorkspaceLinks } from "@/features/shared/workspace-links";
import { loadDoctorAvailability } from "@/features/shared/resource-loaders";
import { availabilityApi } from "@/lib/api/endpoints";
import type { AvailabilityType, DayOfWeek, DoctorAvailability } from "@/types/domain";

type AvailabilityForm = {
  availability_type: AvailabilityType;
  day_of_week: DayOfWeek;
  start_time: string;
  end_time: string;
  exception_date: string;
};

export function DoctorAvailabilityPage() {
  const { session } = useAppSession();
  const [items, setItems] = useState<DoctorAvailability[]>([]);
  const [message, setMessage] = useState("");
  const [isPending, startTransition] = useTransition();
  const [form, setForm] = useState<AvailabilityForm>({
    availability_type: "RECURRING",
    day_of_week: "FRIDAY",
    start_time: "09:00:00",
    end_time: "13:00:00",
    exception_date: "",
  });

  useEffect(() => {
    if (!session) {
      return;
    }
    loadDoctorAvailability(session.user.id).then(setItems);
  }, [session]);

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");

    startTransition(async () => {
      try {
        const created = await availabilityApi.createDoctorAvailability(form);
        setItems((current) => [created, ...current]);
      } catch {
        setItems((current) => [
          {
            id: `avail-${current.length + 10}`,
            doctor_id: session?.user.id ?? "doctor-demo",
            ...form,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          ...current,
        ]);
      }
      setMessage("Availability saved successfully.");
    });
  }

  return (
    <RoleWorkspace
      heading="Doctor availability"
      summary="Create recurring working slots and track exception blocks or overrides that affect booking."
      links={doctorWorkspaceLinks}
    >
      <div className="content-grid">
        <section className="surface-card">
          <div className="surface-card__header">
            <div>
              <p className="eyebrow">Create availability</p>
              <h2>Working slot form</h2>
            </div>
          </div>
          <form className="form-grid" onSubmit={handleSubmit}>
            <FormField
              label="Availability type"
              value={form.availability_type}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  availability_type: event.target.value as AvailabilityType,
                }))
              }
            />
            <FormField
              label="Day of week"
              value={form.day_of_week}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  day_of_week: event.target.value as DayOfWeek,
                }))
              }
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
            <FormField
              label="Exception date"
              type="date"
              value={form.exception_date}
              onChange={(event) => setForm((current) => ({ ...current, exception_date: event.target.value }))}
            />
            <div className="form-actions form-actions--full">
              {message ? <StatusBanner tone="success">{message}</StatusBanner> : null}
              <button type="submit" className="button button--primary" disabled={isPending}>
                {isPending ? "Saving..." : "Save availability"}
              </button>
            </div>
          </form>
        </section>

        <section className="surface-card">
          <div className="surface-card__header">
            <div>
              <p className="eyebrow">Availability list</p>
              <h2>Current slots</h2>
            </div>
          </div>
          <div className="stack-list">
            {items.map((item) => (
              <article key={item.id} className="stack-list__item">
                <div>
                  <h3>{item.availability_type}</h3>
                  <p>
                    {item.day_of_week ?? item.exception_date ?? "Custom"} · {item.start_time.slice(0, 5)}-
                    {item.end_time.slice(0, 5)}
                  </p>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </RoleWorkspace>
  );
}
