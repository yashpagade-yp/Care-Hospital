import { SidebarLayout } from "@/components/layout/SidebarLayout";
import { PrescriptionSheet } from "@/components/ui/PrescriptionSheet";
import { PATIENT_NAV } from "./PatientDashboardPage";
import { EmptyState } from "@/components/ui/EmptyState";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { useAppSession } from "@/features/auth/session/AppSessionProvider";
import { loadPrescriptionsForPatient } from "@/features/shared/resource-loaders";
import { useAsyncResource } from "@/hooks/useAsyncResource";
import { formatDateTime } from "@/lib/utils/format";

const HOSPITAL_NAME = "MedCare Hospital";
const HOSPITAL_ADDRESS = "24 Green Avenue, Lakeview Road, Bengaluru 560048";

export function PatientPrescriptionsPage() {
  const { session } = useAppSession();
  const { data, isLoading, error } = useAsyncResource(
    () => loadPrescriptionsForPatient(session?.user.id ?? ""),
    [session?.user.id],
  );

  return (
    <SidebarLayout sections={PATIENT_NAV}>
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
              <PrescriptionSheet
                key={prescription.id}
                hospitalName={HOSPITAL_NAME}
                hospitalAddress={HOSPITAL_ADDRESS}
                doctorName={prescription.doctor_name ?? "Doctor"}
                patientName={prescription.patient_name ?? session?.user.name ?? "Patient"}
                patientPhone={prescription.patient_phone}
                patientAge={prescription.patient_age}
                patientGender={prescription.patient_gender}
                patientBloodGroup={prescription.patient_blood_group}
                visitReason={prescription.visit_reason}
                medicines={prescription.medicines}
                notes={prescription.notes}
                issuedAt={formatDateTime(prescription.updated_at)}
              />
            ))}
          </div>
        ) : (
          <EmptyState
            title="No prescriptions yet"
            description="Completed appointments with doctor-issued prescriptions will appear here."
          />
        )}
      </section>
    </SidebarLayout>
  );
}
