import { RoleWorkspace } from "@/components/layout/RoleWorkspace";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { adminWorkspaceLinks } from "@/features/shared/workspace-links";
import {
  loadDoctorDirectory,
  loadPatientDirectory,
} from "@/features/shared/resource-loaders";
import { useAsyncResource } from "@/hooks/useAsyncResource";

export function AdminDoctorsPage() {
  const doctors = useAsyncResource(loadDoctorDirectory, []);
  const patients = useAsyncResource(loadPatientDirectory, []);

  return (
    <RoleWorkspace
      heading="Doctor and patient directory"
      summary="Review onboarding status, contact details, specialties, and the current platform directory."
      links={adminWorkspaceLinks}
    >
      {doctors.error ? <StatusBanner tone="warning">{doctors.error}</StatusBanner> : null}
      <div className="content-grid">
        <section className="surface-card">
          <div className="surface-card__header">
            <div>
              <p className="eyebrow">Doctor directory</p>
              <h2>Registered doctors</h2>
            </div>
          </div>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Specialty</th>
                  <th>Experience</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {(doctors.data ?? []).map((doctor) => (
                  <tr key={doctor.id}>
                    <td>{doctor.name}</td>
                    <td>{doctor.specialty ?? "N/A"}</td>
                    <td>{doctor.experience_years ?? 0} years</td>
                    <td><span className={`pill pill--${(doctor.doctor_status ?? "registered").toLowerCase()}`}>{doctor.doctor_status ?? "REGISTERED"}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="surface-card">
          <div className="surface-card__header">
            <div>
              <p className="eyebrow">Patient directory</p>
              <h2>Patient profiles</h2>
            </div>
          </div>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Phone</th>
                </tr>
              </thead>
              <tbody>
                {(patients.data ?? []).map((patient) => (
                  <tr key={patient.id}>
                    <td>{patient.name}</td>
                    <td>{patient.email}</td>
                    <td>{patient.phone ?? "N/A"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </RoleWorkspace>
  );
}
