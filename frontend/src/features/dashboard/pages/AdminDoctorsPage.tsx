import { useEffect, useMemo, useState, useTransition } from "react";

import { EmptyState } from "@/components/ui/EmptyState";
import { SidebarLayout } from "@/components/layout/SidebarLayout";
import {
  loadAdminAppointments,
  loadDoctorDirectory,
  loadPatientDirectory,
} from "@/features/shared/resource-loaders";
import { formatDateTime } from "@/lib/utils/format";
import { userApi } from "@/lib/api/endpoints";
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

function formatVisitMeta(appointment: Appointment | null) {
  if (!appointment) {
    return "No appointment details available";
  }

  const parts = [
    appointment.patient_age ? `${appointment.patient_age} yrs` : null,
    appointment.patient_gender ?? null,
    appointment.patient_blood_group ? `Blood ${appointment.patient_blood_group}` : null,
  ].filter(Boolean);

  return parts.length > 0 ? parts.join(" • ") : "Patient information not available";
}

type DeleteDialogProps = {
  doctorName: string;
  onConfirm: () => void;
  onCancel: () => void;
};

type DoctorPatientRow = {
  patient: PatientProfile;
  latestAppointment: Appointment | null;
};

function DeleteDialog({ doctorName, onConfirm, onCancel }: DeleteDialogProps) {
  return (
    <div className="ws-dialog-overlay" role="dialog" aria-modal="true">
      <div className="ws-dialog">
        <h3>Remove this doctor?</h3>
        <p>
          You are about to permanently remove <strong>{doctorName}</strong> from the platform. This
          action cannot be undone. All their appointments and data will be affected.
        </p>
        <div className="ws-dialog__actions">
          <button type="button" className="ws-btn ws-btn--ghost" onClick={onCancel}>
            Cancel
          </button>
          <button type="button" className="ws-btn ws-btn--danger" onClick={onConfirm}>
            Yes, remove doctor
          </button>
        </div>
      </div>
    </div>
  );
}

export function AdminDoctorsPage() {
  const [isPending, startTransition] = useTransition();

  const [doctors, setDoctors] = useState<DoctorProfile[]>([]);
  const [patients, setPatients] = useState<PatientProfile[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);

  const [deleteTarget, setDeleteTarget] = useState<DoctorProfile | null>(null);
  const [selectedDoctorId, setSelectedDoctorId] = useState("");
  const [actionMsg, setActionMsg] = useState("");

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

  const doctorPatients = useMemo(() => {
    if (!selectedDoctorId) {
      return [] as DoctorPatientRow[];
    }

    const latestByPatientId = new Map<string, Appointment>();

    for (const appointment of appointments) {
      if (appointment.doctor_id !== selectedDoctorId || appointment.status === "CANCELLED") {
        continue;
      }

      const existing = latestByPatientId.get(appointment.patient_id);
      if (
        !existing ||
        new Date(appointment.date_time).getTime() > new Date(existing.date_time).getTime()
      ) {
        latestByPatientId.set(appointment.patient_id, appointment);
      }
    }

    return patients
      .filter((patient) => latestByPatientId.has(patient.id))
      .map((patient) => ({
        patient,
        latestAppointment: latestByPatientId.get(patient.id) ?? null,
      }))
      .sort((left, right) => {
        const leftTime = left.latestAppointment ? new Date(left.latestAppointment.date_time).getTime() : 0;
        const rightTime = right.latestAppointment ? new Date(right.latestAppointment.date_time).getTime() : 0;
        return rightTime - leftTime;
      });
  }, [appointments, patients, selectedDoctorId]);

  const selectedDoctor = useMemo(
    () => doctors.find((doctor) => doctor.id === selectedDoctorId) ?? null,
    [doctors, selectedDoctorId],
  );

  async function handleSuspend(doctor: DoctorProfile) {
    setActionMsg("");
    try {
      await userApi.suspendDoctor(doctor.id);
      setDoctors((prev) =>
        prev.map((item) =>
          item.id === doctor.id ? { ...item, doctor_status: "SUSPENDED" } : item,
        ),
      );
      setActionMsg(`${doctor.name} has been suspended.`);
    } catch {
      setActionMsg("Could not suspend this doctor. Please try again.");
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    try {
      await userApi.deleteDoctor(deleteTarget.id);
      setDoctors((prev) => prev.filter((doctor) => doctor.id !== deleteTarget.id));
      if (selectedDoctorId === deleteTarget.id) {
        setSelectedDoctorId("");
      }
      setActionMsg(`${deleteTarget.name} has been removed from the platform.`);
    } catch {
      setActionMsg("Could not remove this doctor. Please try again.");
    } finally {
      setDeleteTarget(null);
    }
  }

  return (
    <SidebarLayout sections={ADMIN_NAV}>
      {deleteTarget ? (
        <DeleteDialog
          doctorName={deleteTarget.name}
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      ) : null}

      <div className="ws-page-header">
        <p className="ws-page-eyebrow">Admin Workspace</p>
        <h1 className="ws-page-heading">Doctors</h1>
        <p className="ws-page-sub">
          Manage doctors, then open each doctor's patient list to see who they have treated.
        </p>
      </div>

      {actionMsg ? (
        <div
          style={{
            padding: "0.75rem 1rem",
            borderRadius: "var(--radius-sm)",
            background: "var(--green-soft)",
            border: "1px solid rgba(13,158,110,0.2)",
            color: "var(--status-active-text)",
            fontSize: "0.87rem",
            marginBottom: "1.25rem",
          }}
        >
          {actionMsg}
        </div>
      ) : null}

      <div className="ws-card" style={{ marginBottom: "2rem" }}>
        <div className="ws-card__header">
          <div>
            <p className="ws-page-eyebrow" style={{ marginBottom: "0.35rem" }}>Doctor Section</p>
            <h2 className="ws-card__title">Registered doctors</h2>
            <p className="ws-card__sub">
              {doctors.length} doctor{doctors.length !== 1 ? "s" : ""} available on the platform
            </p>
          </div>
        </div>

        {isPending ? (
          <div className="ws-loading">Loading doctors…</div>
        ) : doctors.length === 0 ? (
          <div className="ws-card__body">
            <EmptyState
              title="No doctors yet"
              description="Invite a doctor from the admin workspace to get started."
            />
          </div>
        ) : (
          <div className="ws-table-wrap">
            <table className="ws-table">
              <thead>
                <tr>
                  <th>Doctor</th>
                  <th>Specialty</th>
                  <th>Experience</th>
                  <th>Status</th>
                  <th>Joined</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {doctors.map((doctor) => (
                  <tr key={doctor.id}>
                    <td>
                      <div className="ws-user-cell">
                        <div className="ws-user-avatar">{getInitials(doctor.name)}</div>
                        <div>
                          <span className="ws-user-name">{doctor.name}</span>
                          <span className="ws-user-email">{doctor.email}</span>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span style={{ fontWeight: 600 }}>
                        {doctor.specialty ?? <span style={{ color: "var(--text-soft)" }}>—</span>}
                      </span>
                      {doctor.qualification ? (
                        <span
                          style={{
                            display: "block",
                            fontSize: "0.78rem",
                            color: "var(--text-soft)",
                          }}
                        >
                          {doctor.qualification}
                        </span>
                      ) : null}
                    </td>
                    <td>
                      {doctor.experience_years != null ? (
                        <span>{doctor.experience_years} yr{doctor.experience_years !== 1 ? "s" : ""}</span>
                      ) : (
                        <span style={{ color: "var(--text-soft)" }}>—</span>
                      )}
                    </td>
                    <td>
                      <span
                        className={`ws-badge ws-badge--${(doctor.doctor_status ?? "registered").toLowerCase()}`}
                      >
                        {doctor.doctor_status ?? "REGISTERED"}
                      </span>
                    </td>
                    <td style={{ color: "var(--text-soft)", fontSize: "0.85rem" }}>
                      {formatDate(doctor.created_at)}
                    </td>
                    <td>
                      <div className="ws-action-row">
                        <button
                          type="button"
                          className="ws-btn ws-btn--ghost"
                          onClick={() =>
                            setSelectedDoctorId((current) => (current === doctor.id ? "" : doctor.id))
                          }
                        >
                          {selectedDoctorId === doctor.id ? "Hide patients" : "View Patients"}
                        </button>
                        {doctor.doctor_status !== "SUSPENDED" ? (
                          <button
                            type="button"
                            className="ws-btn ws-btn--amber"
                            onClick={() => handleSuspend(doctor)}
                            title="Suspend this doctor"
                          >
                            Suspend
                          </button>
                        ) : (
                          <span className="ws-badge ws-badge--suspended" style={{ fontSize: "0.78rem" }}>
                            Suspended
                          </span>
                        )}
                        <button
                          type="button"
                          className="ws-btn ws-btn--danger"
                          onClick={() => setDeleteTarget(doctor)}
                          title="Permanently remove this doctor"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedDoctor ? (
        <div className="ws-card" style={{ marginBottom: "2rem" }}>
          <div className="ws-card__header">
            <div>
              <h2 className="ws-card__title">Patients for {selectedDoctor.name}</h2>
              <p className="ws-card__sub">
                Patients who visited or were treated by this doctor.
              </p>
            </div>
          </div>

          {doctorPatients.length === 0 ? (
            <div className="ws-card__body">
              <EmptyState
                title="No linked patients yet"
                description="Patients will appear here once they have appointments with this doctor."
              />
            </div>
          ) : (
            <div className="ws-table-wrap">
              <table className="ws-table">
                <thead>
                  <tr>
                    <th>Patient</th>
                    <th>Phone</th>
                    <th>Patient info</th>
                    <th>Last visit</th>
                    <th>Reason</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {doctorPatients.map(({ patient, latestAppointment }) => (
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
                      <td style={{ color: "var(--text-soft)", fontSize: "0.87rem" }}>
                        {latestAppointment?.patient_phone ?? patient.phone ?? "—"}
                      </td>
                      <td style={{ color: "var(--text-soft)", fontSize: "0.83rem" }}>
                        <div>{formatVisitMeta(latestAppointment)}</div>
                        <div>DOB: {formatDate(patient.dob)}</div>
                      </td>
                      <td style={{ color: "var(--text-soft)", fontSize: "0.83rem" }}>
                        {latestAppointment ? formatDateTime(latestAppointment.date_time) : "—"}
                      </td>
                      <td style={{ color: "var(--text-soft)", fontSize: "0.83rem" }}>
                        {latestAppointment?.reason ?? "Not provided"}
                      </td>
                      <td>
                        {latestAppointment ? (
                          <span className={`ws-badge ws-badge--${latestAppointment.status.toLowerCase()}`}>
                            {latestAppointment.status}
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : null}

    </SidebarLayout>
  );
}
