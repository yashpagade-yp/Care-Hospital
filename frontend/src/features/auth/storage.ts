const PENDING_PATIENT_EMAIL_KEY = "medcare-pending-patient-email";
const PENDING_DOCTOR_FLOW_KEY = "medcare-pending-doctor-flow";

export function setPendingPatientEmail(email: string) {
  localStorage.setItem(PENDING_PATIENT_EMAIL_KEY, email);
}

export function getPendingPatientEmail() {
  return localStorage.getItem(PENDING_PATIENT_EMAIL_KEY) ?? "";
}

export function clearPendingPatientEmail() {
  localStorage.removeItem(PENDING_PATIENT_EMAIL_KEY);
}

export type PendingDoctorFlow = {
  token?: string;
  email?: string;
};

export function setPendingDoctorFlow(payload: PendingDoctorFlow) {
  localStorage.setItem(PENDING_DOCTOR_FLOW_KEY, JSON.stringify(payload));
}

export function getPendingDoctorFlow(): PendingDoctorFlow {
  const raw = localStorage.getItem(PENDING_DOCTOR_FLOW_KEY);
  if (!raw) {
    return {};
  }

  try {
    return JSON.parse(raw) as PendingDoctorFlow;
  } catch {
    return {};
  }
}

export function clearPendingDoctorFlow() {
  localStorage.removeItem(PENDING_DOCTOR_FLOW_KEY);
}
