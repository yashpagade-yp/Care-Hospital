import { useEffect, useTransition, useState } from "react";
import { SidebarLayout } from "@/components/layout/SidebarLayout";
import { userApi } from "@/lib/api/endpoints";
import type { DoctorProfile, PatientProfile } from "@/types/domain";
import { ADMIN_NAV } from "./AdminDashboardPage";

function getInitials(name: string) {
  return name
    .split(" ")
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? "")
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

type DeleteDialogProps = {
  doctorName: string;
  onConfirm: () => void;
  onCancel: () => void;
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

  const [deleteTarget, setDeleteTarget] = useState<DoctorProfile | null>(null);
  const [actionMsg, setActionMsg] = useState("");

  useEffect(() => {
    startTransition(async () => {
      try {
        const [docRes, patRes] = await Promise.all([
          userApi.listDoctors(),
          userApi.listPatients(),
        ]);
        setDoctors(docRes.items);
        setPatients(patRes.items);
      } catch {
        // Demo mode — tables remain empty
      }
    });
  }, []);

  async function handleSuspend(doctor: DoctorProfile) {
    setActionMsg("");
    try {
      await userApi.suspendDoctor(doctor.id);
      setDoctors((prev) =>
        prev.map((d) =>
          d.id === doctor.id ? { ...d, doctor_status: "SUSPENDED" } : d,
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
      setDoctors((prev) => prev.filter((d) => d.id !== deleteTarget.id));
      setActionMsg(`${deleteTarget.name} has been removed from the platform.`);
    } catch {
      setActionMsg("Could not remove this doctor. Please try again.");
    } finally {
      setDeleteTarget(null);
    }
  }

  return (
    <SidebarLayout sections={ADMIN_NAV}>
      {deleteTarget && (
        <DeleteDialog
          doctorName={deleteTarget.name}
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}

      {/* ── Page header ── */}
      <div className="ws-page-header">
        <p className="ws-page-eyebrow">Admin Workspace</p>
        <h1 className="ws-page-heading">Doctors & Patients</h1>
        <p className="ws-page-sub">
          Manage all registered doctors and view the patient directory.
        </p>
      </div>

      {actionMsg && (
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
      )}

      {/* ════════════════ DOCTORS TABLE ════════════════ */}
      <div className="ws-card" style={{ marginBottom: "2rem" }}>
        <div className="ws-card__header">
          <div>
            <h2 className="ws-card__title">Manage doctors</h2>
            <p className="ws-card__sub">
              {doctors.length} doctor{doctors.length !== 1 ? "s" : ""} registered on the platform
            </p>
          </div>
        </div>

        {isPending ? (
          <div className="ws-loading">Loading doctors…</div>
        ) : doctors.length === 0 ? (
          <div className="ws-empty">
            <div className="ws-empty__icon">🩺</div>
            <p className="ws-empty__title">No doctors yet</p>
            <p className="ws-empty__sub">
              Invite a doctor from the dashboard to get started.
            </p>
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
                {doctors.map((doc) => (
                  <tr key={doc.id}>
                    {/* Name + email cell */}
                    <td>
                      <div className="ws-user-cell">
                        <div className="ws-user-avatar">{getInitials(doc.name)}</div>
                        <div>
                          <span className="ws-user-name">{doc.name}</span>
                          <span className="ws-user-email">{doc.email}</span>
                        </div>
                      </div>
                    </td>

                    {/* Specialty */}
                    <td>
                      <span style={{ fontWeight: 600 }}>
                        {doc.specialty ?? <span style={{ color: "var(--text-soft)" }}>—</span>}
                      </span>
                      {doc.qualification && (
                        <span
                          style={{
                            display: "block",
                            fontSize: "0.78rem",
                            color: "var(--text-soft)",
                          }}
                        >
                          {doc.qualification}
                        </span>
                      )}
                    </td>

                    {/* Experience */}
                    <td>
                      {doc.experience_years != null ? (
                        <span>{doc.experience_years} yr{doc.experience_years !== 1 ? "s" : ""}</span>
                      ) : (
                        <span style={{ color: "var(--text-soft)" }}>—</span>
                      )}
                    </td>

                    {/* Status badge */}
                    <td>
                      <span
                        className={`ws-badge ws-badge--${
                          (doc.doctor_status ?? "registered").toLowerCase()
                        }`}
                      >
                        {doc.doctor_status ?? "REGISTERED"}
                      </span>
                    </td>

                    {/* Joined date */}
                    <td style={{ color: "var(--text-soft)", fontSize: "0.85rem" }}>
                      {formatDate(doc.created_at)}
                    </td>

                    {/* Action buttons */}
                    <td>
                      <div className="ws-action-row">
                        {doc.doctor_status !== "SUSPENDED" && (
                          <button
                            type="button"
                            className="ws-btn ws-btn--amber"
                            onClick={() => handleSuspend(doc)}
                            title="Suspend this doctor"
                          >
                            Suspend
                          </button>
                        )}
                        {doc.doctor_status === "SUSPENDED" && (
                          <span
                            className="ws-badge ws-badge--suspended"
                            style={{ fontSize: "0.78rem" }}
                          >
                            Suspended
                          </span>
                        )}
                        <button
                          type="button"
                          className="ws-btn ws-btn--danger"
                          onClick={() => setDeleteTarget(doc)}
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

      {/* ════════════════ PATIENTS TABLE ════════════════ */}
      <div className="ws-card">
        <div className="ws-card__header">
          <div>
            <h2 className="ws-card__title">Patient directory</h2>
            <p className="ws-card__sub">
              {patients.length} patient{patients.length !== 1 ? "s" : ""} registered on the platform
            </p>
          </div>
        </div>

        {isPending ? (
          <div className="ws-loading">Loading patients…</div>
        ) : patients.length === 0 ? (
          <div className="ws-empty">
            <div className="ws-empty__icon">🧑‍⚕️</div>
            <p className="ws-empty__title">No patients yet</p>
            <p className="ws-empty__sub">
              Patients will appear here once they register on the platform.
            </p>
          </div>
        ) : (
          <div className="ws-table-wrap">
            <table className="ws-table">
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Phone</th>
                  <th>Date of birth</th>
                  <th>Registered on</th>
                </tr>
              </thead>
              <tbody>
                {patients.map((patient) => (
                  <tr key={patient.id}>
                    {/* Name + email */}
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

                    {/* Phone */}
                    <td style={{ color: "var(--text-soft)", fontSize: "0.87rem" }}>
                      {patient.phone ?? "—"}
                    </td>

                    {/* Date of birth */}
                    <td style={{ color: "var(--text-soft)", fontSize: "0.87rem" }}>
                      {patient.dob
                        ? new Date(patient.dob).toLocaleDateString("en-IN", {
                            day: "numeric",
                            month: "short",
                            year: "numeric",
                          })
                        : "—"}
                    </td>

                    {/* Registered date */}
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
