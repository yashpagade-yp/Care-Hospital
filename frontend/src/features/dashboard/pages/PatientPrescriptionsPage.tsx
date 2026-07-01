import { RoleWorkspace } from "@/components/layout/RoleWorkspace";
import { EmptyState } from "@/components/ui/EmptyState";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { useAppSession } from "@/features/auth/session/AppSessionProvider";
import { patientWorkspaceLinks } from "@/features/shared/workspace-links";
import { loadPrescriptionsForPatient } from "@/features/shared/resource-loaders";
import { useAsyncResource } from "@/hooks/useAsyncResource";
import { formatDateTime } from "@/lib/utils/format";

export function PatientPrescriptionsPage() {
  const { session } = useAppSession();
  const { data, isLoading, error } = useAsyncResource(
    () => loadPrescriptionsForPatient(session?.user.id ?? ""),
    [session?.user.id],
  );

  return (
    <RoleWorkspace
      heading="Patient prescriptions"
      summary="Review medicines and post-consultation instructions tied to completed appointments."
      links={patientWorkspaceLinks}
    >
      {error ? <StatusBanner tone="warning">{error}</StatusBanner> : null}
      <section className="surface-card">
        <div className="surface-card__header">
          <div>
            <p className="eyebrow">Prescription history</p>
            <h2>Visible clinical instructions</h2>
          </div>
        </div>
        {isLoading || !data ? (
          <div className="loading-panel">Loading prescriptions...</div>
        ) : data.length ? (
          <div className="stack-list">
            {data.map((prescription) => (
              <article key={prescription.id} className="stack-list__item stack-list__item--block">
                <div>
                  <h3>Appointment {prescription.appointment_id}</h3>
                  <p>Updated {formatDateTime(prescription.updated_at)}</p>
                </div>
                <ul className="chip-row">
                  {prescription.medicines.map((medicine) => (
                    <li key={medicine} className="chip">{medicine}</li>
                  ))}
                </ul>
                <p>{prescription.notes ?? "No additional notes."}</p>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState
            title="No prescriptions yet"
            description="Completed appointments with doctor-issued prescriptions will appear here."
          />
        )}
      </section>
    </RoleWorkspace>
  );
}
