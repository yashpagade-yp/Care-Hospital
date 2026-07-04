import { useEffect, useMemo, useState, useTransition } from "react";

import { SidebarLayout } from "@/components/layout/SidebarLayout";
import { EmptyState } from "@/components/ui/EmptyState";
import {
  loadAdminAppointments,
  loadDoctorDirectory,
  loadPatientDirectory,
} from "@/features/shared/resource-loaders";
import { formatDateTime } from "@/lib/utils/format";
import type { Appointment, DoctorProfile, PatientProfile } from "@/types/domain";

import { ADMIN_NAV } from "./AdminDashboardPage";

function getInitials(name: string) {
  return name
    .split(" ")
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

function formatDate(dateStr?: string | null) {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function formatPatientMeta(appointment: Appointment | null, patient: PatientProfile) {
  const parts = [
    appointment?.patient_age ? `${appointment.patient_age} yrs` : null,
    appointment?.patient_gender ?? null,
    appointment?.patient_blood_group ? `Blood ${appointment.patient_blood_group}` : null,
    patient.dob ? `DOB ${formatDate(patient.dob)}` : null,
  ].filter(Boolean);

  return parts.length > 0 ? parts.join(" • ") : "Patient information not available";
}

type PatientDirectoryRow = {
  patient: PatientProfile;
  doctorNames: string[];
  latestAppointment: Appointment | null;
};

export function AdminPatientsPage() {
  const [isPending, startTransition] = useTransition();
  const [doctors, setDoctors] = useState<DoctorProfile[]>([]);
  const [patients, setPatients] = useState<PatientProfile[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);

  useEffect(() => {
    startTransition(async () => {
      try {
        const [doctorItems, patientItems, appointmentItems] = await Promise.all([
          loadDoctorDirectory(),
          loadPatientDirectory(),
          loadAdminAppointments(),
        ]);
        setDoctors(doctorItems);
        setPatients(patientItems);
        setAppointments(appointmentItems);
      } catch {
        // Demo mode or unavailable backend — fallback loaders already handle local data.
      }
    });
  }, []);

  const appointmentDoctorMap = useMemo(
    () => new Map(doctors.map((doctor) => [doctor.id, doctor])),
    [doctors],
  );

  const patientRows = useMemo(() => {
    const relationMap = new Map<string, Set<string>>();
    const latestByPatientId = new Map<string, Appointment>();

    for (const appointment of appointments) {
      if (appointment.status === "CANCELLED") {
        continue;
      }

      const doctorName =
        appointment.doctor_name ?? appointmentDoctorMap.get(appointment.doctor_id)?.name ?? "Doctor";
      const relatedDoctors = relationMap.get(appointment.patient_id) ?? new Set<string>();
      relatedDoctors.add(doctorName);
      relationMap.set(appointment.patient_id, relatedDoctors);

      const existing = latestByPatientId.get(appointment.patient_id);
      if (
        !existing ||
        new Date(appointment.date_time).getTime() > new Date(existing.date_time).getTime()
      ) {
        latestByPatientId.set(appointment.patient_id, appointment);
      }
    }

    return patients
      .map((patient) => ({
        patient,
        doctorNames: [...(relationMap.get(patient.id) ?? new Set<string>())],
        latestAppointment: latestByPatientId.get(patient.id) ?? null,
      }))
      .sort((left, right) => {
        const leftTime = left.latestAppointment ? new Date(left.latestAppointment.date_time).getTime() : 0;
        const rightTime = right.latestAppointment ? new Date(right.latestAppointment.date_time).getTime() : 0;
        return rightTime - leftTime;
      });
  }, [appointments, appointmentDoctorMap, patients]);

  return (
    <SidebarLayout sections={ADMIN_NAV}>
      <div className="ws-page-header">
        <p className="ws-page-eyebrow">Admin Workspace</p>
        <h1 className="ws-page-heading">Patients</h1>
        <p className="ws-page-sub">
          Review all registered patients, their treatment details, and the doctors caring for them.
        </p>
      </div>

      <div className="ws-card">
        <div className="ws-card__header">
          <div>
            <p className="ws-page-eyebrow" style={{ marginBottom: "0.35rem" }}>Patient Section</p>
            <h2 className="ws-card__title">Registered patients</h2>
            <p className="ws-card__sub">
              {patients.length} patient{patients.length !== 1 ? "s" : ""} registered on the platform
            </p>
          </div>
        </div>

        {isPending ? (
          <div className="ws-loading">Loading patients…</div>
        ) : patientRows.length === 0 ? (
          <div className="ws-card__body">
            <EmptyState
              title="No patients yet"
              description="Patients will appear here once they register on the platform."
            />
          </div>
        ) : (
          <div className="ws-table-wrap">
            <table className="ws-table">
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Treating doctor(s)</th>
                  <th>Patient info</th>
                  <th>Phone</th>
                  <th>Last visit</th>
                  <th>Registered on</th>
                </tr>
              </thead>
              <tbody>
                {patientRows.map(({ patient, doctorNames, latestAppointment }) => (
                  <tr key={patient.id}>
                    <td>
                      <div className="ws-user-cell">
                        <div
                          className="ws-user-avatar"
                          style={{
                            background:
                              "linear-gradient(135deg, var(--green) 0%, #0d7a55 100%)",
                          }}
                        >
                          {getInitials(patient.name)}
                        </div>
                        <div>
                          <span className="ws-user-name">{patient.name}</span>
                          <span className="ws-user-email">{patient.email}</span>
                        </div>
                      </div>
                    </td>
                    <td style={{ color: "var(--text-soft)", fontSize: "0.85rem" }}>
                      {doctorNames.length > 0 ? doctorNames.join(", ") : "Not assigned yet"}
                    </td>
                    <td style={{ color: "var(--text-soft)", fontSize: "0.83rem" }}>
                      <div>{formatPatientMeta(latestAppointment, patient)}</div>
                      <div>
                        Reason: {latestAppointment?.reason ?? "Not provided"}
                      </div>
                    </td>
                    <td style={{ color: "var(--text-soft)", fontSize: "0.87rem" }}>
                      {latestAppointment?.patient_phone ?? patient.phone ?? "—"}
                    </td>
                    <td style={{ color: "var(--text-soft)", fontSize: "0.83rem" }}>
                      {latestAppointment ? formatDateTime(latestAppointment.date_time) : "—"}
                    </td>
                    <td style={{ color: "var(--text-soft)", fontSize: "0.85rem" }}>
                      {formatDate(patient.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </SidebarLayout>
  );
}
